"""
行业数字员工——企业记忆智能体
LLM 驱动的对话式智能分析
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import re
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com") + "/v1/chat/completions"

st.set_page_config(page_title="企业记忆智能体", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")

# ── 样式 ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stat-card { background: linear-gradient(135deg, #111827 0%, #1a1f35 100%); border: 1px solid #1f2937; border-radius: 12px; padding: 1rem; text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: 700; color: #22d3ee; }
    .stat-label { font-size: 0.75rem; color: #6b7280; }
    .sidebar-box { background: #0d1320; border: 1px solid #1a2744; border-radius: 8px; padding: 0.8rem; margin: 0.5rem 0; font-size: 0.8rem; color: #9ca3af; line-height: 1.5; }
    .sidebar-box .title { font-size: 0.75rem; color: #6b7280; margin-bottom: 0.4rem; }
    div[data-testid="stSidebar"] { background: #070b14; }
    .tip-box { background: #0d1a16; border: 1px solid #1a3a2e; border-radius: 6px; padding: 0.6rem 0.8rem; font-size: 0.75rem; color: #6ee7b7; }
    section.main > div:has(.stChatMessage) { padding-top: 0; }
</style>
""", unsafe_allow_html=True)

# ── 数据库 ────────────────────────────────────────────
DB_PATH = "/home/administrator/finance_data/db/finance.db"

@st.cache_resource
def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def run_sql(sql):
    return pd.read_sql_query(sql, get_conn())

@st.cache_data
def get_schema():
    """获取数据库 schema 信息给 LLM"""
    conn = get_conn()
    # 表结构
    cols = pd.read_sql_query("PRAGMA table_info(journal)", conn)
    schema = "表 journal (" + ", ".join(f"{r['name']} {r['type']}" for _, r in cols.iterrows()) + ")\n\n"

    # 科目列表（前50个重要科目）
    accts = pd.read_sql_query("""
        SELECT account_code, account_name, COUNT(*) as cnt,
               ROUND(SUM(debit),0) as total_debit, ROUND(SUM(credit),0) as total_credit
        FROM journal GROUP BY account_code ORDER BY cnt DESC LIMIT 50
    """, conn)
    schema += "主要科目:\n"
    for _, r in accts.iterrows():
        schema += f"  {r['account_code']} | {r['account_name']} | {r['cnt']}条 | 借{r['total_debit']:.0f} 贷{r['total_credit']:.0f}\n"

    # 部门列表
    depts = pd.read_sql_query("SELECT DISTINCT department FROM journal WHERE department IS NOT NULL AND department != '' ORDER BY department", conn)
    schema += f"\n部门: {', '.join(depts['department'].tolist())}\n"

    # 年份
    years = pd.read_sql_query("SELECT DISTINCT year FROM journal ORDER BY year", conn)
    schema += f"年份: {', '.join(map(str, years['year'].tolist()))}\n"

    # 数据量
    cnt = pd.read_sql_query("SELECT COUNT(*) as n FROM journal", conn)
    schema += f"\n总记录数: {cnt['n'].iloc[0]:,} 条\n"

    return schema

SCHEMA = get_schema()

# ── LLM 调用 ──────────────────────────────────────────
SYSTEM_PROMPT = f"""你是一个企业财务数据分析助手。你可以访问一个叫 journal 的表，结构如下：

{SCHEMA}

你的任务：根据用户的中文问题，生成一条 SQLite SQL 查询。

规则：
1. 所有金额字段用 ROUND(..., 2) 保留两位小数
2. 费用类科目代码以 6601(销售)、6602(管理)、6603(财务) 开头
3. 收入类科目代码以 6001 开头
4. 成本类科目代码以 6401 开头
5. 资产负债类科目代码以 1(资产)、2(负债)、3(权益)、4(成本)、5(损益) 开头，但 6001/6401/6601-6603 除外
6. 收入的算法是 max(debit, credit) —— 因为收入记贷方但可能有退货
7. 费用的算法是 sum(debit) —— 费用记借方
8. 银行/现金科目代码以 100 开头
9. 如果用户问"上个月"，取当前最大月份-1；"这个月"取最大月份；"今年"取最大年份
10. 如果用户问"花了多少钱"/"费用"/"支出"，查询全部费用（6601/6602/6603的debit总额）
11. 如果用户问"赚了多少"/"利润"，用 收入 - 成本 - 费用 估算
12. 不确定时：宁可多查，不要太限制

返回格式：严格的 JSON，不要 markdown 包裹：
{{"sql": "你的SQL语句", "explanation": "简短说明这查询做了什么", "chart": "line|bar|barh|pie|table"}}"""


def ask_llm(question: str, history: list = None) -> dict:
    """调用 DeepSeek，返回 {sql, explanation, chart}"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for h in history[-6:]:  # 最近3轮对话
            role = "user" if h["role"] == "user" else "assistant"
            content = h["content"]
            if h.get("sql"):
                content += f"\n[SQL: {h['sql'][:200]}]"
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": messages, "temperature": 0.1, "max_tokens": 800},
            timeout=30
        )
        if resp.status_code != 200:
            return {"error": f"API 错误: {resp.status_code}"}

        text = resp.json()["choices"][0]["message"]["content"].strip()

        # 清理可能的 markdown 包裹
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

        result = json.loads(text)
        return {
            "sql": result.get("sql", ""),
            "explanation": result.get("explanation", ""),
            "chart": result.get("chart", "table")
        }
    except json.JSONDecodeError:
        return {"error": "LLM 返回格式异常", "raw": text[:500]}
    except Exception as e:
        return {"error": str(e)}


# ── 图表生成 ──────────────────────────────────────────
def make_chart(df, chart_type, title):
    """根据 chart_type 生成 Plotly 图表"""
    fig = None
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if not num_cols:
        return None

    cat_cols = [c for c in df.columns if c not in num_cols]
    x = cat_cols[0] if cat_cols else df.columns[0]

    if chart_type == "barh" and cat_cols:
        fig = px.bar(df, x=num_cols[0], y=x, orientation='h', template='plotly_dark',
                    color=num_cols[0], color_continuous_scale='blues')
        fig.update_layout(height=max(280, len(df)*22), yaxis={'categoryorder': 'total ascending'})
    elif chart_type == "line":
        color = next((c for c in cat_cols if '年' in str(c)), None)
        if color and len(num_cols) == 1:
            fig = px.line(df, x=x, y=num_cols[0], color=color, markers=True, template='plotly_dark')
        else:
            fig = px.line(df, x=x, y=num_cols, markers=True, template='plotly_dark')
        fig.update_layout(height=380, hovermode='x unified')
    elif chart_type == "pie" and cat_cols:
        fig = px.pie(df, names=x, values=num_cols[0], template='plotly_dark', hole=0.4)
        fig.update_layout(height=380)
    elif chart_type == "bar":
        fig = px.bar(df, x=x, y=num_cols, template='plotly_dark', barmode='group')
        fig.update_layout(height=380)
    else:
        return None

    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation='h', yanchor='bottom', y=1.02),
                    title=title, title_font_size=14)
    return fig


# ── Sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 企业记忆智能体")
    st.caption("基于 DeepSeek LLM · 自然语言 → SQL")

    st.markdown('<div class="sidebar-box"><div class="title">📊 数据库</div>301万条会计分录<br>116个科目 · 21个部门</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-box"><div class="title">🧩 记忆引擎</div>Memory Tree: 35条<br>偏好记忆: 14条规则<br>知识图谱: 34实体</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-box"><div class="title">📋 已学会的规则</div>• 会计周期: 25号→下月25号<br>• 研发支出: 全部费用化<br>• 预付贷方: 重分类至应付<br>• 收入 = max(借,贷)</div>', unsafe_allow_html=True)

# ── 主界面 ────────────────────────────────────────────
st.markdown("### 💬 对话式企业数据智能分析")
st.caption("Agent 使用 LLM 理解自然语言，自动生成 SQL 查询并可视化。试试任何问题——越自然越好。")

# 统计
cols = st.columns(4)
for val, label in [("301万", "会计分录"), ("116", "科目"), ("21", "部门"), ("LLM", "驱动")]:
    cols[0].markdown(f'<div class="stat-card"><div class="stat-value">{val}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
    cols = cols[1:]

st.markdown("<br>", unsafe_allow_html=True)

# ── 聊天状态 ──
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "agent", "content": "你好！我是企业记忆智能体，基于 LLM 驱动。我可以理解任何自然语言问题——\n\n试试问我：\n• 公司上个月花了多少钱？\n• 销售培训部今年的费用变化趋势\n• 哪个部门的费用最高？\n• 今年的利润情况怎么样\n• 银行存款还有多少？", "is_welcome": True}
    ]

# ── 渲染历史 ──
for i, msg in enumerate(st.session_state.messages):
    if msg.get("is_welcome"):
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(msg["content"])
    elif msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "agent":
        with st.chat_message("assistant", avatar="🧠"):
            if msg.get("error"):
                st.error(msg["content"])
            else:
                st.markdown(msg.get("explanation", ""))
                if "sql" in msg:
                    with st.expander("🔍 查看生成的 SQL"):
                        st.code(msg["sql"], language="sql")
                if "fig" in msg:
                    st.plotly_chart(msg["fig"], use_container_width=True, key=f"chart_{i}")
                if "df" in msg:
                    with st.expander("📋 数据明细"):
                        st.dataframe(msg["df"], use_container_width=True, height=250)

# ── 输入 ──
st.markdown("---")
col1, col2 = st.columns([8, 1])
with col2:
    if st.button("🗑️ 清空", use_container_width=True):
        st.session_state.messages = [{"role": "agent", "content": "对话已清空，有什么新的问题？", "is_welcome": True}]
        st.rerun()

if prompt := st.chat_input("输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🧠"):
        status = st.empty()

        # 调用 LLM
        status.markdown("🧠 *Agent 正在理解你的问题...*")
        result = ask_llm(prompt, st.session_state.messages)

        if "error" in result:
            status.empty()
            st.error(f"**出错**: {result['error']}")
            if "raw" in result:
                st.code(result["raw"])
            st.session_state.messages.append({"role": "agent", "content": result['error'], "error": True})
        else:
            # 执行 SQL
            status.markdown(f"✅ *{result['explanation']}*  \n📊 *正在查询数据...*")
            try:
                df = run_sql(result["sql"])
            except Exception as e:
                status.empty()
                st.error(f"SQL 执行出错: {e}")
                st.code(result["sql"], language="sql")
                st.session_state.messages.append({"role": "agent", "content": f"SQL 执行出错: {e}", "sql": result["sql"], "error": True})
                st.rerun()

            status.empty()

            if df.empty:
                st.warning("未找到匹配数据")
                st.session_state.messages.append({"role": "agent", "content": "未找到匹配数据", "explanation": result['explanation'], "sql": result['sql']})
            else:
                # 生成图表
                fig = make_chart(df, result["chart"], "")
                msg_data = {
                    "role": "agent",
                    "explanation": result["explanation"],
                    "sql": result["sql"],
                    "content": result["explanation"]
                }
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    msg_data["fig"] = fig
                else:
                    st.dataframe(df, use_container_width=True, height=300)
                    msg_data["df"] = df

                st.caption(f"返回 {len(df)} 条记录")
                st.session_state.messages.append(msg_data)

    st.rerun()

st.markdown("---")
st.caption("行业数字员工——企业记忆智能体 · LLM 驱动 · 自然语言 → SQL → 可视化 · 全程透明可审计")
