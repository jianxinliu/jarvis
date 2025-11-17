# Jarvis 架构说明

## 多 Tab 架构

Jarvis 现在支持多应用 Tab 模式，多个应用可以同时打开，互不影响。

### 核心组件

1. **TabContainer** (`frontend/src/components/TabContainer.tsx`)
   - 管理多个应用 Tab
   - 处理 Tab 的打开、关闭、切换
   - 持久化 Tab 状态到 localStorage
   - 同步 URL 状态

2. **AppView** (`frontend/src/components/AppView.tsx`)
   - 渲染单个应用的内容
   - 支持 Tab 模式和独立模式
   - 通过应用注册表加载组件

3. **应用注册表** (`frontend/src/apps/registry.tsx`)
   - 管理前端应用组件的注册
   - 支持懒加载
   - 提供组件发现和加载接口

### Tab 特性

- ✅ **独立状态**: 每个 Tab 中的应用状态完全独立
- ✅ **持久化**: Tab 状态保存在 localStorage，刷新后恢复
- ✅ **URL 同步**: Tab 切换会同步更新 URL
- ✅ **智能关闭**: 关闭 Tab 时自动切换到相邻 Tab

## 应用注册机制

### 后端注册

应用通过 `AppManager` 注册到 FastAPI：

```python
from app.core.app_manager import get_app_manager

app_manager = get_app_manager()
app_manager.register_app(MyApp())
```

### 前端注册

应用组件在 `frontend/src/apps/registry.tsx` 中注册：

```typescript
const appComponents = {
  excel: () => import('./excel/ExcelAnalyzer'),
  my_app: () => import('./my_app/MyAppComponent'),
}
```

## 应用开发流程

1. **创建后端应用类** (`app/apps/{app_id}/app.py`)
2. **创建 API 路由** (`app/apps/{app_id}/api.py`)
3. **创建前端组件** (`frontend/src/apps/{app_id}/Component.tsx`)
4. **注册前端组件** (`frontend/src/apps/registry.tsx`)
5. **注册后端应用** (`app/main.py` 或通过 API)

详细步骤请参考 [APP_DEVELOPMENT.md](./APP_DEVELOPMENT.md)。

## 目录结构

```
jarvis/
├── app/
│   ├── apps/                    # 应用目录
│   │   ├── excel/               # Excel 分析应用
│   │   └── tasks/               # 任务管理应用
│   ├── core/
│   │   ├── app_interface.py     # 应用接口定义
│   │   └── app_manager.py      # 应用管理器
│   └── main.py                  # 主应用入口
├── frontend/
│   └── src/
│       ├── apps/                # 前端应用组件
│       │   ├── excel/
│       │   ├── tasks/
│       │   └── registry.tsx     # 应用组件注册表
│       └── components/
│           ├── TabContainer.tsx # Tab 容器
│           └── AppView.tsx      # 应用视图
└── docs/
    ├── APP_DEVELOPMENT.md       # 应用开发指南
    └── ARCHITECTURE.md          # 架构说明（本文档）
```

## 数据流

### 应用启动流程

```
用户点击应用
  ↓
Launcher 调用 handleLaunchApp
  ↓
TabContainer 接收请求
  ↓
从 API 获取应用信息 (/api/apps/{app_id})
  ↓
创建新 Tab
  ↓
AppView 渲染应用
  ↓
从注册表加载组件
  ↓
显示应用界面
```

### Tab 状态管理

```
TabContainer (状态管理)
  ├── tabs: Tab[]              # Tab 列表
  ├── activeTabId: string      # 当前激活的 Tab
  └── localStorage             # 持久化存储
```

## 扩展性

### 新增应用

只需 5 步即可添加新应用：

1. 创建后端应用类
2. 创建 API 路由
3. 创建前端组件
4. 注册前端组件
5. 注册后端应用

详细步骤请参考 [APP_DEVELOPMENT.md](./APP_DEVELOPMENT.md)。

### 应用隔离

- 每个应用有独立的路由前缀
- 每个应用有独立的命名空间
- 每个应用有独立的配置
- 每个 Tab 中的应用状态完全独立

## 技术栈

- **后端**: FastAPI, SQLAlchemy, Python 3.10+
- **前端**: React, TypeScript, Vite
- **状态管理**: React Hooks, localStorage
- **路由**: React Router (通过 URL 状态)

## 未来改进

- [ ] Tab 拖拽排序
- [ ] Tab 分组
- [ ] 应用间通信机制
- [ ] 应用市场/插件系统
- [ ] 应用权限管理

