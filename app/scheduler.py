"""定时任务调度器."""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.api.websocket import broadcast_reminder
from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """提醒调度器类."""

    def __init__(self) -> None:
        """初始化调度器."""
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def start(self, morning_reminder_time: str = "08:00") -> None:
        """
        启动调度器.

        Args:
            morning_reminder_time: 每日早晨提醒时间，格式为 "HH:MM"
        """
        if self.is_running:
            logger.warning("调度器已经在运行中")
            return

        # 解析早晨提醒时间
        hour, minute = map(int, morning_reminder_time.split(":"))

        # 添加间隔提醒任务（每 5 分钟检查一次）
        self.scheduler.add_job(
            self._process_interval_reminders,
            trigger=IntervalTrigger(minutes=5),
            id="interval_reminders",
            name="处理间隔提醒",
            replace_existing=True,
        )

        # 添加每日汇总提醒任务
        self.scheduler.add_job(
            self._process_daily_summary,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_summary",
            name="每日汇总提醒",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        logger.info(f"提醒调度器已启动，每日提醒时间: {morning_reminder_time}")

    def stop(self) -> None:
        """停止调度器."""
        if not self.is_running:
            return
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("提醒调度器已停止")

    def _process_interval_reminders(self) -> None:
        """处理间隔提醒的内部方法."""
        db: Session = SessionLocal()
        try:
            reminder_logs = ReminderService.process_interval_reminders(db)
            if reminder_logs:
                logger.info(f"处理了 {len(reminder_logs)} 个间隔提醒")
                # 广播提醒到 WebSocket 客户端并发送系统通知
                for reminder_log in reminder_logs:
                    reminder_data = {
                        "id": reminder_log.id,
                        "task_id": reminder_log.task_id,
                        "type": reminder_log.reminder_type,
                        "content": reminder_log.content,
                        "time": reminder_log.reminder_time.isoformat(),
                    }
                    # WebSocket 广播
                    broadcast_reminder(reminder_data)
                    # 系统通知
                    NotificationService.send_notification(
                        title="Jarvis 提醒",
                        message=reminder_log.content or "您有新的提醒",
                        subtitle="间隔提醒",
                    )
        except Exception as e:
            logger.error(f"处理间隔提醒时出错: {e}", exc_info=True)
        finally:
            db.close()

    def _process_daily_summary(self) -> None:
        """处理每日汇总提醒的内部方法."""
        db: Session = SessionLocal()
        try:
            reminder_log = ReminderService.process_daily_summary(db)
            if reminder_log:
                logger.info(f"已创建每日汇总提醒: {reminder_log.id}")
                reminder_data = {
                    "id": reminder_log.id,
                    "task_id": reminder_log.task_id,
                    "type": reminder_log.reminder_type,
                    "content": reminder_log.content,
                    "time": reminder_log.reminder_time.isoformat(),
                }
                # WebSocket 广播
                broadcast_reminder(reminder_data)
                # 系统通知
                NotificationService.send_notification(
                    title="Jarvis 每日汇总",
                    message=reminder_log.content or "今日任务汇总",
                    subtitle="每日提醒",
                )
            else:
                logger.info("今日无待办任务，未创建汇总提醒")
        except Exception as e:
            logger.error(f"处理每日汇总提醒时出错: {e}", exc_info=True)
        finally:
            db.close()


# 全局调度器实例
scheduler = ReminderScheduler()

