# 代码结构说明

## 目录结构

### 后端结构

```
app/
├── api/                    # 核心 API（应用管理、提醒、WebSocket）
│   ├── apps.py            # 应用管理 API
│   ├── reminders.py       # 提醒 API
│   └── websocket.py       # WebSocket API
├── apps/                   # 应用目录（按功能模块化）
│   ├── excel/             # Excel 分析应用
│   │   ├── __init__.py
│   │   ├── app.py         # 应用定义
│   │   ├── api.py         # Excel API 路由
│   │   ├── service.py     # Excel 服务层
│   │   └── schemas.py     # Excel 数据模型
│   └── tasks/             # 任务管理应用
│       ├── __init__.py
│       ├── app.py         # 应用定义
│       ├── api.py         # Tasks API 路由
│       ├── service.py     # Tasks 服务层
│       └── schemas.py     # Tasks 数据模型
├── core/                   # 核心功能
│   ├── app_interface.py  # 应用接口定义
│   └── app_manager.py     # 应用管理器
├── services/               # 核心服务（跨应用）
│   ├── app_service.py     # 应用服务
│   ├── reminder_service.py # 提醒服务
│   └── notification_service.py # 通知服务
├── schemas.py              # 核心数据模型（应用管理、提醒等）
├── models.py               # 数据库模型
├── database.py             # 数据库配置
├── config.py               # 应用配置
├── scheduler.py            # 任务调度器
└── main.py                 # 应用入口
```

### 前端结构

```
frontend/src/
├── apps/                   # 应用目录（按功能模块化）
│   ├── excel/             # Excel 分析应用
│   │   ├── ExcelAnalyzer.tsx
│   │   └── ExcelAnalyzer.css
│   └── tasks/             # 任务管理应用
│       ├── TaskList.tsx
│       ├── TaskList.css
│       ├── TaskForm.tsx
│       ├── TaskForm.css
│       ├── ReminderPanel.tsx
│       └── ReminderPanel.css
├── components/             # 核心组件（启动台、应用视图等）
│   ├── Launcher.tsx       # 启动台
│   ├── AppView.tsx        # 应用视图容器
│   └── AppManager.tsx     # 应用管理
├── api.ts                  # API 客户端
├── types.ts                # 类型定义
└── App.tsx                 # 主应用组件
```

## 设计原则

### 1. 模块化
- 每个应用（app）拥有独立的目录
- 应用内部包含完整的业务逻辑：API、服务、数据模型
- 应用之间相互独立，便于维护和扩展

### 2. 职责分离
- **核心功能**（`app/api/`, `app/services/`）：跨应用共享的功能
- **应用功能**（`app/apps/`）：特定应用的业务逻辑
- **前端组件**：按应用组织，核心组件独立

### 3. 导入路径
- 应用内部：使用相对导入或 `app.apps.{app_name}.*`
- 跨应用：通过核心服务或 API
- 前端：使用 `../apps/{app_name}/` 导入应用组件

## 添加新应用

### 后端
1. 在 `app/apps/` 下创建新应用目录
2. 创建以下文件：
   - `app.py` - 应用定义（继承 `JarvisApp`）
   - `api.py` - API 路由
   - `service.py` - 服务层（可选）
   - `schemas.py` - 数据模型（可选）
3. 在 `app/main.py` 中注册应用

### 前端
1. 在 `frontend/src/apps/` 下创建新应用目录
2. 创建应用组件和样式文件
3. 在 `AppView.tsx` 中添加应用渲染逻辑

## 迁移说明

以下文件已从原位置移动到应用目录：

### Excel 应用
- `app/api/excel.py` → `app/apps/excel/api.py`
- `app/services/excel_service.py` → `app/apps/excel/service.py`
- Excel 相关 schemas → `app/apps/excel/schemas.py`
- `frontend/src/components/ExcelAnalyzer.*` → `frontend/src/apps/excel/`

### Tasks 应用
- `app/api/tasks.py` → `app/apps/tasks/api.py`
- `app/services/task_service.py` → `app/apps/tasks/service.py`
- Task 相关 schemas → `app/apps/tasks/schemas.py`
- `frontend/src/components/TaskList.*` → `frontend/src/apps/tasks/`
- `frontend/src/components/TaskForm.*` → `frontend/src/apps/tasks/`
- `frontend/src/components/ReminderPanel.*` → `frontend/src/apps/tasks/`

## 注意事项

1. **核心服务**：`reminder_service` 和 `notification_service` 保持独立，因为它们被多个应用使用
2. **数据模型**：核心模型（如 `AppResponse`）保留在 `app/schemas.py`，应用特定模型移动到各自目录
3. **导入更新**：所有导入路径已更新，确保使用新的模块路径

