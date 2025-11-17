# 应用开发指南

## 概述

Jarvis 支持开发自定义应用，每个应用都是独立的模块，可以动态加载和卸载。应用以 Tab 页的形式展示，多个应用可以同时打开，互不影响。

## 应用架构

### 后端结构

每个应用应该放在 `app/apps/{app_id}/` 目录下，包含以下文件：

```
app/apps/my_app/
├── app.py          # 应用入口文件（必需）
├── api.py          # API 路由（可选）
├── service.py      # 业务逻辑（可选）
├── schemas.py      # 数据模型（可选）
└── models.py       # 数据库模型（可选）
```

### 前端结构

前端应用组件放在 `frontend/src/apps/{app_id}/` 目录下：

```
frontend/src/apps/my_app/
├── MyAppComponent.tsx    # 主组件（必需）
└── MyAppComponent.css   # 样式文件（可选）
```

## 快速开始：5 步创建新应用

### 步骤 1: 创建后端应用类

在 `app/apps/my_app/app.py` 中创建应用类：

```python
"""我的应用."""

from fastapi import APIRouter

from app.core.app_interface import JarvisApp
from app.apps.my_app import api as my_app_api


class MyApp(JarvisApp):
    """我的应用."""

    @property
    def app_id(self) -> str:
        """应用唯一标识."""
        return "my_app"

    @property
    def name(self) -> str:
        """应用名称."""
        return "我的应用"

    @property
    def version(self) -> str:
        """应用版本."""
        return "1.0.0"

    @property
    def route_prefix(self) -> str:
        """路由前缀."""
        return ""  # 路由已经在 api.py 中定义了

    def get_router(self) -> APIRouter:
        """获取应用的路由器."""
        return my_app_api.router


# 应用实例
App = MyApp
```

### 步骤 2: 创建 API 路由

在 `app/apps/my_app/api.py` 中创建 API 路由：

```python
"""我的应用 API 路由."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/my_app", tags=["my_app"])


@router.get("/hello")
def hello():
    """示例接口."""
    return {"message": "Hello from my app"}
```

### 步骤 3: 创建前端组件

在 `frontend/src/apps/my_app/MyAppComponent.tsx` 中创建前端组件：

```typescript
import './MyAppComponent.css'

function MyAppComponent() {
  return (
    <div className="my-app">
      <h2>我的应用</h2>
      <p>这是应用的内容</p>
    </div>
  )
}

export default MyAppComponent
```

**重要**: 组件必须是**默认导出**（`export default`）。

### 步骤 4: 注册前端组件

在 `frontend/src/apps/registry.tsx` 中注册组件：

```typescript
const appComponents: Record<string, () => Promise<{ default: ComponentType<any> }>> = {
  excel: () => import('./excel/ExcelAnalyzer'),
  my_app: () => import('./my_app/MyAppComponent'),  // 添加这一行
}
```

### 步骤 5: 注册后端应用

在 `app/main.py` 的 `lifespan` 函数中注册应用：

```python
# 加载内置应用（直接注册）
try:
    from app.apps.my_app.app import App as MyApp
    app_manager.register_app(MyApp())
except Exception as e:
    logger.warning(f"加载内置应用 my_app 失败: {e}", exc_info=True)
```

或者在数据库中注册（通过 API 或管理界面）。

## 应用接口详解

所有应用必须实现 `JarvisApp` 接口：

```python
from app.core.app_interface import JarvisApp
from fastapi import APIRouter

class MyApp(JarvisApp):
    @property
    def app_id(self) -> str:
        """应用唯一标识，必须唯一."""
        return "my_app"

    @property
    def name(self) -> str:
        """应用显示名称."""
        return "我的应用"

    @property
    def version(self) -> str:
        """应用版本号."""
        return "1.0.0"

    @property
    def route_prefix(self) -> str:
        """API 路由前缀，通常返回空字符串（路由在 api.py 中定义）."""
        return ""

    def get_router(self) -> APIRouter:
        """返回应用的 FastAPI 路由器."""
        return my_app_api.router

    def get_config(self) -> dict[str, Any]:
        """可选：返回应用配置."""
        return {}

    def on_start(self) -> None:
        """可选：应用启动时的回调."""
        pass

    def on_stop(self) -> None:
        """可选：应用停止时的回调."""
        pass

    def on_uninstall(self) -> None:
        """可选：应用卸载时的回调."""
        pass
```

## 前端组件开发

### 组件要求

1. **默认导出**: 组件必须使用 `export default` 导出
2. **独立状态**: 每个 Tab 中的组件状态是独立的，互不影响
3. **样式隔离**: 建议使用 CSS Modules 或带前缀的类名

### 组件注册

在 `frontend/src/apps/registry.tsx` 中注册：

```typescript
import { lazy, ComponentType } from 'react'

const appComponents: Record<string, () => Promise<{ default: ComponentType<any> }>> = {
  excel: () => import('./excel/ExcelAnalyzer'),
  my_app: () => import('./my_app/MyAppComponent'),
}

// 使用 registerAppComponent 函数动态注册
import { registerAppComponent } from './registry'
registerAppComponent('my_app', () => import('./my_app/MyAppComponent'))
```

### 特殊应用处理

如果应用需要复杂的状态管理（如 tasks 应用），可以在 `AppView.tsx` 中特殊处理：

```typescript
// frontend/src/components/AppView.tsx
if (app.app_id === 'my_app') {
  // 特殊处理逻辑
  return <MyAppWithState />
}
```

## 多 Tab 支持

### Tab 特性

- **独立状态**: 每个 Tab 中的应用状态完全独立
- **持久化**: Tab 状态保存在 localStorage，刷新页面后恢复
- **URL 同步**: Tab 切换会同步更新 URL
- **关闭控制**: 可以单独关闭每个 Tab

### Tab 生命周期

1. **打开应用**: 从启动台点击应用，或直接访问 `/app/{app_id}`
2. **切换 Tab**: 点击 Tab 标签切换
3. **关闭 Tab**: 点击 Tab 上的 × 按钮
4. **全部关闭**: 关闭所有 Tab 后自动返回启动台

## 应用注册方式

### 方式一：内置应用（推荐）

在 `app/main.py` 的 `lifespan` 函数中直接注册：

```python
# 加载内置应用（直接注册）
try:
    from app.apps.my_app.app import App as MyApp
    app_manager.register_app(MyApp())
except Exception as e:
    logger.warning(f"加载内置应用 my_app 失败: {e}", exc_info=True)
```

### 方式二：通过 API 注册

```bash
POST /api/apps
Content-Type: application/json

{
  "app_id": "my_app",
  "name": "我的应用",
  "description": "应用描述",
  "icon": "📦",
  "version": "1.0.0",
  "route_prefix": "/api/my_app",
  "is_builtin": false,
  "is_enabled": true
}
```

### 方式三：通过管理界面

在 Jarvis 的管理界面中创建和启用应用。

## 应用隔离

每个应用有：

- **独立路由前缀**: 通过 `route_prefix` 定义
- **独立命名空间**: 通过 `app_id` 标识
- **独立配置**: 通过 `config` 字段存储
- **独立前端组件**: 通过注册表管理

## 示例应用

参考内置应用：

- **任务管理** (`app/apps/tasks/`): 复杂状态管理的示例
- **Excel 分析** (`app/apps/excel/`): 标准应用示例

## 最佳实践

1. **命名规范**: 
   - `app_id` 使用小写字母和下划线（如 `my_app`）
   - 组件文件名使用 PascalCase（如 `MyAppComponent.tsx`）

2. **路由设计**:
   - API 路由统一使用 `/api/{app_id}` 前缀
   - 在 `api.py` 中定义路由，而不是在 `app.py` 中

3. **组件设计**:
   - 保持组件独立，避免依赖其他应用的状态
   - 使用 TypeScript 类型定义
   - 合理使用懒加载

4. **错误处理**:
   - API 接口要有适当的错误处理
   - 前端组件要有加载和错误状态

5. **文档**:
   - 为应用编写 README
   - 注释关键逻辑

## 常见问题

### Q: 如何让应用在启动时自动加载？

A: 在 `app/main.py` 的 `lifespan` 函数中注册应用，或确保数据库中 `is_enabled=True`。

### Q: 前端组件如何调用后端 API？

A: 使用标准的 `fetch` 或 `axios`，API 路径为 `/api/{app_id}/...`。

### Q: 如何实现应用间的通信？

A: 可以通过 WebSocket、共享状态管理或事件总线实现。

### Q: Tab 状态会持久化吗？

A: 是的，Tab 状态保存在 localStorage，刷新页面后会自动恢复。

### Q: 如何调试应用？

A: 
- 后端：查看日志输出
- 前端：使用浏览器开发者工具
- API：使用 `/swagger/v1` 查看 API 文档

## 下一步

- 查看 [CODE_STRUCTURE.md](../CODE_STRUCTURE.md) 了解代码结构
- 查看 [QUICKSTART.md](../QUICKSTART.md) 了解快速开始
- 参考内置应用的实现
