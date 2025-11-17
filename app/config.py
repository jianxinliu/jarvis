"""应用配置."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类."""

    # 应用基础配置
    app_name: str = "Jarvis"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库配置
    database_url: str = "sqlite:///./jarvis.db"

    # 提醒配置
    morning_reminder_time: str = "08:00"  # 每日早晨提醒时间 (HH:MM)

    # 日志配置
    enable_logging: bool = False  # 是否启用日志输出，默认关闭
    enable_sql_echo: bool = False  # 是否启用 SQL 输出，默认关闭

    class Config:
        """Pydantic 配置."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()

