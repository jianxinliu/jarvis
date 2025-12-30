"""TODO 服务层."""

from datetime import timedelta
from typing import Optional, List

from sqlalchemy.orm import Session, joinedload

from app.models import TodoItem, TodoTag, TodoPriority, TodoSubTask
from app.utils.timezone import now


class TodoService:
    """TODO 服务类."""

    @staticmethod
    def create_item(db: Session, item_data: dict) -> TodoItem:
        """
        创建 TODO 项.

        Args:
            db: 数据库会话
            item_data: TODO 项数据字典

        Returns:
            TodoItem: 创建的 TODO 项对象
        """
        tag_ids = item_data.pop("tag_ids", None) or []
        subtasks_data = item_data.pop("subtasks", None) or []
        
        # 如果有提醒间隔，计算下次提醒时间
        next_reminder_time = None
        if item_data.get("reminder_interval_hours"):
            next_reminder_time = now() + timedelta(
                hours=item_data["reminder_interval_hours"]
            )
        
        item = TodoItem(
            title=item_data["title"],
            content=item_data.get("content"),
            quadrant=item_data["quadrant"],
            priority_id=item_data.get("priority_id"),
            due_time=item_data.get("due_time"),
            reminder_time=item_data.get("reminder_time"),
            reminder_interval_hours=item_data.get("reminder_interval_hours"),
            next_reminder_time=next_reminder_time,
        )
        
        # 添加标签
        if tag_ids:
            tags = db.query(TodoTag).filter(TodoTag.id.in_(tag_ids)).all()
            item.tags = tags
        
        db.add(item)
        db.flush()  # 获取 item.id
        
        # 创建子任务
        for subtask_data in subtasks_data:
            subtask = TodoSubTask(
                todo_item_id=item.id,
                title=subtask_data["title"],
                content=subtask_data.get("content"),
                reminder_time=subtask_data["reminder_time"],
            )
            db.add(subtask)
        
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_item(db: Session, item_id: int) -> Optional[TodoItem]:
        """
        根据 ID 获取 TODO 项.

        Args:
            db: 数据库会话
            item_id: TODO 项ID

        Returns:
            Optional[TodoItem]: TODO 项对象，如果不存在返回 None
        """
        return (
            db.query(TodoItem)
            .options(joinedload(TodoItem.subtasks))
            .filter(TodoItem.id == item_id)
            .first()
        )

    @staticmethod
    def get_items_by_quadrant(
        db: Session, quadrant: str, include_archived: bool = False
    ) -> List[TodoItem]:
        """
        根据象限获取 TODO 项.

        Args:
            db: 数据库会话
            quadrant: 象限名称
            include_archived: 是否包含已归档的项

        Returns:
            List[TodoItem]: TODO 项列表
        """
        query = db.query(TodoItem).options(joinedload(TodoItem.subtasks)).filter(TodoItem.quadrant == quadrant)
        if not include_archived:
            query = query.filter(TodoItem.is_archived == False)  # noqa: E712
        return query.order_by(TodoItem.created_at.desc()).all()

    @staticmethod
    def get_all_items(
        db: Session, include_archived: bool = False, include_completed: bool = True
    ) -> List[TodoItem]:
        """
        获取所有 TODO 项.

        Args:
            db: 数据库会话
            include_archived: 是否包含已归档的项
            include_completed: 是否包含已完成的项

        Returns:
            List[TodoItem]: TODO 项列表，按象限和优先级排序
        """
        query = db.query(TodoItem).options(joinedload(TodoItem.subtasks))
        if not include_archived:
            query = query.filter(TodoItem.is_archived == False)  # noqa: E712
        if not include_completed:
            query = query.filter(TodoItem.is_completed == False)  # noqa: E712
        # 排序：象限 > 优先级 > 创建时间
        return query.order_by(
            TodoItem.quadrant.asc(),
            TodoItem.priority_id.asc().nulls_last(),
            TodoItem.created_at.desc()
        ).all()

    @staticmethod
    def get_today_todos(db: Session) -> List[TodoItem]:
        """
        获取今天要做的事情（未完成、未归档的 TODO 项）.

        Args:
            db: 数据库会话

        Returns:
            List[TodoItem]: 今天要做的 TODO 项列表
        """
        # 获取未完成、未归档的 TODO 项
        query = (
            db.query(TodoItem)
            .filter(TodoItem.is_completed == False)  # noqa: E712
            .filter(TodoItem.is_archived == False)  # noqa: E712
        )
        
        # 按象限和优先级排序
        items = query.order_by(
            TodoItem.quadrant.asc(),
            TodoItem.priority_id.asc(),
            TodoItem.due_time.asc().nulls_last(),
            TodoItem.created_at.asc()
        ).all()
        
        return items

    @staticmethod
    def update_item(db: Session, item_id: int, item_data: dict) -> Optional[TodoItem]:
        """
        更新 TODO 项.

        Args:
            db: 数据库会话
            item_id: TODO 项ID
            item_data: 要更新的数据字典

        Returns:
            Optional[TodoItem]: 更新后的 TODO 项对象，如果不存在返回 None
        """
        item = db.query(TodoItem).filter(TodoItem.id == item_id).first()
        if not item:
            return None

        # 处理子任务更新
        if "subtasks" in item_data:
            subtasks_data = item_data.pop("subtasks")
            # 删除旧的子任务
            db.query(TodoSubTask).filter(TodoSubTask.todo_item_id == item_id).delete()
            # 创建新的子任务
            if subtasks_data:
                for subtask_data in subtasks_data:
                    subtask = TodoSubTask(
                        todo_item_id=item.id,
                        title=subtask_data["title"],
                        content=subtask_data.get("content"),
                        reminder_time=subtask_data["reminder_time"],
                    )
                    db.add(subtask)

        # 处理标签更新
        if "tag_ids" in item_data:
            tag_ids = item_data.pop("tag_ids")
            if tag_ids is not None:
                tags = db.query(TodoTag).filter(TodoTag.id.in_(tag_ids)).all()
                item.tags = tags

        # 如果更新了提醒间隔，重新计算下次提醒时间
        if "reminder_interval_hours" in item_data and item_data["reminder_interval_hours"]:
            item.next_reminder_time = now() + timedelta(
                hours=item_data["reminder_interval_hours"]
            )
        elif "reminder_interval_hours" in item_data and item_data["reminder_interval_hours"] is None:
            item.next_reminder_time = None

        # 更新其他字段
        for key, value in item_data.items():
            if value is not None:
                setattr(item, key, value)

        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_item(db: Session, item_id: int) -> bool:
        """
        删除 TODO 项.

        Args:
            db: 数据库会话
            item_id: TODO 项ID

        Returns:
            bool: 是否成功删除
        """
        item = db.query(TodoItem).filter(TodoItem.id == item_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    # 标签管理
    @staticmethod
    def create_tag(db: Session, tag_data: dict) -> TodoTag:
        """创建标签."""
        tag = TodoTag(**tag_data)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def get_all_tags(db: Session) -> List[TodoTag]:
        """获取所有标签."""
        return db.query(TodoTag).order_by(TodoTag.name.asc()).all()

    @staticmethod
    def update_tag(db: Session, tag_id: int, tag_data: dict) -> Optional[TodoTag]:
        """更新标签."""
        tag = db.query(TodoTag).filter(TodoTag.id == tag_id).first()
        if not tag:
            return None
        for key, value in tag_data.items():
            if value is not None:
                setattr(tag, key, value)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def delete_tag(db: Session, tag_id: int) -> bool:
        """删除标签."""
        tag = db.query(TodoTag).filter(TodoTag.id == tag_id).first()
        if not tag:
            return False
        db.delete(tag)
        db.commit()
        return True

    # 优先级管理
    @staticmethod
    def create_priority(db: Session, priority_data: dict) -> TodoPriority:
        """创建优先级."""
        priority = TodoPriority(**priority_data)
        db.add(priority)
        db.commit()
        db.refresh(priority)
        return priority

    @staticmethod
    def get_all_priorities(db: Session) -> List[TodoPriority]:
        """获取所有优先级."""
        return db.query(TodoPriority).order_by(TodoPriority.level.asc()).all()

    @staticmethod
    def update_priority(db: Session, priority_id: int, priority_data: dict) -> Optional[TodoPriority]:
        """更新优先级."""
        priority = db.query(TodoPriority).filter(TodoPriority.id == priority_id).first()
        if not priority:
            return None
        for key, value in priority_data.items():
            if value is not None:
                setattr(priority, key, value)
        db.commit()
        db.refresh(priority)
        return priority

    @staticmethod
    def delete_priority(db: Session, priority_id: int) -> bool:
        """删除优先级."""
        priority = db.query(TodoPriority).filter(TodoPriority.id == priority_id).first()
        if not priority:
            return False
        db.delete(priority)
        db.commit()
        return True

    # 子任务管理
    @staticmethod
    def get_subtasks_by_item_id(db: Session, item_id: int) -> List[TodoSubTask]:
        """
        获取 TODO 项的所有子任务.

        Args:
            db: 数据库会话
            item_id: TODO 项ID

        Returns:
            List[TodoSubTask]: 子任务列表
        """
        return db.query(TodoSubTask).filter(TodoSubTask.todo_item_id == item_id).order_by(TodoSubTask.reminder_time.asc()).all()

    @staticmethod
    def get_subtasks_for_reminder(db: Session) -> List[TodoSubTask]:
        """
        获取需要提醒的子任务（定时提醒）.

        Args:
            db: 数据库会话

        Returns:
            List[TodoSubTask]: 需要提醒的子任务列表
        """
        current_time = now()
        # 使用 select_from 明确指定左表，避免 SQLAlchemy 2.0 的歧义
        return (
            db.query(TodoSubTask)
            .select_from(TodoSubTask)
            .join(TodoItem, TodoSubTask.item_id == TodoItem.id)
            .filter(TodoItem.is_completed == False)  # noqa: E712
            .filter(TodoItem.is_archived == False)  # noqa: E712
            .filter(TodoSubTask.is_completed == False)  # noqa: E712
            .filter(TodoSubTask.is_notified == False)  # noqa: E712
            .filter(TodoSubTask.reminder_time.isnot(None))  # 只获取设置了提醒时间的子任务
            .filter(TodoSubTask.reminder_time <= current_time)
            .all()
        )

    @staticmethod
    def mark_subtask_as_notified(db: Session, subtask_id: int) -> bool:
        """
        标记子任务为已提醒.

        Args:
            db: 数据库会话
            subtask_id: 子任务ID

        Returns:
            bool: 是否成功标记
        """
        subtask = db.query(TodoSubTask).filter(TodoSubTask.id == subtask_id).first()
        if not subtask:
            return False
        subtask.is_notified = True
        db.commit()
        return True

    @staticmethod
    def get_items_for_interval_reminder(db: Session) -> List[TodoItem]:
        """
        获取需要执行间隔提醒的 TODO 项.

        Args:
            db: 数据库会话

        Returns:
            List[TodoItem]: 需要提醒的 TODO 项列表
        """
        current_time = now()
        return (
            db.query(TodoItem)
            .filter(TodoItem.is_completed == False)  # noqa: E712
            .filter(TodoItem.is_archived == False)  # noqa: E712
            .filter(TodoItem.reminder_interval_hours.isnot(None))
            .filter(TodoItem.next_reminder_time <= current_time)
            .all()
        )

    @staticmethod
    def update_next_reminder_time(db: Session, item: TodoItem) -> None:
        """
        更新 TODO 项的下次提醒时间.

        Args:
            db: 数据库会话
            item: TODO 项对象
        """
        if item.reminder_interval_hours:
            item.next_reminder_time = now() + timedelta(hours=item.reminder_interval_hours)
            db.commit()

