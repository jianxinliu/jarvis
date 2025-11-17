"""应用管理相关的 API 路由."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.app_manager import get_app_manager
from app.database import get_db
from app.schemas import AppCreate, AppResponse, AppUpdate
from app.services.app_service import AppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apps", tags=["apps"])


@router.post("", response_model=AppResponse, status_code=status.HTTP_201_CREATED)
def create_app(
    app: AppCreate,
    db: Session = Depends(get_db),
) -> AppResponse:
    """
    创建新应用.

    Args:
        app: 应用创建数据
        db: 数据库会话

    Returns:
        AppResponse: 创建的应用
    """
    # 检查 app_id 是否已存在
    existing = AppService.get_app(db, app.app_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"应用 {app.app_id} 已存在",
        )

    app_data = app.model_dump()
    created_app = AppService.create_app(db, app_data)

    # 尝试加载应用
    try:
        app_manager = get_app_manager()
        app_manager.load_app_from_db(app.app_id)
    except Exception as e:
        logger.warning(f"加载应用 {app.app_id} 失败: {e}")

    return AppResponse.model_validate(created_app)


@router.get("", response_model=List[AppResponse])
def get_apps(
    enabled_only: bool = False,
    builtin_only: bool = False,
    db: Session = Depends(get_db),
) -> List[AppResponse]:
    """
    获取所有应用.

    Args:
        enabled_only: 是否只返回启用的应用
        builtin_only: 是否只返回内置应用
        db: 数据库会话

    Returns:
        List[AppResponse]: 应用列表
    """
    apps = AppService.get_all_apps(db, enabled_only=enabled_only, builtin_only=builtin_only)
    return [AppResponse.model_validate(app) for app in apps]


@router.get("/{app_id}", response_model=AppResponse)
def get_app(app_id: str, db: Session = Depends(get_db)) -> AppResponse:
    """
    根据 app_id 获取应用.

    Args:
        app_id: 应用ID
        db: 数据库会话

    Returns:
        AppResponse: 应用信息

    Raises:
        HTTPException: 如果应用不存在
    """
    app = AppService.get_app(db, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"应用 {app_id} 不存在",
        )
    return AppResponse.model_validate(app)


@router.put("/{app_id}", response_model=AppResponse)
def update_app(
    app_id: str,
    app_update: AppUpdate,
    db: Session = Depends(get_db),
) -> AppResponse:
    """
    更新应用.

    Args:
        app_id: 应用ID
        app_update: 要更新的应用数据
        db: 数据库会话

    Returns:
        AppResponse: 更新后的应用

    Raises:
        HTTPException: 如果应用不存在
    """
    app_data = app_update.model_dump(exclude_unset=True)
    updated_app = AppService.update_app(db, app_id, app_data)
    if not updated_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"应用 {app_id} 不存在",
        )
    return AppResponse.model_validate(updated_app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_app(app_id: str, db: Session = Depends(get_db)) -> None:
    """
    删除应用.

    Args:
        app_id: 应用ID
        db: 数据库会话

    Raises:
        HTTPException: 如果应用不存在或是内置应用
    """
    success = AppService.delete_app(db, app_id)
    if not success:
        app = AppService.get_app(db, app_id)
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"应用 {app_id} 不存在",
            )
        if app.is_builtin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除内置应用",
            )

    # 卸载应用
    try:
        app_manager = get_app_manager()
        app_manager.unregister_app(app_id)
    except Exception as e:
        logger.warning(f"卸载应用 {app_id} 失败: {e}")


@router.post("/{app_id}/toggle", response_model=AppResponse)
def toggle_app(
    app_id: str,
    db: Session = Depends(get_db),
) -> AppResponse:
    """
    切换应用的启用状态.

    Args:
        app_id: 应用ID
        db: 数据库会话

    Returns:
        AppResponse: 更新后的应用

    Raises:
        HTTPException: 如果应用不存在
    """
    app = AppService.toggle_app_enabled(db, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"应用 {app_id} 不存在",
        )

    # 如果启用，尝试加载应用；如果禁用，卸载应用
    try:
        app_manager = get_app_manager()
        if app.is_enabled:
            app_manager.load_app_from_db(app_id)
        else:
            app_manager.unregister_app(app_id)
    except Exception as e:
        logger.warning(f"切换应用 {app_id} 状态失败: {e}")

    return AppResponse.model_validate(app)


@router.post("/{app_id}/reload", response_model=AppResponse)
def reload_app(
    app_id: str,
    db: Session = Depends(get_db),
) -> AppResponse:
    """
    重新加载应用.

    Args:
        app_id: 应用ID
        db: 数据库会话

    Returns:
        AppResponse: 应用信息

    Raises:
        HTTPException: 如果应用不存在或未启用
    """
    app = AppService.get_app(db, app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"应用 {app_id} 不存在",
        )

    if not app.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"应用 {app_id} 未启用",
        )

    # 先卸载，再加载
    try:
        app_manager = get_app_manager()
        app_manager.unregister_app(app_id)
        app_manager.load_app_from_db(app_id)
    except Exception as e:
        logger.error(f"重新加载应用 {app_id} 失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新加载应用失败: {str(e)}",
        )

    return AppResponse.model_validate(app)

