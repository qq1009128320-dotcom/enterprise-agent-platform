#!/bin/bash
# 企业记忆智能体 — 一键部署脚本

set -e

echo "=========================================="
echo "  行业数字员工——企业记忆智能体 部署"
echo "=========================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.10+"
    exit 1
fi

echo "✅ Python: $(python3 --version)"

# 安装依赖
echo ""
echo "📦 安装依赖..."
pip install streamlit pandas plotly python-dotenv requests --quiet

# 克隆记忆引擎（如果不存在）- 指定 v2.2.0 标签
if [ ! -d "memory-engine" ]; then
    echo ""
    echo "📥 克隆企业记忆引擎 v2.2.0..."
    git clone --branch v2.2.0 https://github.com/qq1009128320-dotcom/memory-engine.git
    cd memory-engine
    pip install -r requirements.txt --quiet
    cd ..
fi

echo ""
echo "=========================================="
echo "  部署完成！"
echo "  启动演示：streamlit run demo/app.py"
echo "  记忆引擎通过 MCP 连接（端口 8765）"
echo "=========================================="
