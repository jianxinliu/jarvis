"""任务管理相关的数据模型."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    """任务基础模型."""

    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    content: Optional[str] = Field(None, description="任务内容/提醒内容")
    priority: int = Field(1, ge=1, description="优先级 (1-最高, 数字越大优先级越低)")
    reminder_interval_hours: Optional[int] = Field(
        None, ge=1, description="提醒间隔（小时），None 表示不设置间隔提醒"
    )
    end_time: Optional[datetime] = Field(None, description="任务结束时间")


class TaskCreate(TaskBase):
    """创建任务的请求模型."""

    pass


class TaskUpdate(BaseModel):
    """更新任务的请求模型."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    reminder_interval_hours: Optional[int] = Field(None, ge=1)
    end_time: Optional[datetime] = None

    @field_validator("reminder_interval_hours")
    @classmethod
    def validate_reminder_interval(cls, v: Optional[int]) -> Optional[int]:
        """验证提醒间隔."""
        if v is not None and v < 1:
            raise ValueError("提醒间隔必须大于等于 1 小时")
        return v


class TaskResponse(TaskBase):
    """任务响应模型."""

    id: int
    is_active: bool
    next_reminder_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic 配置."""

        from_attributes = True

