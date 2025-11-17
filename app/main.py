"""FastAPI 应用主入口."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api import apps, reminders, websocket
from app.config import settings
from app.core.app_manager import init_app_manager
from app.database import Base, engine, SessionLocal
from app.models import App
from app.scheduler import scheduler

# 配置日志（根据配置决定是否启用）
if settings.enable_logging:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
else:
    # 禁用所有日志输出
    logging.basicConfig(level=logging.CRITICAL + 1)

logger = logging.getLogger(__name__)


def init_builtin_apps(db: Session) -> None:
    """
    初始化内置应用.

    Args:
        db: 数据库会话
    """
    builtin_apps = [
        {
            "app_id": "tasks",
            "name": "任务管理",
            "description": "管理持续性任务，并在特殊时间点提醒",
            "icon": "📋",
            "version": "1.0.0",
            "route_prefix": "/api/tasks",
            "frontend_path": None,
            "is_builtin": True,
            "is_enabled": True,
        },
        {
            "app_id": "excel",
            "name": "Excel 分析",
            "description": "上传 Excel 文件，根据规则筛选链接",
            "icon": "📊",
            "version": "1.0.0",
            "route_prefix": "/api/excel",
            "frontend_path": None,
            "is_builtin": True,
            "is_enabled": True,
        },
    ]

    for app_data in builtin_apps:
        existing = db.query(App).filter(App.app_id == app_data["app_id"]).first()
        if not existing:
            app = App(**app_data)
            db.add(app)
            logger.info(f"创建内置应用: {app_data['app_id']}")

    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理.

    Args:
        app: FastAPI 应用实例
    """
    # 启动时执行
    # 初始化应用管理器
    app_manager = init_app_manager(app)

    # 初始化内置应用
    db: Session = SessionLocal()
    try:
        init_builtin_apps(db)
    finally:
        db.close()

    # 加载内置应用（直接注册）
    try:
        from app.apps.tasks.app import App as TasksApp
        app_manager.register_app(TasksApp())
    except Exception as e:
        logger.warning(f"加载内置应用 tasks 失败: {e}", exc_info=True)

    try:
        from app.apps.excel.app import App as ExcelApp
        app_manager.register_app(ExcelApp())
    except Exception as e:
        logger.warning(f"加载内置应用 excel 失败: {e}", exc_info=True)

    # 加载其他启用的应用（从数据库）
    app_manager.load_all_apps_from_db()

    # 启动调度器
    scheduler.start(settings.morning_reminder_time)

    yield

    # 关闭时执行
    scheduler.stop()


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    description="Jarvis - 操作系统式应用平台",
    version="0.2.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册核心路由（应用管理、提醒、WebSocket）
app.include_router(apps.router)
app.include_router(reminders.router)
app.include_router(websocket.router)

# 挂载静态文件（前端构建后的文件）
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
except RuntimeError:
    # 如果前端目录不存在，忽略错误
    pass


@app.get("/api/health")
def health_check() -> dict:
    """
    健康检查接口.

    Returns:
        dict: 健康状态
    """
    return {"status": "ok", "app": settings.app_name}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

