"""应用接口定义."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from fastapi import APIRouter


class JarvisApp(ABC):
    """Jarvis 应用接口."""

    @property
    @abstractmethod
    def app_id(self) -> str:
        """应用唯一标识."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """应用名称."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """应用版本."""
        pass

    @property
    @abstractmethod
    def route_prefix(self) -> str:
        """路由前缀."""
        pass

    @abstractmethod
    def get_router(self) -> APIRouter:
        """
        获取应用的路由器.

        Returns:
            APIRouter: FastAPI 路由器
        """
        pass

    def get_config(self) -> dict[str, Any]:
        """
        获取应用配置.

        Returns:
            dict: 应用配置字典
        """
        return {}

    def on_start(self) -> None:
        """应用启动时的回调."""
        pass

    def on_stop(self) -> None:
        """应用停止时的回调."""
        pass

    def on_uninstall(self) -> None:
        """应用卸载时的回调."""
        pass

