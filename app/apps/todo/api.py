"""TODO 相关的 API 路由."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.apps.todo.schemas import (
    TodoItemCreate,
    TodoItemResponse,
    TodoItemUpdate,
    TodoTagCreate,
    TodoTagResponse,
    TodoTagUpdate,
    TodoPriorityCreate,
    TodoPriorityResponse,
    TodoPriorityUpdate,
    TodoSubTaskResponse,
)
from app.apps.todo.service import TodoService

router = APIRouter(prefix="/api/todo", tags=["todo"])


# TODO 项相关接口
@router.post("/items", response_model=TodoItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: TodoItemCreate,
    db: Session = Depends(get_db),
) -> TodoItemResponse:
    """创建 TODO 项."""
    item_data = item.model_dump()
    created_item = TodoService.create_item(db, item_data)
    return TodoItemResponse.model_validate(created_item)


@router.get("/items", response_model=List[TodoItemResponse])
def get_items(
    quadrant: Optional[str] = None,
    include_archived: bool = False,
    include_completed: bool = True,
    db: Session = Depends(get_db),
) -> List[TodoItemResponse]:
    """获取 TODO 项列表."""
    if quadrant:
        items = TodoService.get_items_by_quadrant(db, quadrant, include_archived)
    else:
        items = TodoService.get_all_items(db, include_archived, include_completed)
    return [TodoItemResponse.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=TodoItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)) -> TodoItemResponse:
    """根据 ID 获取 TODO 项."""
    item = TodoService.get_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO 项 {item_id} 不存在",
        )
    return TodoItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=TodoItemResponse)
def update_item(
    item_id: int,
    item_update: TodoItemUpdate,
    db: Session = Depends(get_db),
) -> TodoItemResponse:
    """更新 TODO 项."""
    item_data = item_update.model_dump(exclude_unset=True)
    updated_item = TodoService.update_item(db, item_id, item_data)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO 项 {item_id} 不存在",
        )
    return TodoItemResponse.model_validate(updated_item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """删除 TODO 项."""
    success = TodoService.delete_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"TODO 项 {item_id} 不存在",
        )


# 标签相关接口
@router.post("/tags", response_model=TodoTagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: TodoTagCreate,
    db: Session = Depends(get_db),
) -> TodoTagResponse:
    """创建标签."""
    tag_data = tag.model_dump()
    created_tag = TodoService.create_tag(db, tag_data)
    return TodoTagResponse.model_validate(created_tag)


@router.get("/tags", response_model=List[TodoTagResponse])
def get_tags(db: Session = Depends(get_db)) -> List[TodoTagResponse]:
    """获取所有标签."""
    tags = TodoService.get_all_tags(db)
    return [TodoTagResponse.model_validate(tag) for tag in tags]


@router.put("/tags/{tag_id}", response_model=TodoTagResponse)
def update_tag(
    tag_id: int,
    tag_update: TodoTagUpdate,
    db: Session = Depends(get_db),
) -> TodoTagResponse:
    """更新标签."""
    tag_data = tag_update.model_dump(exclude_unset=True)
    updated_tag = TodoService.update_tag(db, tag_id, tag_data)
    if not updated_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"标签 {tag_id} 不存在",
        )
    return TodoTagResponse.model_validate(updated_tag)


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> None:
    """删除标签."""
    success = TodoService.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"标签 {tag_id} 不存在",
        )


# 优先级相关接口
@router.post(
    "/priorities", response_model=TodoPriorityResponse, status_code=status.HTTP_201_CREATED
)
def create_priority(
    priority: TodoPriorityCreate,
    db: Session = Depends(get_db),
) -> TodoPriorityResponse:
    """创建优先级."""
    priority_data = priority.model_dump()
    created_priority = TodoService.create_priority(db, priority_data)
    return TodoPriorityResponse.model_validate(created_priority)


@router.get("/priorities", response_model=List[TodoPriorityResponse])
def get_priorities(db: Session = Depends(get_db)) -> List[TodoPriorityResponse]:
    """获取所有优先级."""
    priorities = TodoService.get_all_priorities(db)
    return [TodoPriorityResponse.model_validate(p) for p in priorities]


@router.put("/priorities/{priority_id}", response_model=TodoPriorityResponse)
def update_priority(
    priority_id: int,
    priority_update: TodoPriorityUpdate,
    db: Session = Depends(get_db),
) -> TodoPriorityResponse:
    """更新优先级."""
    priority_data = priority_update.model_dump(exclude_unset=True)
    updated_priority = TodoService.update_priority(db, priority_id, priority_data)
    if not updated_priority:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优先级 {priority_id} 不存在",
        )
    return TodoPriorityResponse.model_validate(updated_priority)


@router.delete("/priorities/{priority_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_priority(priority_id: int, db: Session = Depends(get_db)) -> None:
    """删除优先级."""
    success = TodoService.delete_priority(db, priority_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优先级 {priority_id} 不存在",
        )


# 子任务相关接口
@router.get("/items/{item_id}/subtasks", response_model=List[TodoSubTaskResponse])
def get_subtasks(item_id: int, db: Session = Depends(get_db)) -> List[TodoSubTaskResponse]:
    """获取 TODO 项的所有子任务."""
    subtasks = TodoService.get_subtasks_by_item_id(db, item_id)
    return [TodoSubTaskResponse.model_validate(subtask) for subtask in subtasks]
