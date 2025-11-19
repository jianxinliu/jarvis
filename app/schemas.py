"""Pydantic 数据模型定义."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator


# Task 相关模型已移动到 app.apps.tasks.schemas

class ReminderLogResponse(BaseModel):
    """提醒记录响应模型."""

    id: int
    task_id: int
    reminder_type: str
    reminder_time: datetime
    is_read: bool
    content: Optional[str]
    app_id: Optional[str] = None

    class Config:
        """Pydantic 配置."""

        from_attributes = True


class DailySummaryResponse(BaseModel):
    """每日汇总响应模型."""

    date: str
    tasks: list[Any]  # TaskResponse 已移动到 app.apps.tasks.schemas
    total_count: int


# Excel 分析相关模型已移动到 app.apps.excel.schemas
# Task 相关模型已移动到 app.apps.tasks.schemas

# 应用管理相关模型
class AppBase(BaseModel):
    """应用基础模型."""

    app_id: str = Field(..., min_length=1, max_length=100, description="应用唯一标识")
    name: str = Field(..., min_length=1, max_length=200, description="应用名称")
    description: Optional[str] = Field(None, description="应用描述")
    icon: Optional[str] = Field(None, description="应用图标URL或路径")
    version: str = Field("1.0.0", description="应用版本")
    author: Optional[str] = Field(None, description="作者")
    route_prefix: str = Field(..., description="路由前缀")
    frontend_path: Optional[str] = Field(None, description="前端路径")
    config: Optional[dict[str, Any]] = Field(None, description="应用配置")


class AppCreate(AppBase):
    """创建应用的请求模型."""

    pass


class AppUpdate(BaseModel):
    """更新应用的请求模型."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    route_prefix: Optional[str] = None
    frontend_path: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class AppResponse(AppBase):
    """应用响应模型."""

    id: int
    is_enabled: bool
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic 配置."""

        from_attributes = True
