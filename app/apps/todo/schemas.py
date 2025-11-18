"""TODO 应用的数据模型."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TodoTagBase(BaseModel):
    """标签基础模型."""

    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    color: Optional[str] = Field(None, max_length=20, description="标签颜色（十六进制）")


class TodoTagCreate(TodoTagBase):
    """创建标签的请求模型."""

    pass


class TodoTagUpdate(BaseModel):
    """更新标签的请求模型."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=20)


class TodoTagResponse(TodoTagBase):
    """标签响应模型."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic 配置."""

        from_attributes = True


class TodoPriorityBase(BaseModel):
    """优先级基础模型."""

    name: str = Field(..., min_length=1, max_length=50, description="优先级名称")
    level: int = Field(..., description="优先级级别（数字越小优先级越高）")
    color: Optional[str] = Field(None, max_length=20, description="优先级颜色（十六进制）")


class TodoPriorityCreate(TodoPriorityBase):
    """创建优先级的请求模型."""

    pass


class TodoPriorityUpdate(BaseModel):
    """更新优先级的请求模型."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    level: Optional[int] = None
    color: Optional[str] = Field(None, max_length=20)


class TodoPriorityResponse(TodoPriorityBase):
    """优先级响应模型."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic 配置."""

        from_attributes = True


class TodoItemBase(BaseModel):
    """TODO 项基础模型."""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: Optional[str] = Field(None, description="内容（支持 Markdown）")
    quadrant: str = Field(..., description="象限：reminder(提醒), record(记录), urgent(紧急), important(重要)")
    priority_id: Optional[int] = Field(None, description="优先级ID")
    due_time: Optional[datetime] = Field(None, description="截止时间")
    reminder_time: Optional[datetime] = Field(None, description="提醒时间")
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表")


class TodoItemCreate(TodoItemBase):
    """创建 TODO 项的请求模型."""

    pass


class TodoItemUpdate(BaseModel):
    """更新 TODO 项的请求模型."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    quadrant: Optional[str] = None
    priority_id: Optional[int] = None
    due_time: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
    is_archived: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class TodoItemResponse(TodoItemBase):
    """TODO 项响应模型."""

    id: int
    is_completed: bool
    is_archived: bool
    priority: Optional[TodoPriorityResponse] = None
    tags: List[TodoTagResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic 配置."""

        from_attributes = True

