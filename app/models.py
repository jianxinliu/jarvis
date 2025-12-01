"""数据库模型定义."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON, LargeBinary, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base

# TODO 应用的关联表
todo_item_tag = Table(
    "todo_item_tag",
    Base.metadata,
    Column("todo_item_id", Integer, ForeignKey("todo_items.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("todo_tags.id"), primary_key=True),
)


class Task(Base):
    """任务模型."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    content = Column(Text, nullable=True, comment="任务内容/提醒内容")
    priority = Column(Integer, default=1, nullable=False, comment="优先级 (1-最高, 数字越大优先级越低)")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    is_completed = Column(Boolean, default=False, nullable=False, comment="是否已完成")
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


class SubTask(Base):
    """子任务模型."""

    __tablename__ = "sub_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True, comment="关联的任务ID")
    title = Column(String(200), nullable=False, comment="子任务标题")
    reminder_time = Column(DateTime, nullable=False, comment="提醒时间（定时提醒）")
    is_completed = Column(Boolean, default=False, nullable=False, comment="是否已完成")
    is_notified = Column(Boolean, default=False, nullable=False, comment="是否已提醒")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        """返回子任务的字符串表示."""
        return f"<SubTask(id={self.id}, task_id={self.task_id}, title='{self.title}', reminder_time={self.reminder_time})>"


class ReminderLog(Base):
    """提醒记录模型."""

    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, nullable=False, index=True, comment="关联的任务ID")
    subtask_id = Column(Integer, nullable=True, index=True, comment="关联的子任务ID（如果是子任务提醒）")
    app_id = Column(String(100), nullable=True, index=True, comment="来源应用ID")
    reminder_type = Column(
        String(50), nullable=False, comment="提醒类型: interval(间隔提醒), daily(每日汇总), subtask(子任务提醒), todo(TODO提醒)"
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


class ExcelAnalysisRecord(Base):
    """Excel 分析记录模型."""

    __tablename__ = "excel_analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(500), nullable=False, comment="文件名")
    total_rows = Column(Integer, nullable=False, comment="总行数")
    matched_count = Column(Integer, nullable=False, comment="符合规则的数量")
    rule = Column(JSON, nullable=False, comment="使用的筛选规则")
    columns = Column(JSON, nullable=False, comment="Excel 列名列表")
    rule_fields = Column(JSON, nullable=True, comment="规则中使用的字段列表")
    days = Column(Integer, default=7, nullable=False, comment="查看近几日的均值")
    file_content = Column(LargeBinary, nullable=True, comment="原始文件内容（二进制）")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        """返回分析记录的字符串表示."""
        return f"<ExcelAnalysisRecord(id={self.id}, file_name='{self.file_name}', matched_count={self.matched_count})>"


class ExcelLinkHistory(Base):
    """Excel 链接历史记录模型."""

    __tablename__ = "excel_link_histories"

    id = Column(Integer, primary_key=True, index=True)
    analysis_record_id = Column(Integer, nullable=False, index=True, comment="关联的分析记录ID")
    link = Column(String(1000), nullable=False, index=True, comment="链接")
    ctr = Column(String(50), nullable=True, comment="CTR 值（字符串格式，保留原始精度）")
    revenue = Column(String(50), nullable=True, comment="收入值（字符串格式，保留原始精度）")
    data = Column(JSON, nullable=True, comment="其他数据")
    matched_groups = Column(JSON, nullable=True, comment="满足的规则组索引列表")
    matched_rules = Column(JSON, nullable=True, comment="满足的规则描述列表")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        """返回链接历史记录的字符串表示."""
        return f"<ExcelLinkHistory(id={self.id}, link='{self.link[:50]}...', record_id={self.analysis_record_id})>"


class TodoItem(Base):
    """TODO 项模型."""

    __tablename__ = "todo_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=True, comment="内容（支持 Markdown）")
    quadrant = Column(String(20), nullable=False, comment="象限：reminder(提醒), record(记录), urgent(紧急), important(重要)")
    priority_id = Column(Integer, ForeignKey("todo_priorities.id"), nullable=True, comment="优先级ID")
    due_time = Column(DateTime, nullable=True, comment="截止时间")
    reminder_time = Column(DateTime, nullable=True, comment="提醒时间")
    reminder_interval_hours = Column(
        Integer, nullable=True, comment="提醒间隔（小时），None 表示不设置间隔提醒"
    )
    next_reminder_time = Column(
        DateTime, nullable=True, comment="下次提醒时间，用于计算间隔提醒"
    )
    is_completed = Column(Boolean, default=False, nullable=False, comment="是否已完成")
    is_archived = Column(Boolean, default=False, nullable=False, comment="是否已归档")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关联关系
    priority = relationship("TodoPriority", back_populates="items")
    tags = relationship("TodoTag", secondary=todo_item_tag, back_populates="items")
    subtasks = relationship("TodoSubTask", back_populates="item", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """返回 TODO 项的字符串表示."""
        return f"<TodoItem(id={self.id}, title='{self.title}', quadrant='{self.quadrant}')>"


class TodoTag(Base):
    """TODO 标签模型."""

    __tablename__ = "todo_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="标签名称")
    color = Column(String(20), nullable=True, comment="标签颜色（十六进制）")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关联关系
    items = relationship("TodoItem", secondary=todo_item_tag, back_populates="tags")

    def __repr__(self) -> str:
        """返回标签的字符串表示."""
        return f"<TodoTag(id={self.id}, name='{self.name}')>"


class TodoPriority(Base):
    """TODO 优先级模型."""

    __tablename__ = "todo_priorities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="优先级名称")
    level = Column(Integer, nullable=False, comment="优先级级别（数字越小优先级越高）")
    color = Column(String(20), nullable=True, comment="优先级颜色（十六进制）")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关联关系
    items = relationship("TodoItem", back_populates="priority")

    def __repr__(self) -> str:
        """返回优先级的字符串表示."""
        return f"<TodoPriority(id={self.id}, name='{self.name}', level={self.level})>"


class TodoSubTask(Base):
    """TODO 子任务模型."""

    __tablename__ = "todo_sub_tasks"

    id = Column(Integer, primary_key=True, index=True)
    todo_item_id = Column(Integer, ForeignKey("todo_items.id"), nullable=False, index=True, comment="关联的 TODO 项ID")
    title = Column(String(200), nullable=False, comment="子任务标题")
    content = Column(Text, nullable=True, comment="子任务内容（支持 Markdown）")
    reminder_time = Column(DateTime, nullable=True, comment="提醒时间（定时提醒），None 表示不设置提醒")
    is_completed = Column(Boolean, default=False, nullable=False, comment="是否已完成")
    is_notified = Column(Boolean, default=False, nullable=False, comment="是否已提醒")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # 关联关系
    item = relationship("TodoItem", back_populates="subtasks")

    def __repr__(self) -> str:
        """返回子任务的字符串表示."""
        return f"<TodoSubTask(id={self.id}, todo_item_id={self.todo_item_id}, title='{self.title}', reminder_time={self.reminder_time})>"
