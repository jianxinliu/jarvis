"""提醒服务层."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import ReminderLog, Task, SubTask
from app.apps.tasks.service import TaskService
from app.apps.todo.service import TodoService
from app.utils.timezone import now


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

    @staticmethod
    def process_subtask_reminders(db: Session) -> list[ReminderLog]:
        """
        处理子任务提醒：查找需要提醒的子任务并创建提醒记录.

        Args:
            db: 数据库会话

        Returns:
            list[ReminderLog]: 创建的提醒记录列表
        """
        subtasks = TaskService.get_subtasks_for_reminder(db)
        reminder_logs = []

        for subtask in subtasks:
            # 获取父任务
            task = TaskService.get_task(db, subtask.task_id)
            if not task:
                continue

            # 创建提醒记录
            content = f"子任务提醒：{subtask.title}"
            reminder_log = ReminderService.create_reminder_log(
                db=db,
                task_id=task.id,
                reminder_type="subtask",
                content=content,
            )
            # 设置子任务ID
            reminder_log.subtask_id = subtask.id
            db.commit()
            db.refresh(reminder_log)

            reminder_logs.append(reminder_log)

            # 标记子任务为已提醒
            TaskService.mark_subtask_as_notified(db, subtask.id)

        return reminder_logs

    @staticmethod
    def process_todo_reminders(db: Session) -> list[ReminderLog]:
        """
        处理 TODO 项的提醒：查找需要提醒的 TODO 项并创建提醒记录.

        Args:
            db: 数据库会话

        Returns:
            list[ReminderLog]: 创建的提醒记录列表
        """
        from app.models import TodoItem

        now_time = now()
        # 查找需要提醒的 TODO 项（紧急象限，有提醒时间，未完成，未归档）
        todo_items = (
            db.query(TodoItem)
            .filter(TodoItem.quadrant == "urgent")
            .filter(TodoItem.reminder_time.isnot(None))
            .filter(TodoItem.reminder_time <= now_time)
            .filter(TodoItem.is_completed == False)  # noqa: E712
            .filter(TodoItem.is_archived == False)  # noqa: E712
            .all()
        )

        reminder_logs = []
        for item in todo_items:
            # 创建提醒记录
            content = f"TODO 提醒：{item.title}"
            reminder_log = ReminderService.create_reminder_log(
                db=db,
                task_id=0,  # TODO 项不使用 task_id
                reminder_type="todo",
                content=content,
            )
            reminder_logs.append(reminder_log)

            # 清除提醒时间（避免重复提醒）
            item.reminder_time = None
            db.commit()

        return reminder_logs

    @staticmethod
    def process_todo_daily_reminder(db: Session) -> Optional[ReminderLog]:
        """
        处理 TODO 每日提醒：获取今天要做的事情并创建提醒记录.

        Args:
            db: 数据库会话

        Returns:
            Optional[ReminderLog]: 创建的提醒记录，如果没有 TODO 项则返回 None
        """
        todo_items = TodoService.get_today_todos(db)
        if not todo_items:
            return None

        # 按象限分组
        quadrant_map = {
            'reminder': '提醒',
            'record': '记录',
            'urgent': '紧急',
            'important': '重要',
        }
        
        items_by_quadrant = {}
        for item in todo_items:
            quadrant_label = quadrant_map.get(item.quadrant, item.quadrant)
            if quadrant_label not in items_by_quadrant:
                items_by_quadrant[quadrant_label] = []
            items_by_quadrant[quadrant_label].append(item)

        # 生成提醒内容
        content_parts = [f"今天要做的事情（共 {len(todo_items)} 项）：\n"]
        
        for quadrant_label, items in items_by_quadrant.items():
            content_parts.append(f"\n【{quadrant_label}象限】")
            for item in items:
                priority_text = f"（优先级：{item.priority.name}）" if item.priority else ""
                due_text = f" - 截止：{item.due_time.strftime('%Y-%m-%d %H:%M')}" if item.due_time else ""
                content_parts.append(f"  • {item.title}{priority_text}{due_text}")
        
        content = "\n".join(content_parts)

        # 创建提醒记录（使用 task_id=0 表示 TODO 每日提醒）
        reminder_log = ReminderLog(
            task_id=0,
            reminder_type="todo_daily",
            content=content,
        )
        db.add(reminder_log)
        db.commit()
        db.refresh(reminder_log)
        return reminder_log

