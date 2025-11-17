"""任务管理应用."""

from fastapi import APIRouter

from app.core.app_interface import JarvisApp
from app.apps.tasks import api as tasks_api


class TasksApp(JarvisApp):
    """任务管理应用."""

    @property
    def app_id(self) -> str:
        """应用唯一标识."""
        return "tasks"

    @property
    def name(self) -> str:
        """应用名称."""
        return "任务管理"

    @property
    def version(self) -> str:
        """应用版本."""
        return "1.0.0"

    @property
    def route_prefix(self) -> str:
        """路由前缀."""
        return ""  # 路由已经在 tasks_api.router 中定义了

    def get_router(self) -> APIRouter:
        """获取应用的路由器."""
        return tasks_api.router


# 应用实例
App = TasksApp

