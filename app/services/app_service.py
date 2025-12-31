"""应用服务层."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import App


class AppService:
    """应用服务类."""

    @staticmethod
    def create_app(db: Session, app_data: dict) -> App:
        """
        创建新应用.

        Args:
            db: 数据库会话
            app_data: 应用数据字典

        Returns:
            App: 创建的应用对象
        """
        app = App(
            app_id=app_data["app_id"],
            name=app_data["name"],
            description=app_data.get("description"),
            icon=app_data.get("icon"),
            version=app_data.get("version", "1.0.0"),
            author=app_data.get("author"),
            route_prefix=app_data["route_prefix"],
            frontend_path=app_data.get("frontend_path"),
            config=app_data.get("config"),
            is_builtin=app_data.get("is_builtin", False),
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def get_app(db: Session, app_id: str) -> Optional[App]:
        """
        根据 app_id 获取应用.

        Args:
            db: 数据库会话
            app_id: 应用ID

        Returns:
            Optional[App]: 应用对象，如果不存在返回 None
        """
        return db.query(App).filter(App.app_id == app_id).first()

    @staticmethod
    def get_app_by_id(db: Session, id: int) -> Optional[App]:
        """
        根据 ID 获取应用.

        Args:
            db: 数据库会话
            id: 应用数据库ID

        Returns:
            Optional[App]: 应用对象，如果不存在返回 None
        """
        return db.query(App).filter(App.id == id).first()

    @staticmethod
    def get_all_apps(
        db: Session, enabled_only: bool = False, builtin_only: bool = False
    ) -> list[App]:
        """
        获取所有应用.

        Args:
            db: 数据库会话
            enabled_only: 是否只返回启用的应用
            builtin_only: 是否只返回内置应用

        Returns:
            list[App]: 应用列表
        """
        query = db.query(App)
        if enabled_only:
            query = query.filter(App.is_enabled == True)  # noqa: E712
        if builtin_only:
            query = query.filter(App.is_builtin == True)  # noqa: E712
        return query.order_by(App.created_at.desc()).all()

    @staticmethod
    def update_app(db: Session, app_id: str, app_data: dict) -> Optional[App]:
        """
        更新应用.

        Args:
            db: 数据库会话
            app_id: 应用ID
            app_data: 要更新的应用数据字典

        Returns:
            Optional[App]: 更新后的应用对象，如果不存在返回 None
        """
        app = db.query(App).filter(App.app_id == app_id).first()
        if not app:
            return None

        # 更新字段
        for key, value in app_data.items():
            if value is not None:
                setattr(app, key, value)

        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def delete_app(db: Session, app_id: str) -> bool:
        """
        删除应用（非内置应用）.

        Args:
            db: 数据库会话
            app_id: 应用ID

        Returns:
            bool: 是否成功删除
        """
        app = db.query(App).filter(App.app_id == app_id).first()
        if not app:
            return False

        # 不允许删除内置应用
        if app.is_builtin:  # type: ignore
            return False

        db.delete(app)
        db.commit()
        return True

    @staticmethod
    def toggle_app_enabled(db: Session, app_id: str) -> Optional[App]:
        """
        切换应用的启用状态.

        Args:
            db: 数据库会话
            app_id: 应用ID

        Returns:
            Optional[App]: 更新后的应用对象，如果不存在返回 None
        """
        app = db.query(App).filter(App.app_id == app_id).first()
        if not app:
            return None

        app.is_enabled = not bool(app.is_enabled)  # type: ignore  # type: ignore[assignment]
        db.commit()
        db.refresh(app)
        return app
