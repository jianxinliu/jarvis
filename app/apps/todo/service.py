"""TODO 服务层."""

from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import TodoItem, TodoTag, TodoPriority
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
        
        item = TodoItem(
            title=item_data["title"],
            content=item_data.get("content"),
            quadrant=item_data["quadrant"],
            priority_id=item_data.get("priority_id"),
            due_time=item_data.get("due_time"),
            reminder_time=item_data.get("reminder_time"),
        )
        
        # 添加标签
        if tag_ids:
            tags = db.query(TodoTag).filter(TodoTag.id.in_(tag_ids)).all()
            item.tags = tags
        
        db.add(item)
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
        return db.query(TodoItem).filter(TodoItem.id == item_id).first()

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
        query = db.query(TodoItem).filter(TodoItem.quadrant == quadrant)
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
            List[TodoItem]: TODO 项列表
        """
        query = db.query(TodoItem)
        if not include_archived:
            query = query.filter(TodoItem.is_archived == False)  # noqa: E712
        if not include_completed:
            query = query.filter(TodoItem.is_completed == False)  # noqa: E712
        return query.order_by(TodoItem.created_at.desc()).all()

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

        # 处理标签更新
        if "tag_ids" in item_data:
            tag_ids = item_data.pop("tag_ids")
            if tag_ids is not None:
                tags = db.query(TodoTag).filter(TodoTag.id.in_(tag_ids)).all()
                item.tags = tags

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

