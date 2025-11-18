"""TODO 应用."""

from fastapi import APIRouter

from app.core.app_interface import JarvisApp
from app.apps.todo import api as todo_api


class TodoApp(JarvisApp):
    """TODO 应用."""

    @property
    def app_id(self) -> str:
        """应用唯一标识."""
        return "todo"

    @property
    def name(self) -> str:
        """应用名称."""
        return "TODO 四象限"

    @property
    def version(self) -> str:
        """应用版本."""
        return "1.0.0"

    @property
    def route_prefix(self) -> str:
        """路由前缀."""
        return ""

    def get_router(self) -> APIRouter:
        """获取应用的路由器."""
        return todo_api.router


# 应用实例
App = TodoApp

