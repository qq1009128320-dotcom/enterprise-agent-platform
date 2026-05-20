"""
行业数字员工——企业记忆智能体
Streamlit 演示界面 for 2026武汉AI智能体大赛·经开区
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="企业记忆智能体",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 数据库连接 ──────────────────────────────────────────
DB_PATH = "/home/administrator/finance_data/db/finance.db"

@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=300)
def run_query(sql, params=None):
    conn = get_connection()
    return pd.read_sql_query(sql, conn, params=params)

# ── 预定义查询 ──────────────────────────────────────────
PRESET_QUERIES = {
    "各部门费用排名": """
        SELECT department, ROUND(SUM(debit), 2) as total_expense
        FROM journal
        WHERE account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%'
          AND department IS NOT NULL AND department != ''
        GROUP BY department
        ORDER BY total_expense DESC
    """,
    "月度收入趋势": """
        SELECT year, period, ROUND(SUM(CASE WHEN debit > credit THEN debit ELSE credit END), 2) as revenue
        FROM journal
        WHERE account_code LIKE '6001%'
        GROUP BY year, period
        ORDER BY year, period
    """,
    "月度费用趋势": """
        SELECT year, period,
               ROUND(SUM(CASE WHEN account_code LIKE '6601%' THEN debit ELSE 0 END), 2) as sales_expense,
               ROUND(SUM(CASE WHEN account_code LIKE '6602%' THEN debit ELSE 0 END), 2) as admin_expense,
               ROUND(SUM(CASE WHEN account_code LIKE '6603%' THEN debit ELSE 0 END), 2) as finance_expense
        FROM journal
        WHERE account_code LIKE '6601%' OR account_code LIKE '6602%' OR account_code LIKE '6603%'
        GROUP BY year, period
        ORDER BY year, period
    """,
    "核心科目余额": """
        SELECT account_code, account_name,
               ROUND(SUM(debit), 2) as total_debit,
               ROUND(SUM(credit), 2) as total_credit,
               ROUND(SUM(debit) - SUM(credit), 2) as balance
        FROM journal
        WHERE account_code NOT LIKE '660%' AND account_code NOT LIKE '600%'
        GROUP BY account_code
        HAVING ABS(SUM(debit) - SUM(credit)) > 1000000
        ORDER BY ABS(balance) DESC
        LIMIT 20
    """,
    "电商平台推广费明细": """
        SELECT year, period, department, ROUND(SUM(debit), 2) as promotion_fee
        FROM journal
        WHERE account_name LIKE '%推广%' OR account_name LIKE '%电商%'
        GROUP BY year, period, department
        ORDER BY year, period, promotion_fee DESC
        LIMIT 30
    """,
    "资金渠道分布": """
        SELECT 
            CASE 
                WHEN account_name LIKE '%支付宝%' THEN '支付宝'
                WHEN account_name LIKE '%微信%' THEN '微信商户'
                WHEN account_name LIKE '%银行%' THEN '银行存款'
                ELSE '其他'
            END as channel,
            ROUND(SUM(credit) - SUM(debit), 2) as net_flow
        FROM journal
        WHERE account_code LIKE '100%'
        GROUP BY channel
        ORDER BY net_flow DESC
    """,
}


# ── 侧边栏 ──────────────────────────────────────────────
st.sidebar.title("🧠 企业记忆智能体")
st.sidebar.caption("行业数字员工——企业记忆智能体")

tab = st.sidebar.radio(
    "导航",
    ["🏠 系统概览", "💬 数据对话", "🧩 记忆引擎", "📊 报表中心"],
)

st.sidebar.divider()
st.sidebar.markdown("""
**2026武汉AI智能体大赛**  
经开区·"经开智造"分赛区  
赛道：场景落地类  
""")

st.sidebar.caption(f"数据库: 3,017,575 条分录 | 116个科目 | 21个部门")


# ── Tab 1: 系统概览 ─────────────────────────────────────
if tab == "🏠 系统概览":
    st.title("行业数字员工——企业记忆智能体")
    st.subheader("让每家企业拥有一个懂业务、会学习的 AI 数字员工")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("数据量", "301万条", "会计分录")
    col2.metric("科目数", "116个", "分级科目")
    col3.metric("部门数", "21个", "组织架构")
    col4.metric("记忆层", "4层", "持久记忆")

    st.divider()

    st.markdown("""
    ### 系统架构

    ```
    ┌──────────────────────────────────────────────────┐
    │              交互层                               │
    │   Streamlit Web  │  飞书机器人 @对话              │
    ├──────────────────────────────────────────────────┤
    │           Agent 编排层 (Hermes)                   │
    │  ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐         │
    │  │数据  │ │报表  │ │飞书  │ │知识    │         │
    │  │查询  │ │生成  │ │集成  │ │摄入    │         │
    │  └──────┘ └──────┘ └──────┘ └────────┘         │
    ├──────────────────────────────────────────────────┤
    │       企业记忆引擎 (MCP Server)                   │
    │  ┌─────────┐ ┌─────────┐ ┌───────┐ ┌────────┐  │
    │  │Memory   │ │偏好记忆  │ │纠错   │ │知识    │  │
    │  │Tree     │ │会计周期  │ │记忆   │ │图谱    │  │
    │  └─────────┘ └─────────┘ └───────┘ └────────┘  │
    ├──────────────────────────────────────────────────┤
    │      ChromaDB 向量库 + SQLite 结构化存储         │
    └──────────────────────────────────────────────────┘
    ```

    ### 什么是"四层记忆"？

    普通的 AI 问答每次对话都是"从零开始"，像金鱼一样只有7秒记忆。  
    我们的智能体有**四层持久记忆**，越用越聪明：
    """)

    mem_cols = st.columns(4)
    with mem_cols[0]:
        st.info("**Memory Tree**\n\n文档向量化存储\n语义检索\n自动切片去重")
    with mem_cols[1]:
        st.success("**偏好记忆**\n\n字段映射\n会计周期规则\n企业特殊做法")
    with mem_cols[2]:
        st.warning("**纠错记忆**\n\n历史错误记录\n正确做法\n自动衰减")
    with mem_cols[3]:
        st.error("**知识图谱**\n\n实体关系\n部门归属\n人员关联")


# ── Tab 2: 数据对话 ─────────────────────────────────────
elif tab == "💬 数据对话":
    st.title("💬 对话式数据查询")
    st.caption("像跟同事说话一样，提问即可获得分析结果。不需要写SQL。")

    mode = st.radio("查询方式", ["📋 预设问题", "✏️ 自定义SQL"], horizontal=True)

    if mode == "📋 预设问题":
        query_name = st.selectbox("选择问题", list(PRESET_QUERIES.keys()))
        sql = PRESET_QUERIES[query_name]
        st.code(sql, language="sql")

        if st.button("🔍 执行查询", type="primary"):
            with st.spinner("Agent 正在分析..."):
                df = run_query(sql)
                st.success(f"查询完成，返回 {len(df)} 条记录")
                st.dataframe(df, use_container_width=True, height=300)

                # 自动选择图表类型
                num_cols = df.select_dtypes(include='number').columns.tolist()
                if len(df.columns) >= 2:
                    if 'period' in df.columns or 'year' in df.columns:
                        # 时间序列 -> 折线图
                        x_col = 'period' if 'period' in df.columns else 'year'
                        if len(num_cols) >= 2:
                            fig = px.line(df, x=x_col, y=num_cols[:4],
                                        title=f"{query_name} - 趋势")
                        else:
                            fig = px.bar(df, x=df.columns[0], y=num_cols[0],
                                       title=query_name)
                    else:
                        # 排名 -> 横向柱状图
                        fig = px.bar(df, x=num_cols[0], y=df.columns[0],
                                   orientation='h', title=query_name)
                    st.plotly_chart(fig, use_container_width=True)

    else:
        custom_sql = st.text_area("输入SQL查询", height=100,
                                  placeholder="SELECT department, SUM(debit) FROM journal WHERE ...")
        if st.button("执行", type="primary") and custom_sql.strip():
            try:
                df = run_query(custom_sql)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"查询错误: {e}")


# ── Tab 3: 记忆引擎 ─────────────────────────────────────
elif tab == "🧩 记忆引擎":
    st.title("🧩 企业记忆引擎状态")

    st.markdown("""
    ### 四层记忆架构

    记忆引擎作为独立的 MCP (Model Context Protocol) Server 运行，Agent 每次对话时自动检索四层记忆：
    """)

    # 模拟记忆引擎状态
    memory_status = {
        "Memory Tree": {"count": 35, "status": "✅ 正常", "desc": "文档和数据的向量化索引"},
        "偏好记忆": {"count": 14, "status": "✅ 正常", "desc": "字段映射、会计周期等规则"},
        "纠错记忆": {"count": 6, "status": "✅ 正常", "desc": "历史纠正记录和正确做法"},
        "知识图谱": {"count": 34, "status": "✅ 正常", "desc": "实体关系：34个实体，29条关系"},
    }

    mem_cols = st.columns(4)
    for i, (name, info) in enumerate(memory_status.items()):
        with mem_cols[i]:
            st.metric(name, info["count"], info["status"])
            st.caption(info["desc"])

    st.divider()

    st.markdown("### 记忆示例：偏好记忆（企业规则已学习）")

    rules = [
        ("会计周期", "每月25日至下月25日", "财务政策"),
        ("研发支出", "全部费用化，不资本化", "会计处理"),
        ("电商推广费", "科目6601.03——最大费用项", "费用结构"),
        ("预付账款贷方", "重分类至应付账款", "报表调整"),
        ("收入算法", "max(借方,贷方)为实际发生额", "计算规则"),
        ("化妆品模式", "纯贸易/经销，无生产成本", "业务模式"),
    ]

    rule_df = pd.DataFrame(rules, columns=["规则类型", "具体内容", "分类"])
    st.dataframe(rule_df, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 知识图谱（部分实体关系）")

    graph_data = [
        ("化妆品公司", "包含", "21个部门"),
        ("销售培训部", "产生", "销售费用"),
        ("电商平台", "渠道", "推广费559万"),
        ("银行存款", "资金渠道", "净贷方1.4亿"),
        ("应付账款", "包含", "预付重分类"),
        ("本年利润", "关联", "利润表差异845万"),
    ]
    graph_df = pd.DataFrame(graph_data, columns=["实体A", "关系", "实体B"])
    st.dataframe(graph_df, use_container_width=True, hide_index=True)


# ── Tab 4: 报表中心 ─────────────────────────────────────
elif tab == "📊 报表中心":
    st.title("📊 财务报表中心")
    st.caption("一句话生成专业财务报表，支持导出和飞书推送")

    report_type = st.selectbox("报表类型", [
        "月度费用分析",
        "部门费用对比",
        "收入成本趋势",
        "核心科目变动",
    ])

    if st.button("📄 生成报表", type="primary"):
        with st.spinner("Agent 正在生成报表..."):
            if report_type == "月度费用分析":
                sql = PRESET_QUERIES["月度费用趋势"]
                df = run_query(sql)
                df['month_label'] = df['year'].astype(str) + '-' + df['period'].astype(str).str.zfill(2)

                fig = go.Figure()
                fig.add_trace(go.Bar(name='销售费用', x=df['month_label'], y=df['sales_expense']))
                fig.add_trace(go.Bar(name='管理费用', x=df['month_label'], y=df['admin_expense']))
                fig.add_trace(go.Bar(name='财务费用', x=df['month_label'], y=df['finance_expense']))
                fig.update_layout(barmode='stack', title='月度费用趋势（三大费用）',
                                template='plotly_dark', height=400)
                st.plotly_chart(fig, use_container_width=True)

                # 汇总指标
                total_sales = df['sales_expense'].sum()
                total_admin = df['admin_expense'].sum()
                total_fin = df['finance_expense'].sum()
                col1, col2, col3 = st.columns(3)
                col1.metric("销售费用合计", f"{total_sales/10000:.1f}万")
                col2.metric("管理费用合计", f"{total_admin/10000:.1f}万")
                col3.metric("财务费用合计", f"{total_fin/10000:.1f}万")

            elif report_type == "部门费用对比":
                df = run_query(PRESET_QUERIES["各部门费用排名"])
                fig = px.bar(df.head(15), x='total_expense', y='department', orientation='h',
                            title='各部门费用排名 TOP15', template='plotly_dark',
                            color='total_expense', color_continuous_scale='oranges')
                fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True, height=300)

            elif report_type == "收入成本趋势":
                df = run_query(PRESET_QUERIES["月度收入趋势"])
                fig = px.line(df, x='period', y='revenue', color='year',
                            title='收入趋势（分年度对比）', template='plotly_dark',
                            markers=True)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)

            elif report_type == "核心科目变动":
                df = run_query(PRESET_QUERIES["核心科目余额"])
                fig = px.bar(df.head(15), x='balance', y='account_name', orientation='h',
                            title='核心科目余额 TOP15', template='plotly_dark',
                            color='balance', color_continuous_scale='rdbu')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True)


# ── 页脚 ────────────────────────────────────────────────
st.divider()
st.caption("2026武汉AI智能体创新大赛 · 经开区\"经开智造\"分赛区 · 行业数字员工——企业记忆智能体")
