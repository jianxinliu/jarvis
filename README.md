# Jarvis

操作系统式应用平台 - 支持插件化应用的私人助理系统

## 架构特点

Jarvis 采用类似操作系统的架构设计：

- **启动台**: 类似 macOS Launchpad，展示所有可用应用
- **应用系统**: 支持动态加载、卸载、启用/禁用应用
- **应用隔离**: 每个应用有独立的路由前缀和命名空间
- **插件化**: 支持开发自定义应用并动态安装

## 核心功能

### 应用管理

- **启动台**: 统一的应用入口，展示所有已安装的应用
- **应用管理**: 启用/禁用、重新加载、卸载应用
- **应用隔离**: 每个应用有独立的路由和配置
- **动态加载**: 支持运行时加载和卸载应用

### 内置应用

#### 1. 任务管理

管理持续性任务，并在特殊时间点给我提醒。

- **间隔提醒**: 支持设置一个任务，每隔 x 小时提醒一次，直到指定的结束时间
- **每日汇总**: 每天早上（默认 08:00）提醒今天需要处理的工作，按优先级排序（1,2,3...）
- **实时通知**: 通过 WebSocket 实时推送提醒消息
- **系统通知**: 支持 macOS 系统原生通知（使用 osascript）
- **任务管理**: 完整的任务 CRUD 功能，支持优先级、激活/暂停状态管理

#### 2. Excel 分析

上传 Excel 文件，根据规则筛选链接。

- **规则筛选**: 支持自定义筛选规则（CTR、收入等）
- **近日均值**: 自动计算近 N 日的均值
- **灵活配置**: 支持 AND/OR 逻辑组合多个条件

## 技术栈

### 后端

- **FastAPI**: 现代化的 Python Web 框架
- **SQLAlchemy**: ORM 数据库操作
- **APScheduler**: 定时任务调度
- **WebSocket**: 实时通信
- **uv**: 快速的 Python 包管理器
- **SQLite**: 默认数据库（可配置为 PostgreSQL）

### 前端

- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 快速构建工具
- **Axios**: HTTP 客户端

## 快速开始

### 1. 安装依赖

#### 安装 uv（如果未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 Homebrew (macOS)
brew install uv

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 后端依赖

```bash
# 使用 uv 安装依赖（会自动创建虚拟环境）
uv sync

# 或手动安装开发依赖
uv sync --extra dev
```

#### 前端依赖

```bash
cd frontend
npm install
cd ..
```

### 2. 启动应用

#### 方式一：使用启动脚本（推荐）

```bash
./run.sh
```

#### 方式二：手动启动

**启动后端：**

```bash
# 使用 uv 运行（推荐，自动使用虚拟环境）
uv run python -m app.main

# 或使用 uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 传统方式（需要先激活虚拟环境）
source .venv/bin/activate  # uv 创建的虚拟环境在 .venv 目录
python -m app.main
```

**启动前端：**

```bash
cd frontend
npm run dev
```

### 3. 访问应用

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 使用说明

### 创建任务

1. 点击"新建任务"按钮
2. 填写任务信息：
   - **任务标题**（必填）
   - **任务内容/提醒内容**（可选）
   - **优先级**（1-5，1 为最高优先级）
   - **提醒间隔**（小时，可选，设置后每隔指定时间提醒一次）
   - **结束时间**（可选，任务到期时间）

### 任务管理

- **查看任务**: 在"所有任务"标签页查看所有任务，在"今日任务"标签页查看今天需要处理的任务
- **编辑任务**: 点击任务卡片上的"编辑"按钮
- **暂停/激活**: 点击"暂停"或"激活"按钮控制任务状态
- **删除任务**: 点击"删除"按钮（会弹出确认对话框）

### 提醒功能

- **间隔提醒**: 如果任务设置了提醒间隔，系统会每隔指定时间自动提醒
- **每日汇总**: 每天早上 08:00（可在配置中修改）自动生成今日任务汇总
- **实时通知**: 新提醒会通过 WebSocket 实时推送到前端，并显示浏览器通知（需要授权）
- **系统通知**:
  - **macOS**: 使用系统原生通知，会在通知中心显示
  - **Linux**: 使用 `notify-send` 命令（需要安装 `libnotify-bin`）
  - **Windows**: 使用 `plyer` 库发送系统通知

### 提醒中心

右侧面板显示：

- **每日汇总**: 点击"展开"查看今天的任务汇总
- **未读提醒**: 显示所有未读的提醒记录，可以点击"标记已读"

## 配置

### 环境变量

创建 `.env` 文件（可选）：

```env
# 应用配置
APP_NAME=Jarvis
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./jarvis.db
# 或使用 PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/jarvis

# 提醒配置
MORNING_REMINDER_TIME=08:00

# 日志配置（默认关闭）
ENABLE_LOGGING=False  # 是否启用日志输出
ENABLE_SQL_ECHO=False  # 是否启用 SQL 输出
```

### 修改每日提醒时间

在 `app/config.py` 中修改 `morning_reminder_time` 参数，或通过环境变量 `MORNING_REMINDER_TIME` 设置。

## 项目结构

```
jarvis/
├── app/                    # 后端应用
│   ├── api/               # API 路由
│   │   ├── apps.py        # 应用管理 API
│   │   ├── tasks.py       # 任务相关 API
│   │   ├── reminders.py   # 提醒相关 API
│   │   ├── excel.py       # Excel 分析 API
│   │   └── websocket.py   # WebSocket 处理
│   ├── apps/              # 应用目录
│   │   ├── tasks/         # 任务管理应用
│   │   │   └── app.py     # 应用入口
│   │   └── excel/         # Excel 分析应用
│   │       └── app.py     # 应用入口
│   ├── core/              # 核心模块
│   │   ├── app_interface.py  # 应用接口定义
│   │   └── app_manager.py    # 应用管理器
│   ├── services/          # 业务逻辑层
│   │   ├── app_service.py
│   │   ├── task_service.py
│   │   ├── reminder_service.py
│   │   ├── excel_service.py
│   │   └── notification_service.py
│   ├── models.py          # 数据库模型
│   ├── schemas.py         # Pydantic 数据模型
│   ├── database.py        # 数据库连接
│   ├── config.py          # 配置管理
│   ├── scheduler.py       # 定时任务调度
│   └── main.py           # 应用入口
├── frontend/              # 前端应用
│   ├── src/
│   │   ├── components/   # React 组件
│   │   │   ├── Launcher.tsx      # 启动台
│   │   │   ├── AppView.tsx       # 应用视图
│   │   │   ├── AppManager.tsx    # 应用管理
│   │   │   ├── TaskList.tsx
│   │   │   ├── TaskForm.tsx
│   │   │   ├── ReminderPanel.tsx
│   │   │   └── ExcelAnalyzer.tsx
│   │   ├── hooks/        # 自定义 Hooks
│   │   ├── api.ts        # API 客户端
│   │   └── types.ts      # TypeScript 类型
│   └── package.json
├── pyproject.toml        # 项目配置（uv 格式）
├── uv.lock              # uv 锁定文件（自动生成）
└── README.md
```

## API 文档

启动后端后，访问 http://localhost:8000/docs 查看完整的 API 文档（Swagger UI）。

### 主要 API 端点

#### 应用管理

- `GET /api/apps` - 获取所有应用
- `GET /api/apps/{app_id}` - 获取应用信息
- `POST /api/apps` - 创建/注册应用
- `PUT /api/apps/{app_id}` - 更新应用
- `DELETE /api/apps/{app_id}` - 删除应用
- `POST /api/apps/{app_id}/toggle` - 启用/禁用应用
- `POST /api/apps/{app_id}/reload` - 重新加载应用

#### 任务管理

- `GET /api/tasks` - 获取所有任务
- `GET /api/tasks/today` - 获取今日任务
- `POST /api/tasks` - 创建任务
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

#### 提醒

- `GET /api/reminders` - 获取未读提醒
- `POST /api/reminders/{id}/read` - 标记提醒为已读
- `GET /api/reminders/daily-summary` - 获取每日汇总

#### Excel 分析

- `POST /api/excel/analyze` - 分析 Excel 文件
- `POST /api/excel/preview` - 预览 Excel 文件

#### 其他

- `WS /ws` - WebSocket 连接

## 开发

### 代码规范

- Python: 使用 `ruff` 进行代码格式化和检查
- TypeScript: 使用 ESLint 进行代码检查

### 依赖管理

项目使用 **uv** 进行依赖管理，这是 Astral 开发的快速 Python 包管理器。

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 运行命令
uv run python script.py

# 查看依赖
uv tree
```

### 运行测试

```bash
# 后端测试（待实现）
pytest

# 前端测试（待实现）
cd frontend
npm test
```

## 许可证

MIT License
