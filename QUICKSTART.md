# 快速启动指南

## 一键启动（推荐）

```bash
./run.sh
```

脚本会自动：
1. 检查并安装 uv（如果未安装）
2. 使用 uv 安装后端依赖
3. 安装前端依赖（如果不存在）
4. 启动后端服务（端口 8000）
5. 启动前端开发服务器（端口 3000）

## 手动启动

### 步骤 1: 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv
```

### 步骤 2: 安装后端依赖

```bash
# uv 会自动创建虚拟环境并安装依赖
uv sync
```

### 步骤 3: 安装前端依赖

```bash
cd frontend
yarn install
cd ..
```

### 步骤 4: 启动后端

```bash
# 使用 uv 运行（推荐）
uv run python -m app.main

# 或使用 uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 步骤 5: 启动前端（新终端）

```bash
cd frontend
yarn dev
```

## 访问应用

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 首次使用

1. 打开浏览器访问 http://localhost:3000
2. 点击"新建任务"创建你的第一个任务
3. 设置提醒间隔（例如：每 2 小时提醒一次）
4. 设置结束时间（例如：3 天后）
5. 系统会自动在指定时间提醒你

## macOS 系统通知

在 macOS 上，提醒会通过系统原生通知显示：
- 通知会出现在屏幕右上角
- 可以在通知中心查看历史通知
- 支持通知声音（可在系统设置中配置）

**注意**: 首次运行时，macOS 可能会请求通知权限，请允许以便接收提醒。

## 注意事项

- 确保端口 8000 和 3000 未被占用
- 首次运行会自动创建 SQLite 数据库文件 `jarvis.db`
- 浏览器会请求通知权限，请允许以便接收提醒通知
- uv 会自动管理虚拟环境，无需手动创建
