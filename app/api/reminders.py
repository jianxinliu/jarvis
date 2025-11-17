"""提醒相关的 API 路由."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DailySummaryResponse, ReminderLogResponse
from app.apps.tasks.schemas import TaskResponse
from app.services.reminder_service import ReminderService
from app.apps.tasks.service import TaskService

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=List[ReminderLogResponse])
def get_unread_reminders(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[ReminderLogResponse]:
    """
    获取未读提醒.

    Args:
        limit: 返回的最大记录数
        db: 数据库会话

    Returns:
        List[ReminderLogResponse]: 未读提醒列表
    """
    reminders = ReminderService.get_unread_reminders(db, limit=limit)
    return [ReminderLogResponse.model_validate(reminder) for reminder in reminders]


@router.post("/{reminder_id}/read", status_code=status.HTTP_200_OK)
def mark_reminder_as_read(
    reminder_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    标记提醒为已读.

    Args:
        reminder_id: 提醒记录ID
        db: 数据库会话

    Returns:
        dict: 操作结果

    Raises:
        HTTPException: 如果提醒不存在
    """
    success = ReminderService.mark_reminder_as_read(db, reminder_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"提醒 {reminder_id} 不存在",
        )
    return {"message": "提醒已标记为已读", "reminder_id": reminder_id}


@router.get("/daily-summary", response_model=DailySummaryResponse)
def get_daily_summary(db: Session = Depends(get_db)) -> DailySummaryResponse:
    """
    获取每日任务汇总.

    Args:
        db: 数据库会话

    Returns:
        DailySummaryResponse: 每日汇总信息
    """
    from datetime import date

    tasks = TaskService.get_today_tasks(db)
    return DailySummaryResponse(
        date=str(date.today()),
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total_count=len(tasks),
    )

