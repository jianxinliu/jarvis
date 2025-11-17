"""提醒服务层."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import ReminderLog, Task
from app.apps.tasks.service import TaskService


class ReminderService:
    """提醒服务类."""

    @staticmethod
    def create_reminder_log(
        db: Session,
        task_id: int,
        reminder_type: str,
        content: Optional[str] = None,
    ) -> ReminderLog:
        """
        创建提醒记录.

        Args:
            db: 数据库会话
            task_id: 任务ID
            reminder_type: 提醒类型 (interval 或 daily)
            content: 提醒内容

        Returns:
            ReminderLog: 创建的提醒记录对象
        """
        reminder_log = ReminderLog(
            task_id=task_id,
            reminder_type=reminder_type,
            content=content,
        )
        db.add(reminder_log)
        db.commit()
        db.refresh(reminder_log)
        return reminder_log

    @staticmethod
    def get_unread_reminders(db: Session, limit: int = 50) -> list[ReminderLog]:
        """
        获取未读提醒.

        Args:
            db: 数据库会话
            limit: 返回的最大记录数

        Returns:
            list[ReminderLog]: 未读提醒列表
        """
        return (
            db.query(ReminderLog)
            .filter(ReminderLog.is_read == False)  # noqa: E712
            .order_by(ReminderLog.reminder_time.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def mark_reminder_as_read(db: Session, reminder_id: int) -> bool:
        """
        标记提醒为已读.

        Args:
            db: 数据库会话
            reminder_id: 提醒记录ID

        Returns:
            bool: 是否成功标记
        """
        reminder = db.query(ReminderLog).filter(ReminderLog.id == reminder_id).first()
        if not reminder:
            return False
        reminder.is_read = True
        db.commit()
        return True

    @staticmethod
    def process_interval_reminders(db: Session) -> list[ReminderLog]:
        """
        处理间隔提醒：查找需要提醒的任务并创建提醒记录.

        Args:
            db: 数据库会话

        Returns:
            list[ReminderLog]: 创建的提醒记录列表
        """
        tasks = TaskService.get_tasks_for_interval_reminder(db)
        reminder_logs = []

        for task in tasks:
            # 创建提醒记录
            content = task.content or f"提醒：{task.title}"
            reminder_log = ReminderService.create_reminder_log(
                db=db,
                task_id=task.id,
                reminder_type="interval",
                content=content,
            )
            reminder_logs.append(reminder_log)

            # 更新下次提醒时间
            TaskService.update_next_reminder_time(db, task)

        return reminder_logs

    @staticmethod
    def process_daily_summary(db: Session) -> Optional[ReminderLog]:
        """
        处理每日汇总提醒：获取今天的任务并创建汇总提醒.

        Args:
            db: 数据库会话

        Returns:
            Optional[ReminderLog]: 创建的汇总提醒记录，如果没有任务则返回 None
        """
        tasks = TaskService.get_today_tasks(db)
        if not tasks:
            return None

        # 生成汇总内容
        task_list = "\n".join(
            [
                f"优先级 {task.priority}: {task.title}"
                for task in sorted(tasks, key=lambda x: x.priority)
            ]
        )
        content = f"今日待办任务汇总（共 {len(tasks)} 项）：\n\n{task_list}"

        # 创建汇总提醒记录（使用 task_id=0 表示汇总提醒）
        reminder_log = ReminderLog(
            task_id=0,
            reminder_type="daily",
            content=content,
        )
        db.add(reminder_log)
        db.commit()
        db.refresh(reminder_log)
        return reminder_log

