"""任务服务层."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Task


class TaskService:
    """任务服务类."""

    @staticmethod
    def create_task(db: Session, task_data: dict) -> Task:
        """
        创建新任务.

        Args:
            db: 数据库会话
            task_data: 任务数据字典

        Returns:
            Task: 创建的任务对象
        """
        # 如果有提醒间隔，计算下次提醒时间
        next_reminder_time = None
        if task_data.get("reminder_interval_hours"):
            next_reminder_time = datetime.now() + timedelta(
                hours=task_data["reminder_interval_hours"]
            )

        task = Task(
            title=task_data["title"],
            content=task_data.get("content"),
            priority=task_data.get("priority", 1),
            reminder_interval_hours=task_data.get("reminder_interval_hours"),
            end_time=task_data.get("end_time"),
            next_reminder_time=next_reminder_time,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """
        根据 ID 获取任务.

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            Optional[Task]: 任务对象，如果不存在返回 None
        """
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_all_tasks(
        db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> list[Task]:
        """
        获取所有任务.

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            active_only: 是否只返回激活的任务

        Returns:
            list[Task]: 任务列表
        """
        query = db.query(Task)
        if active_only:
            query = query.filter(Task.is_active == True)  # noqa: E712
        return query.order_by(Task.priority.asc(), Task.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_today_tasks(db: Session) -> list[Task]:
        """
        获取今天需要处理的任务（激活状态的任务）.

        Args:
            db: 数据库会话

        Returns:
            list[Task]: 按优先级排序的任务列表
        """
        today = datetime.now().date()
        return (
            db.query(Task)
            .filter(Task.is_active == True)  # noqa: E712
            .filter(
                (Task.end_time.is_(None)) | (Task.end_time >= datetime.combine(today, datetime.min.time()))
            )
            .order_by(Task.priority.asc(), Task.created_at.desc())
            .all()
        )

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: dict) -> Optional[Task]:
        """
        更新任务.

        Args:
            db: 数据库会话
            task_id: 任务ID
            task_data: 要更新的任务数据字典

        Returns:
            Optional[Task]: 更新后的任务对象，如果不存在返回 None
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None

        # 更新字段
        for key, value in task_data.items():
            if value is not None:
                setattr(task, key, value)

        # 如果更新了提醒间隔，重新计算下次提醒时间
        if "reminder_interval_hours" in task_data and task_data["reminder_interval_hours"]:
            task.next_reminder_time = datetime.now() + timedelta(
                hours=task_data["reminder_interval_hours"]
            )
        elif "reminder_interval_hours" in task_data and task_data["reminder_interval_hours"] is None:
            task.next_reminder_time = None

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """
        删除任务.

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            bool: 是否成功删除
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True

    @staticmethod
    def get_tasks_for_interval_reminder(db: Session) -> list[Task]:
        """
        获取需要执行间隔提醒的任务.

        Args:
            db: 数据库会话

        Returns:
            list[Task]: 需要提醒的任务列表
        """
        now = datetime.now()
        return (
            db.query(Task)
            .filter(Task.is_active == True)  # noqa: E712
            .filter(Task.reminder_interval_hours.isnot(None))
            .filter(Task.next_reminder_time <= now)
            .filter(
                (Task.end_time.is_(None)) | (Task.end_time > now)
            )
            .all()
        )

    @staticmethod
    def update_next_reminder_time(db: Session, task: Task) -> None:
        """
        更新任务的下次提醒时间.

        Args:
            db: 数据库会话
            task: 任务对象
        """
        if task.reminder_interval_hours:
            task.next_reminder_time = datetime.now() + timedelta(hours=task.reminder_interval_hours)
            db.commit()

