"""数据库模型定义."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.sql import func

from app.database import Base


class Task(Base):
    """任务模型."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    content = Column(Text, nullable=True, comment="任务内容/提醒内容")
    priority = Column(Integer, default=1, nullable=False, comment="优先级 (1-最高, 数字越大优先级越低)")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    reminder_interval_hours = Column(
        Integer, nullable=True, comment="提醒间隔（小时），None 表示不设置间隔提醒"
    )
    end_time = Column(DateTime, nullable=True, comment="任务结束时间，None 表示无结束时间")
    next_reminder_time = Column(
        DateTime, nullable=True, comment="下次提醒时间，用于计算间隔提醒"
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """返回任务的字符串表示."""
        return f"<Task(id={self.id}, title='{self.title}', priority={self.priority})>"


class ReminderLog(Base):
    """提醒记录模型."""

    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True, comment="关联的任务ID")
    reminder_type = Column(
        String(50), nullable=False, comment="提醒类型: interval(间隔提醒) 或 daily(每日汇总)"
    )
    reminder_time = Column(DateTime, server_default=func.now(), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, comment="是否已读")
    content = Column(Text, nullable=True, comment="提醒内容")

    def __repr__(self) -> str:
        """返回提醒记录的字符串表示."""
        return (
            f"<ReminderLog(id={self.id}, task_id={self.task_id}, "
            f"type='{self.reminder_type}', is_read={self.is_read})>"
        )


class App(Base):
    """应用模型."""

    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(String(100), unique=True, nullable=False, index=True, comment="应用唯一标识")
    name = Column(String(200), nullable=False, comment="应用名称")
    description = Column(Text, nullable=True, comment="应用描述")
    icon = Column(String(500), nullable=True, comment="应用图标URL或路径")
    version = Column(String(50), nullable=False, default="1.0.0", comment="应用版本")
    author = Column(String(200), nullable=True, comment="作者")
    
    # 路由配置
    route_prefix = Column(String(100), nullable=False, comment="路由前缀，如 /app/tasks")
    frontend_path = Column(String(500), nullable=True, comment="前端路径，相对于 apps/ 目录")
    
    # 应用配置
    config = Column(JSON, nullable=True, comment="应用配置（JSON格式）")
    
    # 状态
    is_enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    is_builtin = Column(Boolean, default=False, nullable=False, comment="是否内置应用")
    
    # 元数据
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """返回应用的字符串表示."""
        return f"<App(id={self.id}, app_id='{self.app_id}', name='{self.name}')>"
