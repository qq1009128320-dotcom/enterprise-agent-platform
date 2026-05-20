#!/usr/bin/env python3
"""
Hermes 桥接服务 — 接收自然语言问题，调用 DeepSeek + 记忆引擎，返回结果
供 Streamlit 演示面板调用
"""

import sys
import json
import sqlite3
import requests
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DB_PATH = "/home/administrator/finance_data/db/finance.db"

# ── 读取 Schema ──
def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cols = conn.execute("PRAGMA table_info(journal)").fetchall()
    schema = "CREATE TABLE journal (" + ", ".join(f"{c[1]} {c[2]}" for c in cols) + ");\n\n"

    rows = conn.execute("""
        SELECT account_code, account_name, COUNT(*) as cnt,
               ROUND(SUM(debit),0) as td, ROUND(SUM(credit),0) as tc
        FROM journal GROUP BY account_code ORDER BY cnt DESC LIMIT 40
    """).fetchall()
    schema += "主要科目:\n"
    for r in rows:
        schema += f"  {r[0]} | {r[1]} | {r[2]}条 | 借{r[3]} 贷{r[4]}\n"

    depts = conn.execute("SELECT DISTINCT department FROM journal WHERE department IS NOT NULL AND department != ''").fetchall()
    schema += f"\n部门: {', '.join(d[0] for d in depts)}\n"

    years = conn.execute("SELECT DISTINCT year, MAX(period) FROM journal GROUP BY year ORDER BY year").fetchall()
    for y in years:
        schema += f"  {y[0]}年: 1-{y[1]}月\n"

    cnt = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]
    schema += f"\n总记录: {cnt:,} 条\n"

    # 查询记忆引擎状态
    schema += "\n记忆引擎已知规则（偏好记忆）:\n"
    schema += "  会计周期: 每月25日至下月25日\n"
    schema += "  研发支出: 全部费用化，不资本化\n"
    schema += "  收入算法: max(借方, 贷方) = 实际发生额\n"
    schema += "  预付账款贷方余额: 重分类至应付账款\n"
    schema += "  业务模式: 化妆品纯贸易/经销，无生产成本\n"

    conn.close()
    return schema

SCHEMA = get_schema()

SYSTEM_PROMPT = f"""你是企业财务数据分析助手 Hermes Agent。你可以访问企业的 journal 表：

{SCHEMA}

根据用户的中文问题，生成一条 SQLite SQL 查询。

规则：
- 费用(花了多少钱/支出/开销): account_code LIKE '6601%' OR '6602%' OR '6603%', 取 SUM(debit)
- 收入: account_code LIKE '6001%', 取 MAX(debit, credit)
- 成本: account_code LIKE '6401%', 取 MAX(debit, credit)  
- 银行存款/资金/现金: account_code LIKE '100%'
- 利润估算 ≈ 收入 - 成本 - 费用
- 资产负债: 资产(1开头)=借-贷, 负债(2开头)=贷-借
- "上个月"=当前最大月份-1, "这个月"=最大月份, "今年"=最大年份
- 所有金额用 ROUND(..., 2)
- 按部门分组时排除 NULL 和空字符串
- 只生成 SELECT 语句，只查询不修改

返回 JSON（不要 markdown 包裹）:
{{"sql": "SQL查询", "explanation": "简短说明", "type": "metric|table|bar|line|pie"}}"""


def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql).fetchall()]
    conn.close()
    return rows


def process(question: str, history: list = None) -> dict:
    """处理一个问题，返回结果"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for h in history[-6:]:
            messages.append({"role": "user" if h["role"]=="user" else "assistant",
                           "content": h.get("content","")[:300]})

    messages.append({"role": "user", "content": question})

    # 1. 调用 LLM
    try:
        resp = requests.post(DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": messages, "temperature": 0.1, "max_tokens": 600},
            timeout=30)
        if resp.status_code != 200:
            return {"error": f"API {resp.status_code}", "detail": resp.text[:300]}

        text = resp.json()["choices"][0]["message"]["content"].strip()
        # 清理 markdown 包裹
        import re
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text).strip()
        result = json.loads(text)
    except Exception as e:
        return {"error": "LLM调用失败", "detail": str(e)}

    sql = result.get("sql", "")
    explanation = result.get("explanation", "")
    chart_type = result.get("type", "table")

    # 2. 执行 SQL
    try:
        rows = run_query(sql)
    except Exception as e:
        return {"error": "SQL执行失败", "detail": str(e), "sql": sql, "explanation": explanation}

    # 3. 如果结果很多，用 LLM 生成摘要
    summary = ""
    if len(rows) > 5 and len(rows) <= 50:
        try:
            data_preview = json.dumps(rows[:10], ensure_ascii=False, indent=2)
            sum_resp = requests.post(DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是数据分析助手。根据查询结果，用1-3句中文给出关键发现。简洁直接。"},
                        {"role": "user", "content": f"问题: {question}\n\n查询结果(共{len(rows)}条，展示前10条):\n{data_preview}\n\n请给出关键发现。"}
                    ],
                    "temperature": 0.3, "max_tokens": 200
                }, timeout=20)
            if sum_resp.status_code == 200:
                summary = sum_resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass

    return {
        "sql": sql,
        "explanation": explanation,
        "summary": summary,
        "chart_type": chart_type,
        "row_count": len(rows),
        "data": rows[:100],  # 最多返回100条
    }


if __name__ == "__main__":
    # 命令行模式: echo '{"question":"..."}' | python hermes_bridge.py
    try:
        input_data = json.loads(sys.stdin.read())
        question = input_data.get("question", "")
        history = input_data.get("history", [])
        result = process(question, history)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
