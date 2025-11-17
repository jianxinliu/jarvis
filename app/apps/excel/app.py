"""Excel 分析应用."""

from fastapi import APIRouter

from app.core.app_interface import JarvisApp
from app.apps.excel import api as excel_api


class ExcelApp(JarvisApp):
    """Excel 分析应用."""

    @property
    def app_id(self) -> str:
        """应用唯一标识."""
        return "excel"

    @property
    def name(self) -> str:
        """应用名称."""
        return "Excel 分析"

    @property
    def version(self) -> str:
        """应用版本."""
        return "1.0.0"

    @property
    def route_prefix(self) -> str:
        """路由前缀."""
        return ""  # 路由已经在 excel_api.router 中定义了

    def get_router(self) -> APIRouter:
        """获取应用的路由器."""
        return excel_api.router


# 应用实例
App = ExcelApp

