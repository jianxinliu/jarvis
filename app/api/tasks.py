"""任务相关的 API 路由."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    创建新任务.

    Args:
        task: 任务创建数据
        db: 数据库会话

    Returns:
        TaskResponse: 创建的任务
    """
    task_data = task.model_dump()
    created_task = TaskService.create_task(db, task_data)
    return TaskResponse.model_validate(created_task)


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[TaskResponse]:
    """
    获取所有任务.

    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        active_only: 是否只返回激活的任务
        db: 数据库会话

    Returns:
        List[TaskResponse]: 任务列表
    """
    tasks = TaskService.get_all_tasks(db, skip=skip, limit=limit, active_only=active_only)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/today", response_model=List[TaskResponse])
def get_today_tasks(db: Session = Depends(get_db)) -> List[TaskResponse]:
    """
    获取今天需要处理的任务.

    Args:
        db: 数据库会话

    Returns:
        List[TaskResponse]: 按优先级排序的任务列表
    """
    tasks = TaskService.get_today_tasks(db)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    """
    根据 ID 获取任务.

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        TaskResponse: 任务信息

    Raises:
        HTTPException: 如果任务不存在
    """
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    更新任务.

    Args:
        task_id: 任务ID
        task_update: 要更新的任务数据
        db: 数据库会话

    Returns:
        TaskResponse: 更新后的任务

    Raises:
        HTTPException: 如果任务不存在
    """
    task_data = task_update.model_dump(exclude_unset=True)
    updated_task = TaskService.update_task(db, task_id, task_data)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )
    return TaskResponse.model_validate(updated_task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    """
    删除任务.

    Args:
        task_id: 任务ID
        db: 数据库会话

    Raises:
        HTTPException: 如果任务不存在
    """
    success = TaskService.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在",
        )

