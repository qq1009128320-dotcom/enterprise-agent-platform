"""
行业数字员工——企业记忆智能体
Hermes Agent + 记忆引擎 演示面板
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import subprocess as sp

st.set_page_config(page_title="企业记忆智能体", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# ── 样式 ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stat-card { background: linear-gradient(135deg, #0f1724 0%, #1a1f35 100%); border: 1px solid #1e293b; border-radius: 10px; padding: 1rem; text-align: center; }
    .stat-value { font-size: 1.6rem; font-weight: 700; color: #22d3ee; }
    .stat-label { font-size: 0.7rem; color: #64748b; letter-spacing: 0.05em; }
    
    .step-box { 
        background: #0d1520; border: 1px solid #1a2744; border-radius: 8px; 
        padding: 0.8rem 1rem; margin: 0.4rem 0; 
        display: flex; align-items: flex-start; gap: 0.8rem;
    }
    .step-num { 
        width: 26px; height: 26px; border-radius: 50%; 
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 700; flex-shrink: 0;
    }
    .step-active { background: #22d3ee; color: #000; }
    .step-done { background: #1e3a5f; color: #22d3ee; }
    .step-pending { background: #1a1f2e; color: #475569; }
    
    .memory-layer { 
        background: #0d1520; border: 1px solid #1a2744; border-radius: 8px; 
        padding: 0.7rem; text-align: center; 
    }
    .memory-layer .icon { font-size: 1.2rem; }
    .memory-layer .label { font-size: 0.72rem; color: #22d3ee; font-weight: 600; margin: 0.2rem 0; }
    .memory-layer .value { font-size: 0.78rem; color: #cbd5e1; }
    
    .arch-layer { 
        background: #0d1520; border: 1px solid; border-radius: 8px; 
        padding: 0.8rem 1rem; margin: 0.3rem 0; text-align: center;
    }
    
    div[data-testid="stSidebar"] { background: #070b14; }
    section[data-testid="stSidebar"] .stButton button { 
        background: transparent; border: 1px solid #1e293b; color: #94a3b8; 
        font-size: 0.8rem; padding: 0.5rem 0.8rem; border-radius: 6px; text-align: left;
        width: 100%; transition: all 0.2s;
    }
    section[data-testid="stSidebar"] .stButton button:hover { border-color: #22d3ee; color: #22d3ee; background: #0f1a2e; }
    
    .sql-block { background: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 0.6rem 0.8rem; font-family: 'SF Mono','Consolas',monospace; font-size: 0.75rem; color: #8b949e; margin: 0.3rem 0; }
    
    hr { border-color: #1e293b; }
</style>
""", unsafe_allow_html=True)

# ── 数据库 ────────────────────────────────────────────
DB_PATH = "/home/administrator/finance_data/db/finance.db"

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data
def query(sql):
    return pd.read_sql_query(sql, get_conn())

# ── Sidebar: 演示场景 ─────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 企业记忆智能体")
    st.caption("Hermes Agent + 记忆引擎")
    st.markdown("---")

    st.markdown("#### 📋 演示场景")

    scenario = st.radio("选择场景", [
        "💬 真实对话（自由提问）",
        "🏠 系统架构总览",
        "🔍 场景一：Agent 对话式数据查询",
        "🧩 场景二：记忆引擎如何工作",
        "📊 场景三：自动报表生成",
        "🔄 场景四：Agent 纠错与学习",
        "📋 场景五：飞书协作推送",
    ], label_visibility="collapsed")

    st.markdown("---")

    # 记忆引擎状态
    st.markdown("#### 🧩 记忆引擎状态")
    mem_data = [
        ("📚", "Memory Tree", "35条", "文档向量索引"),
        ("⭐", "偏好记忆", "14条", "企业规则"),
        ("🔧", "纠错记忆", "6条", "历史纠正"),
        ("🕸️", "知识图谱", "34实体", "关系网络"),
    ]
    for icon, label, val, sub in mem_data:
        st.markdown(f'<div class="memory-layer"><div class="icon">{icon}</div><div class="label">{label}</div><div class="value">{val}</div><div style="font-size:0.65rem;color:#475569;">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("行业数字员工——企业记忆智能体")


# ── 真实对话 ──────────────────────────────────────────
if scenario == "💬 真实对话（自由提问）":
    st.markdown("### 💬 真实对话 — Hermes Agent 后台处理")
    st.caption("输入任何自然语言问题，后台 Hermes Agent 桥接服务调用 LLM + 记忆引擎，返回结果。")

    # 聊天历史
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 渲染历史
    for i, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🧠"):
                if msg.get("error"):
                    st.error(msg["content"])
                else:
                    st.markdown(f"**{msg.get('explanation','')}**")
                    if msg.get("summary"):
                        st.info(msg["summary"])
                    if "sql" in msg:
                        with st.expander("🔍 SQL"):
                            st.code(msg["sql"], language="sql")
                    if "fig" in msg:
                        st.plotly_chart(msg["fig"], use_container_width=True, key=f"rc_{i}")
                    if "metric_val" in msg:
                        st.markdown(f'<div class="stat-card"><div class="stat-value">{msg["metric_val"]}</div><div class="stat-label">{msg.get("metric_label","")}</div></div>', unsafe_allow_html=True)
                    if "df" in msg:
                        with st.expander("📋 数据明细"):
                            st.dataframe(msg["df"], use_container_width=True)

    # 输入框
    c1, c2 = st.columns([8, 1])
    with c2:
        if st.button("🗑️", use_container_width=True, key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    if prompt := st.chat_input("输入问题，例如：公司上个月花了多少钱？今年利润怎么样？"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.spinner("🧠 Hermes Agent 正在处理..."):
            try:
                inp = json.dumps({"question": prompt, "history": [
                    {"role": h["role"], "content": h.get("content","")}
                    for h in st.session_state.chat_history[-6:-1]
                ]}, ensure_ascii=False)
                proc = sp.run(
                    ["python3", "/home/administrator/enterprise-agent-platform/demo/hermes_bridge.py"],
                    input=inp, capture_output=True, text=True, timeout=45
                )
                if proc.returncode != 0:
                    result = {"error": proc.stderr[:300]}
                else:
                    result = json.loads(proc.stdout)
            except sp.TimeoutExpired:
                result = {"error": "处理超时（45秒），换个简单的问题试试"}
            except Exception as e:
                result = {"error": str(e)}

        if "error" in result:
            st.session_state.chat_history.append({
                "role": "agent", "content": f"❌ {result['error']}",
                "error": True
            })
        else:
            msg = {
                "role": "agent",
                "explanation": result.get("explanation", ""),
                "sql": result.get("sql", ""),
                "summary": result.get("summary", ""),
                "content": result.get("explanation", "")
            }

            # 渲染结果
            data = result.get("data", [])
            chart_type = result.get("chart_type", "table")

            if data:
                df = pd.DataFrame(data)
                if chart_type == "metric" and len(df) == 1:
                    val = list(df.iloc[0])[0]
                    if isinstance(val, (int, float)):
                        msg["metric_val"] = f"¥{val:,.0f}"
                        msg["metric_label"] = result.get("explanation", "")
                elif chart_type == "pie" and len(df.columns) >= 2:
                    nc = df.select_dtypes(include='number').columns.tolist()
                    cc = [c for c in df.columns if c not in nc]
                    if nc and cc:
                        fig = px.pie(df, names=cc[0], values=nc[0], template='plotly_dark', hole=0.4)
                        fig.update_layout(height=350, margin=dict(l=20,r=20,t=10,b=10))
                        msg["fig"] = fig
                elif chart_type in ("bar", "barh") and len(df.columns) >= 2:
                    nc = df.select_dtypes(include='number').columns.tolist()
                    cc = [c for c in df.columns if c not in nc]
                    if nc and cc:
                        orient = 'h' if chart_type == 'barh' else 'v'
                        fig = px.bar(df, x=nc[0] if orient == 'h' else cc[0],
                                    y=cc[0] if orient == 'h' else nc[0],
                                    orientation=orient, template='plotly_dark',
                                    color=nc[0] if orient == 'h' else None,
                                    color_continuous_scale='blues')
                        fig.update_layout(height=max(260, len(df)*22) if orient == 'h' else 350,
                                        margin=dict(l=20,r=20,t=10,b=10))
                        if orient == 'h':
                            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                        msg["fig"] = fig
                elif chart_type == "line" and len(df.columns) >= 2:
                    nc = df.select_dtypes(include='number').columns.tolist()
                    cc = [c for c in df.columns if c not in nc]
                    if nc and cc:
                        fig = px.line(df, x=cc[0], y=nc, markers=True, template='plotly_dark')
                        fig.update_layout(height=350, hovermode='x unified', margin=dict(l=20,r=20,t=10,b=10))
                        msg["fig"] = fig

                if not msg.get("fig") and not msg.get("metric_val"):
                    msg["df"] = df

            st.session_state.chat_history.append(msg)
        st.rerun()


# ── 场景渲染 ──────────────────────────────────────────
elif scenario == "🏠 系统架构总览":
    st.markdown("### 🏠 系统架构总览")
    st.caption("行业数字员工——企业记忆智能体：Hermes Agent 编排 + 四层记忆引擎 + 企业数据")

    # 架构图
    arch_layers = [
        ("交互层", "#22d3ee", "Streamlit 演示面板 · 飞书机器人 @对话 · 飞书 Base 多维表格"),
        ("Agent 编排层", "#34d399", "Hermes Agent — 对话管理 · 工具调度 · 技能路由 · 多轮上下文"),
        ("技能层", "#34d399", "数据查询 · 报表生成 · 知识摄入 · 飞书集成 · 自动纠错"),
        ("记忆引擎", "#a78bfa", "MCP Server — Memory Tree(向量检索) · 偏好记忆(规则) · 纠错记忆(历史) · 知识图谱(关系)"),
        ("数据层", "#a78bfa", "SQLite(301万条分录) · ChromaDB(向量索引) · BGE-M3(语义匹配)"),
    ]
    for name, color, desc in arch_layers:
        st.markdown(f'<div class="arch-layer" style="border-color:{color};"><div style="color:{color};font-weight:600;font-size:0.85rem;">{name}</div><div style="color:#94a3b8;font-size:0.75rem;margin-top:0.2rem;">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 数据统计
    cols = st.columns(4)
    vals = [("3,017,575", "会计分录"), ("116", "会计科目"), ("21", "业务部门"), ("2个年度", "2024-2025")]
    for i, (v, l) in enumerate(vals):
        cols[i].markdown(f'<div class="stat-card"><div class="stat-value">{v}</div><div class="stat-label">{l}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 四层记忆详解
    st.markdown("#### 🧩 四层记忆架构（核心竞争力）")
    c1, c2, c3, c4 = st.columns(4)
    mems = [
        ("📚 Memory Tree", "文档自动切片、向量化存储、语义检索", "制度文件、会计分录 → 自动入库"),
        ("⭐ 偏好记忆", "企业特殊规则永久存储", "会计周期25号、研发费用化、收入算法"),
        ("🔧 纠错记忆", "曾纠正的错误+正确做法", "预付贷方→应付账款重分类"),
        ("🕸️ 知识图谱", "实体关系网络，支持关联推理", "34个实体·29条关系·部门归属"),
    ]
    for i, (title, desc, example) in enumerate(mems):
        with [c1, c2, c3, c4][i]:
            st.markdown(f'<div style="background:#0d1520;border:1px solid #1a2744;border-radius:8px;padding:0.8rem;height:100%;"><div style="color:#22d3ee;font-weight:600;font-size:0.8rem;">{title}</div><div style="color:#94a3b8;font-size:0.72rem;margin:0.3rem 0;">{desc}</div><div style="color:#475569;font-size:0.68rem;">例：{example}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 部署方案
    st.markdown("#### 🚀 部署方案")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**本地部署**\n- Docker Compose 一键启动\n- 数据不出企业内网\n- 最低 4核/8GB/20GB")
    with dc2:
        st.markdown("**飞书集成**\n- 飞书机器人 @对话\n- Base 多维表格数据同步\n- 主流中国企业协作工具")


# ── 场景一：Agent 对话式数据查询 ──────────────────────
elif scenario == "🔍 场景一：Agent 对话式数据查询":
    st.markdown("### 🔍 场景一：Agent 对话式数据查询")
    st.caption("用户自然语言提问 → Hermes Agent 编排 → 查记忆 → 理解意图 → 生成SQL → 执行 → 可视化")

    # 演示输入
    demo_q = st.selectbox("选择演示问题", [
        "公司上个月花了多少钱？",
        "哪个部门费用最高？",
        "销售培训部的费用趋势怎么样？",
        "银行存款余额变化情况",
        "2025年整体收支结构",
    ])

    if st.button("▶️ 运行演示", type="primary"):
        steps = st.container()

        # Step 1: 用户输入
        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">1</div><div><strong>用户输入</strong><br><span style="color:#94a3b8;">👤 "{demo_q}"</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.6)

        # Step 2: Hermes 查记忆
        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">2</div><div><strong>Hermes Agent 检索记忆引擎</strong><br><span style="color:#94a3b8;">查询偏好记忆：会计周期=25号→下月25号、收入算法=max(借,贷)、研发全部费用化</span><br><span style="color:#22d3ee;font-size:0.75rem;">✅ 命中 3 条相关规则</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.6)

        # Step 3: 理解意图
        with steps:
            if "花" in demo_q or "费用" in demo_q:
                intent = "费用查询 — 汇总销售/管理/财务费用"
            elif "收入" in demo_q or "收支" in demo_q:
                intent = "收支结构 — 收入+成本+费用全貌"
            elif "部门" in demo_q:
                intent = "部门分析 — 按部门分组排序"
            elif "银行" in demo_q or "存款" in demo_q:
                intent = "资金查询 — 现金/银行科目汇总"
            else:
                intent = "综合数据查询"

            st.markdown(f'<div class="step-box"><div class="step-num step-active">3</div><div><strong>Agent 理解意图</strong><br><span style="color:#94a3b8;">意图识别：{intent}</span><br><span style="color:#22d3ee;font-size:0.75rem;">✅ 应用记忆规则：收入取max(借,贷)、费用取sum(借方)</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.5)

        # Step 4: 生成并执行 SQL
        real_queries = {
            "公司上个月花了多少钱？": {
                "sql": "SELECT ROUND(SUM(debit), 2) AS 上个月总费用\nFROM journal\nWHERE (account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%')\n  AND year = 2025 AND period = 5",
                "chart": "metric"
            },
            "哪个部门费用最高？": {
                "sql": "SELECT department AS 部门, ROUND(SUM(debit), 2) AS 费用总额\nFROM journal\nWHERE (account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%')\n  AND department IS NOT NULL AND department != ''\nGROUP BY department\nORDER BY 费用总额 DESC\nLIMIT 10",
                "chart": "barh"
            },
            "销售培训部的费用趋势怎么样？": {
                "sql": "SELECT period AS 月份, ROUND(SUM(debit), 2) AS 费用\nFROM journal\nWHERE department = '销售培训部'\n  AND (account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%')\nGROUP BY period\nORDER BY period",
                "chart": "line"
            },
            "银行存款余额变化情况": {
                "sql": "SELECT account_name AS 账户,\n       ROUND(SUM(credit) - SUM(debit), 2) AS 净流入\nFROM journal\nWHERE account_code LIKE '100%'\nGROUP BY account_name\nORDER BY 净流入 DESC\nLIMIT 8",
                "chart": "barh"
            },
            "2025年整体收支结构": {
                "sql": "SELECT CASE WHEN account_code LIKE '6001%' THEN '收入'\n            WHEN account_code LIKE '6401%' THEN '成本'\n            WHEN account_code LIKE '6601%' THEN '销售费用'\n            WHEN account_code LIKE '6602%' THEN '管理费用'\n            WHEN account_code LIKE '6603%' THEN '财务费用'\n       END AS 类别,\n       ROUND(SUM(CASE WHEN account_code LIKE '6001%' THEN\n           CASE WHEN debit>credit THEN debit ELSE credit END\n           ELSE debit END), 2) AS 金额\nFROM journal WHERE year=2025\nGROUP BY 类别 HAVING 类别 IS NOT NULL\nORDER BY 金额 DESC",
                "chart": "pie"
            },
        }

        qdata = real_queries[demo_q]

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">4</div><div><strong>Agent 生成 SQL 并执行</strong></div></div>', unsafe_allow_html=True)
            st.code(qdata["sql"], language="sql")

        # Step 5: 结果
        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">5</div><div><strong>返回结果</strong></div></div>', unsafe_allow_html=True)

            try:
                df = query(qdata["sql"])
            except:
                df = query(qdata["sql"].replace("\n", " "))

            chart_type = qdata["chart"]

            if chart_type == "metric" and len(df) == 1:
                val = df.iloc[0, 0]
                st.markdown(f'<div class="stat-card"><div class="stat-value">¥{val:,.0f}</div><div class="stat-label">上个月总费用</div></div>', unsafe_allow_html=True)

            elif chart_type == "barh":
                num_col = df.select_dtypes(include='number').columns[0]
                cat_col = [c for c in df.columns if c != num_col][0]
                fig = px.bar(df, x=num_col, y=cat_col, orientation='h', template='plotly_dark',
                            color=num_col, color_continuous_scale='blues')
                fig.update_layout(height=max(260, len(df)*22), yaxis={'categoryorder': 'total ascending'},
                                margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "line":
                fig = px.line(df, x=df.columns[0], y=df.columns[1], markers=True, template='plotly_dark')
                fig.update_layout(height=320, margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "pie":
                num_col = df.select_dtypes(include='number').columns[0]
                cat_col = [c for c in df.columns if c != num_col][0]
                fig = px.pie(df, names=cat_col, values=num_col, template='plotly_dark', hole=0.45)
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📋 数据明细"):
                st.dataframe(df, use_container_width=True)


# ── 场景二：记忆引擎如何工作 ──────────────────────────
elif scenario == "🧩 场景二：记忆引擎如何工作":
    st.markdown("### 🧩 场景二：记忆引擎如何工作")
    st.caption("四层记忆架构：Agent 每次对话自动检索四层记忆，越用越聪明")

    st.markdown("---")

    # 记忆层级展示
    st.markdown("#### 记忆检索流程（Agent 每次对话自动执行）")

    flow_steps = [
        ("1️⃣ 用户提问", "\"这个月的研发费用化处理了吗？\"", "#22d3ee"),
        ("2️⃣ 查偏好记忆", "命中规则：「研发支出全部费用化，不资本化」", "#34d399"),
        ("3️⃣ 查纠错记忆", "无相关纠错记录，跳过", "#a78bfa"),
        ("4️⃣ 查 Memory Tree", "检索到「2026年度研发预算：大模型训练1800万、推理700万、标注500万」", "#f59e0b"),
        ("5️⃣ 查知识图谱", "实体「研发部」→属于→「AI部门」→关联→「2026预算」", "#ec4899"),
        ("6️⃣ Agent 综合回答", "结合偏好+Tree+图谱，给出精准回答", "#22d3ee"),
    ]
    for title, desc, color in flow_steps:
        st.markdown(f'<div class="step-box"><div style="color:{color};font-weight:600;font-size:0.85rem;min-width:120px;">{title}</div><div style="color:#94a3b8;font-size:0.8rem;">{desc}</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # 四层记忆详细状态
    st.markdown("#### 当前记忆状态")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**📚 Memory Tree（文档向量库）**")
        tree_items = [
            "2026年度研发预算（AI部门）",
            "化妆品公司2025年1-6月账表分析",
            "企业差旅管理制度",
            "财务政策：研发费用化、会计周期",
            "报表驾驶舱v3.0设计规范",
        ]
        for item in tree_items:
            st.markdown(f'<div style="background:#0d1520;border:1px solid #1a2744;border-radius:6px;padding:0.5rem 0.8rem;margin:0.2rem 0;font-size:0.78rem;color:#94a3b8;">📄 {item}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown("**⭐ 偏好记忆（企业规则）**")
        prefs = [
            ("会计周期", "每月25日→下月25日", "field_alias"),
            ("研发支出", "全部费用化，不资本化", "policy"),
            ("收入算法", "max(借方, 贷方)为实际发生额", "field_alias"),
            ("预付账款贷方", "重分类至应付账款", "policy"),
            ("化妆品模式", "纯贸易/经销，无生产成本", "policy"),
            ("电商推广费", "科目6601.03 — 最大费用项", "field_alias"),
        ]
        for rule, detail, cat in prefs:
            st.markdown(f'<div style="background:#0d1520;border:1px solid #1a2744;border-radius:6px;padding:0.5rem 0.8rem;margin:0.2rem 0;"><span style="color:#22d3ee;font-size:0.75rem;">{rule}</span> <span style="color:#64748b;font-size:0.65rem;">[{cat}]</span><br><span style="color:#94a3b8;font-size:0.78rem;">{detail}</span></div>', unsafe_allow_html=True)


# ── 场景三：自动报表生成 ──────────────────────────────
elif scenario == "📊 场景三：自动报表生成":
    st.markdown("### 📊 场景三：自动报表生成")
    st.caption("一句话生成专业财务报表 → Agent 自动计算、图表呈现、飞书推送")

    report_type = st.selectbox("报表类型", ["月度费用分析", "部门费用排名", "收入成本利润", "资金渠道分布"])

    if st.button("▶️ 一句话生成报表", type="primary"):
        steps = st.container()

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">1</div><div><strong>用户指令</strong><br><span style="color:#94a3b8;">👤 "生成{report_type}报表"</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.4)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">2</div><div><strong>Agent 查记忆引擎</strong><br><span style="color:#94a3b8;">✅ 收入算法=max(借,贷) | ✅ 费用=sum(借方) | ✅ 预付贷方重分类</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.4)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">3</div><div><strong>Agent 生成 SQL + 执行</strong></div></div>', unsafe_allow_html=True)

        # 实际查询
        if report_type == "月度费用分析":
            sql = """
                SELECT year as 年, period as 月,
                       ROUND(SUM(CASE WHEN account_code LIKE '6601%' THEN debit ELSE 0 END),2) as 销售费用,
                       ROUND(SUM(CASE WHEN account_code LIKE '6602%' THEN debit ELSE 0 END),2) as 管理费用,
                       ROUND(SUM(CASE WHEN account_code LIKE '6603%' THEN debit ELSE 0 END),2) as 财务费用
                FROM journal
                WHERE account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%'
                GROUP BY year, period ORDER BY year, period
            """
        elif report_type == "部门费用排名":
            sql = """
                SELECT department as 部门, ROUND(SUM(debit),2) as 费用总额
                FROM journal
                WHERE (account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%')
                  AND department IS NOT NULL AND department != ''
                GROUP BY department ORDER BY 费用总额 DESC LIMIT 15
            """
        elif report_type == "收入成本利润":
            sql = """
                SELECT period as 月份,
                       ROUND(SUM(CASE WHEN account_code LIKE '6001%' THEN CASE WHEN debit>credit THEN debit ELSE credit END ELSE 0 END),2) as 收入,
                       ROUND(SUM(CASE WHEN account_code LIKE '6401%' THEN CASE WHEN debit>credit THEN debit ELSE credit END ELSE 0 END),2) as 成本,
                       ROUND(SUM(CASE WHEN account_code LIKE '660%' THEN debit ELSE 0 END),2) as 费用
                FROM journal WHERE year=2025 GROUP BY period ORDER BY period
            """
        else:
            sql = """
                SELECT CASE WHEN account_name LIKE '%支付宝%' THEN '支付宝'
                            WHEN account_name LIKE '%微信%' THEN '微信商户'
                            WHEN account_name LIKE '%银行%' THEN '银行存款' END as 渠道,
                       ROUND(SUM(credit)-SUM(debit),2) as 净流入
                FROM journal WHERE account_code LIKE '100%' GROUP BY 渠道 ORDER BY 净流入 DESC
            """

        st.code(sql, language="sql")

        df = query(sql)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">4</div><div><strong>生成可视化报表</strong> · 返回 {len(df)} 条</div></div>', unsafe_allow_html=True)

        # 图表
        num_cols = df.select_dtypes(include='number').columns.tolist()
        cat_cols = [c for c in df.columns if c not in num_cols]

        if len(num_cols) >= 3 and report_type == "月度费用分析":
            fig = go.Figure()
            for nc, color in zip(num_cols, ['#22d3ee', '#34d399', '#a78bfa']):
                fig.add_trace(go.Bar(name=nc, x=df[cat_cols[0]].astype(str), y=df[nc], marker_color=color))
            fig.update_layout(barmode='stack', template='plotly_dark', height=380)
            st.plotly_chart(fig, use_container_width=True)
        elif report_type == "部门费用排名":
            fig = px.bar(df, x=num_cols[0], y=cat_cols[0], orientation='h', template='plotly_dark',
                        color=num_cols[0], color_continuous_scale='blues')
            fig.update_layout(height=max(300, len(df)*22), yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        elif report_type == "收入成本利润":
            fig = px.line(df, x=cat_cols[0], y=num_cols, markers=True, template='plotly_dark')
            fig.update_layout(height=380, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = px.pie(df, names=cat_cols[0], values=num_cols[0], template='plotly_dark', hole=0.4)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">5</div><div><strong>✅ 报表生成完毕</strong><br><span style="color:#94a3b8;">可一键推送至飞书 Base 多维表格</span></div></div>', unsafe_allow_html=True)


# ── 场景四：Agent 纠错与学习 ──────────────────────────
elif scenario == "🔄 场景四：Agent 纠错与学习":
    st.markdown("### 🔄 场景四：Agent 纠错与学习")
    st.caption("用户纠正 → Agent 永久记住 → 下次不再犯错（记忆引擎核心能力）")

    if st.button("▶️ 演示纠错学习流程", type="primary"):
        steps = st.container()

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">1</div><div><strong>第一轮对话</strong><br><span style="color:#94a3b8;">👤 "预付账款余额是多少？"</span><br>🤖 "预付账款借方 58,824.80，贷方 2,340,000.00，净贷方 2,281,175.20"</div></div>', unsafe_allow_html=True)
            time.sleep(0.6)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">2</div><div><strong>用户纠正</strong><br><span style="color:#f87171;">👤 "不对！预付账款的贷方余额应该重分类到应付账款，不能直接算在预付账款余额里"</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.5)

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-active">3</div><div><strong>Agent 记录到偏好记忆</strong><br><span style="color:#22d3ee;">✅ 偏好记忆新增：「预付账款贷方余额 → 重分类至应付账款」</span><br><span style="color:#a78bfa;">✅ 纠错记忆新增：「不可直接计算预付账款净额，需先重分类贷方余额」</span></div></div>', unsafe_allow_html=True)
            time.sleep(0.5)

        # 实际查询证明
        try:
            df = query("SELECT ROUND(SUM(debit),2) as 借方, ROUND(SUM(credit),2) as 贷方 FROM journal WHERE account_code LIKE '1123%'")
            if not df.empty:
                d, c = df.iloc[0, 0], df.iloc[0, 1]
                with steps:
                    st.markdown(f'<div class="step-box"><div class="step-num step-active">4</div><div><strong>第二轮的 Agent 自动应用规则</strong><br><span style="color:#94a3b8;">👤 "预付账款余额是多少？"</span><br>🤖 "预付账款余额为借方 <b>{d:,.2f}</b>。另外，贷方 <b>{c:,.2f}</b> 已按规则重分类至应付账款。"<br><span style="color:#22d3ee;">✅ Agent 自动应用了纠正后的规则！</span></div></div>', unsafe_allow_html=True)
        except:
            pass

        with steps:
            st.markdown(f'<div class="step-box"><div class="step-num step-done">✅</div><div><strong>核心价值</strong><br><span style="color:#94a3b8;">普通 AI 问答每次都是"金鱼记忆"，纠正过的错误下次还会犯。<br>企业记忆智能体的四层记忆架构让 Agent <b>永久记住</b>每一次纠正，越用越聪明。</span></div></div>', unsafe_allow_html=True)


# ── 场景五：飞书协作推送 ──────────────────────────────
elif scenario == "📋 场景五：飞书协作推送":
    st.markdown("### 📋 场景五：飞书协作推送")
    st.caption("报表生成 → 自动推送至飞书 Base 多维表格 → 团队成员实时协作")

    flow = [
        ("1", "Agent 生成月报", "一句话「生成本月费用分析」→ Agent 自动计算并生成图表", "#22d3ee"),
        ("2", "推送至飞书 Base", "调用飞书 API，将报表数据写入 Base 多维表格", "#34d399"),
        ("3", "团队成员查看", "财务部、管理层在飞书中直接查看和协作", "#a78bfa"),
        ("4", "自动定时更新", "Cron 定时任务：每月1号自动生成上月报表并推送", "#f59e0b"),
    ]

    for num, title, desc, color in flow:
        st.markdown(f'<div class="step-box"><div class="step-num" style="background:{color};color:#000;">{num}</div><div><strong style="color:{color};">{title}</strong><br><span style="color:#94a3b8;font-size:0.8rem;">{desc}</span></div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.info("📌 飞书集成已授权（用户：阿达，token 有效期至 5月26日），支持文档、Base多维表格、消息推送。")

st.markdown("---")
st.caption("行业数字员工——企业记忆智能体 · Hermes Agent + 记忆引擎演示面板")
