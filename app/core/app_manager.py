"""应用管理器."""

import importlib
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, FastAPI
from sqlalchemy.orm import Session

from app.core.app_interface import JarvisApp
from app.database import SessionLocal
from app.models import App

logger = logging.getLogger(__name__)


class AppManager:
    """应用管理器类."""

    def __init__(self, main_app: FastAPI) -> None:
        """
        初始化应用管理器.

        Args:
            main_app: FastAPI 主应用实例
        """
        self.main_app = main_app
        self.registered_apps: dict[str, JarvisApp] = {}
        self.app_routers: dict[str, APIRouter] = {}

    def register_app(self, app_instance: JarvisApp) -> bool:
        """
        注册应用实例.

        Args:
            app_instance: 应用实例

        Returns:
            bool: 是否成功注册
        """
        try:
            app_id = app_instance.app_id
            if app_id in self.registered_apps:
                logger.warning(f"应用 {app_id} 已注册，跳过")
                return False

            # 获取路由器
            router = app_instance.get_router()

            # 注册到主应用（使用应用的路由前缀）
            self.main_app.include_router(router, prefix=app_instance.route_prefix)

            # 保存引用
            self.registered_apps[app_id] = app_instance
            self.app_routers[app_id] = router

            # 调用启动回调
            app_instance.on_start()

            logger.info(f"应用 {app_id} ({app_instance.name}) 已注册")
            return True
        except Exception as e:
            logger.error(f"注册应用失败: {e}", exc_info=True)
            return False

    def unregister_app(self, app_id: str) -> bool:
        """
        卸载应用.

        Args:
            app_id: 应用ID

        Returns:
            bool: 是否成功卸载
        """
        if app_id not in self.registered_apps:
            logger.warning(f"应用 {app_id} 未注册")
            return False

        try:
            app_instance = self.registered_apps[app_id]

            # 调用卸载回调
            app_instance.on_uninstall()

            # 从主应用中移除路由
            router = self.app_routers.get(app_id)
            if router:
                # 注意：FastAPI 不支持动态移除路由，这里只做标记
                # 实际的路由移除需要在应用重启时生效
                pass

            # 移除引用
            del self.registered_apps[app_id]
            if app_id in self.app_routers:
                del self.app_routers[app_id]

            logger.info(f"应用 {app_id} 已卸载")
            return True
        except Exception as e:
            logger.error(f"卸载应用失败: {e}", exc_info=True)
            return False

    def get_app(self, app_id: str) -> Optional[JarvisApp]:
        """
        获取应用实例.

        Args:
            app_id: 应用ID

        Returns:
            Optional[JarvisApp]: 应用实例，如果不存在返回 None
        """
        return self.registered_apps.get(app_id)

    def list_apps(self) -> list[JarvisApp]:
        """
        列出所有已注册的应用.

        Returns:
            list[JarvisApp]: 应用实例列表
        """
        return list(self.registered_apps.values())

    def load_app_from_db(self, app_id: str) -> bool:
        """
        从数据库加载应用.

        Args:
            app_id: 应用ID

        Returns:
            bool: 是否成功加载
        """
        db: Session = SessionLocal()
        try:
            app_model = db.query(App).filter(App.app_id == app_id).first()
            if not app_model or not app_model.is_enabled:
                return False

            # 尝试动态加载应用模块
            # 应用模块应该在 app/apps/{app_id}/ 目录下
            apps_dir = Path("app/apps")
            app_dir = apps_dir / app_id

            if not app_dir.exists():
                logger.warning(f"应用目录不存在: {app_dir}")
                return False

            # 查找应用入口文件
            app_module_path = app_dir / "app.py"
            if not app_module_path.exists():
                logger.warning(f"应用入口文件不存在: {app_module_path}")
                return False

            # 动态导入应用模块
            module_name = f"app.apps.{app_id}.app"
            try:
                module = importlib.import_module(module_name)
                # 查找应用类（通常命名为 App 或 {AppId}App）
                app_class = getattr(module, "App", None)
                if app_class is None:
                    app_class = getattr(module, f"{app_id.capitalize()}App", None)

                if app_class is None:
                    logger.error(f"应用模块 {module_name} 中未找到应用类")
                    return False

                # 实例化应用
                app_instance = app_class()
                if not isinstance(app_instance, JarvisApp):
                    logger.error(f"应用类 {app_class} 未实现 JarvisApp 接口")
                    return False

                # 注册应用
                return self.register_app(app_instance)
            except ImportError as e:
                logger.error(f"导入应用模块失败: {e}", exc_info=True)
                return False
        finally:
            db.close()

    def load_all_apps_from_db(self) -> int:
        """
        从数据库加载所有启用的应用.

        Returns:
            int: 成功加载的应用数量
        """
        db: Session = SessionLocal()
        try:
            apps = db.query(App).filter(App.is_enabled == True).all()  # noqa: E712
            count = 0
            for app_model in apps:
                if self.load_app_from_db(app_model.app_id):
                    count += 1
            logger.info(f"从数据库加载了 {count}/{len(apps)} 个应用")
            return count
        finally:
            db.close()


# 全局应用管理器实例
app_manager: Optional[AppManager] = None


def get_app_manager() -> AppManager:
    """
    获取全局应用管理器实例.

    Returns:
        AppManager: 应用管理器实例

    Raises:
        RuntimeError: 如果应用管理器未初始化
    """
    if app_manager is None:
        raise RuntimeError("应用管理器未初始化，请先调用 init_app_manager")
    return app_manager


def init_app_manager(main_app: FastAPI) -> AppManager:
    """
    初始化全局应用管理器.

    Args:
        main_app: FastAPI 主应用实例

    Returns:
        AppManager: 应用管理器实例
    """
    global app_manager
    app_manager = AppManager(main_app)
    return app_manager

