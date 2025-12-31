"""任务服务层."""

from datetime import timedelta
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import Task, SubTask, ReminderLog
from app.utils.timezone import now, today


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
        # 提取子任务数据
        subtasks_data = task_data.pop("subtasks", None) or []

        # 如果有提醒间隔，计算下次提醒时间
        next_reminder_time = None
        if task_data.get("reminder_interval_hours"):
            next_reminder_time = now() + timedelta(hours=task_data["reminder_interval_hours"])

        task = Task(
            title=task_data["title"],
            content=task_data.get("content"),
            priority=task_data.get("priority", 1),
            reminder_interval_hours=task_data.get("reminder_interval_hours"),
            end_time=task_data.get("end_time"),
            next_reminder_time=next_reminder_time,
        )
        db.add(task)
        db.flush()  # 获取 task.id

        # 创建子任务
        for subtask_data in subtasks_data:
            subtask = SubTask(
                task_id=task.id,
                title=subtask_data["title"],
                reminder_time=subtask_data["reminder_time"],
            )
            db.add(subtask)

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
        query = db.query(Task).filter(Task.is_completed == False)  # noqa: E712
        if active_only:
            query = query.filter(Task.is_active == True)  # noqa: E712
        return (
            query.order_by(Task.priority.asc(), Task.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_today_tasks(db: Session) -> list[Task]:
        """
        获取今天需要处理的任务（激活状态的任务）.

        Args:
            db: 数据库会话

        Returns:
            list[Task]: 按优先级排序的任务列表
        """
        today_date = today().date()
        return (
            db.query(Task)
            .filter(Task.is_completed == False)  # noqa: E712
            .filter(Task.is_active == True)  # noqa: E712
            .filter((Task.end_time.is_(None)) | (Task.end_time >= today_date))
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

        # 处理子任务更新
        if "subtasks" in task_data:
            subtasks_data = task_data.pop("subtasks")
            # 删除旧的子任务
            db.query(SubTask).filter(SubTask.task_id == task_id).delete()
            # 创建新的子任务
            if subtasks_data:
                for subtask_data in subtasks_data:
                    subtask = SubTask(
                        task_id=task.id,
                        title=subtask_data["title"],
                        reminder_time=subtask_data["reminder_time"],
                    )
                    db.add(subtask)

        # 更新字段
        for key, value in task_data.items():
            if value is not None:
                setattr(task, key, value)

        # 如果更新了提醒间隔，重新计算下次提醒时间
        if "reminder_interval_hours" in task_data and task_data["reminder_interval_hours"]:  # type: ignore[truthy-bool]
            task.next_reminder_time = now() + timedelta(  # type: ignore
                hours=task_data["reminder_interval_hours"]
            )
        elif (
            "reminder_interval_hours" in task_data and task_data["reminder_interval_hours"] is None
        ):
            task.next_reminder_time = None  # type: ignore

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """
        标记任务为完成（软删除）.

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            bool: 是否成功标记
        """
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False

        # 标记任务为已完成并停用
        task.is_completed = True  # type: ignore
        task.is_active = False  # type: ignore

        # 删除该任务的所有提醒记录（包括已读和未读）
        db.query(ReminderLog).filter(ReminderLog.task_id == task_id).delete()

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
        current_time = now()
        return (
            db.query(Task)
            .filter(Task.is_completed == False)  # noqa: E712
            .filter(Task.is_active == True)  # noqa: E712
            .filter(Task.reminder_interval_hours.isnot(None))
            .filter(Task.next_reminder_time <= current_time)
            .filter((Task.end_time.is_(None)) | (Task.end_time > current_time))
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
        if task.reminder_interval_hours is not None:  # type: ignore
            task.next_reminder_time = now() + timedelta(hours=int(task.reminder_interval_hours))  # type: ignore
            db.commit()

    @staticmethod
    def get_subtasks_by_task_id(db: Session, task_id: int) -> List[SubTask]:
        """
        获取任务的所有子任务.

        Args:
            db: 数据库会话
            task_id: 任务ID

        Returns:
            List[SubTask]: 子任务列表
        """
        return (
            db.query(SubTask)
            .filter(SubTask.task_id == task_id)
            .order_by(SubTask.reminder_time.asc())
            .all()
        )

    @staticmethod
    def get_subtasks_for_reminder(db: Session) -> List[SubTask]:
        """
        获取需要提醒的子任务（定时提醒）.

        Args:
            db: 数据库会话

        Returns:
            List[SubTask]: 需要提醒的子任务列表
        """
        current_time = now()
        # 使用 select_from 明确指定左表，避免 SQLAlchemy 2.0 的歧义
        return (
            db.query(SubTask)
            .select_from(SubTask)
            .join(Task, SubTask.task_id == Task.id)
            .filter(Task.is_active == True)  # noqa: E712
            .filter(SubTask.is_completed == False)  # noqa: E712
            .filter(SubTask.is_notified == False)  # noqa: E712
            .filter(SubTask.reminder_time <= current_time)
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
        subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
        if not subtask:
            return False
        subtask.is_notified = True  # type: ignore
        db.commit()
        return True
