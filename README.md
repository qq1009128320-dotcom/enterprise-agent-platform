# 行业数字员工——企业记忆智能体

> **让每家企业拥有一个懂自家业务数据、会学习、不遗忘的 AI 数字员工。**
> 参赛作品 — 2026武汉经开区"经开智造"AI智能体大赛 · 场景落地类赛道

[![Hermes Agent](https://img.shields.io/badge/Hermes%20Agent-FF6B35?style=flat)](https://hermes-agent.nousresearch.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![FAISS](https://img.shields.io/badge/FAISS-384dim-00C853?style=flat)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 一句话说清楚

**上传企业文档和数据 → Agent 自动理解、记住、对话分析 → 越用越聪明，不再犯同样的错。**

和普通 AI 问答的区别：**这个 Agent 有长期记忆。**

---

## 为什么企业需要

| 企业现状 | 有了记忆智能体之后 |
|---------|-------------------|
| 财务数据在 Excel 里沉睡，分析靠手工拉表 | 对话式查询："这个月费用最高部门？" 秒出结果 |
| 公司特殊做法靠老员工口口相传 | Agent 记住所有规则：会计周期 25 号到下月 25 号、研发全部费用化 |
| 每次问 AI 都像第一次见面，从头解释 | 纠正过一次，永久记住，下次直接用正确方式回答 |
| 报表制作耗时数天 | 一句话生成利润表、费用分析、驾驶舱大屏 |

---

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                 交互层                           │
│     Streamlit Web  │  微信/钉钉 机器人 @对话       │
├─────────────────────────────────────────────────┤
│              Agent 编排层 (Hermes)               │
│  对话管理 · 工具调度 · 技能路由 · 多轮上下文      │
├─────────────────────────────────────────────────┤
│                 技能层                           │
│  数据查询 · 报表生成 · 知识摄入 · 自动纠错       │
├─────────────────────────────────────────────────┤
│          企业记忆引擎 (MCP Server v2.2.0)        │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐  │
│  │Memory   │ │偏好记忆  │ │纠错记忆 │ │知识  │  │
│  │Tree     │ │字段映射  │ │历史错误 │ │图谱  │  │
│  │FAISS向量│ │会计周期  │ │正确做法 │ │实体  │  │
│  │检索     │ │命名习惯  │ │         │ │关系  │  │
│  └──────────┘ └──────────┘ └────────┘ └──────┘  │
│                                                  │
│         FAISS 向量库 + SQLite 结构化存储          │
│         嵌入模型: all-MiniLM-L6-v2 (384维)       │
└─────────────────────────────────────────────────┘
```

### 四层记忆架构（核心竞争力）

| 层级 | 做什么 | 例子 |
|------|--------|------|
| Memory Tree | 文档/数据向量化存储和语义检索 | 制度文件、会计分录自动切片入库 |
| 偏好记忆 | 记住企业的特殊规则和习惯 | "这个公司的会计周期是每月25号" |
| 纠错记忆 | 记录曾被纠正的错误+正确做法 | "预付账款贷方余额应重分类为应付" |
| 知识图谱 | 实体关系网络 | 张三是财务部 → 财务部属于化妆品公司 |

---

## 演示场景

平台包含6个演示场景，通过左侧边栏切换：

1. **💬 真实对话（自由提问）** — 核心功能，自然语言提问，Agent 自动处理
2. **🏠 系统架构总览** — 架构图、数据统计、四层记忆详解、部署方案
3. **🔍 Agent 对话式数据查询** — 分步演示5种典型查询（含实时数据 + 图表）
4. **🧩 记忆引擎如何工作** — 记忆检索流程展示 + 当前记忆状态
5. **📊 自动报表生成** — 一句话生成月度费用分析/部门排名/利润表/资金分布
6. **🔄 Agent 纠错与学习** — 演示纠正→记住→下次正确回答的闭环

---

## 快速开始

### 环境要求
- Python 3.10+
- Git

### 方式一：一键部署

```bash
# 1. 克隆本项目
git clone https://github.com/qq1009128320-dotcom/enterprise-agent-platform.git
cd enterprise-agent-platform

# 2. 一键部署（安装依赖 + 克隆记忆引擎）
bash setup.sh

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY

# 4. 启动记忆引擎 MCP Server（新终端）
cd memory-engine
python memory_server.py --port 8765

# 5. 启动演示面板（新终端）
cd ..
streamlit run demo/app.py --server.port 8501
```

### 方式二：Docker 部署

```bash
docker-compose up -d
# 访问 http://localhost:8501
```

### 访问方式
- 演示面板：http://localhost:8501
- 数据基于 301 万条真实企业会计分录

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Agent 框架 | Hermes Agent | 对话编排、工具调用、多技能调度 |
| 记忆引擎 | Enterprise Memory v2.2.0 | 独立 MCP Server，四层记忆架构 |
| 向量检索 | FAISS + all-MiniLM-L6-v2 | 384维嵌入，语义匹配，支持中文 |
| 演示界面 | Streamlit | 交互式数据对话和分析 |
| 企业协作 | 微信/钉钉 | 机器人集成、消息推送 |
| 数据存储 | SQLite | 零配置，百万行无压力 |

---

## 项目结构

```
enterprise-agent-platform/
├── README.md               # 项目说明
├── setup.sh                # 一键部署脚本
├── docker-compose.yml      # Docker 编排
├── .env.example            # 环境变量模板
├── demo/
│   ├── app.py              # Streamlit 演示面板（6个场景）
│   ├── hermes_bridge.py    # Hermes Agent 桥接服务
│   └── requirements.txt    # Python 依赖
├── config/
│   └── hermes_config.yaml  # Agent 配置示例
├── docs/
│   ├── architecture.html   # 详细技术架构说明
│   └── 项目说明_行业数字员工.pdf
└── scripts/
    └── demo_workflow.sh    # 演示流程脚本
```

---

## 相关仓库

- [企业记忆引擎 (memory-engine)](https://github.com/qq1009128320-dotcom/memory-engine) — 四层记忆 MCP Server
- [报表驾驶舱 (financial-statements)](https://github.com/qq1009128320-dotcom/financial-statements) — 财务分析大屏

---

## License

MIT
