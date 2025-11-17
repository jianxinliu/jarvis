#!/bin/bash

# Jarvis 启动脚本

echo "🚀 启动 Jarvis 私人助理..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 未找到 uv，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "❌ uv 安装失败，请手动安装: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

echo "✅ 使用 uv 管理依赖..."

# 使用 uv 同步依赖（会自动创建虚拟环境）
echo "📥 安装 Python 依赖..."
uv sync

# 启动后端
echo "🔙 启动后端服务..."
uv run python -m app.main &
BACKEND_PID=$!

# 检查 curl 是否安装
if ! command -v curl &> /dev/null; then
    echo "⚠️  未找到 curl，跳过健康检查（建议安装 curl 以确保后端正常启动）"
    sleep 5
else
    # 等待后端启动并检查状态
    echo "⏳ 等待后端服务启动..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    BACKEND_READY=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
            BACKEND_READY=true
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 1
    done

    if [ "$BACKEND_READY" = false ]; then
        echo "❌ 后端服务启动失败，请检查日志"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi

    echo "✅ 后端服务已启动"
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd frontend
    if ! npm install; then
        echo "❌ 前端依赖安装失败"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    cd ..
fi

# 检查 Node.js 是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装 Node.js"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 启动前端开发服务器
echo "🎨 启动前端开发服务器..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端启动
sleep 2

echo ""
echo "✅ Jarvis 已启动！"
echo "📱 前端地址: http://localhost:3000"
echo "🔌 后端 API: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    # 等待进程结束
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

# 注册清理函数
trap cleanup INT TERM

# 等待进程
wait

