"""应用配置."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        # 从环境变量读取配置（支持 K8s ConfigMap）
        env_file=".env",
        # 大小写不敏感，支持 K8s ConfigMap 中的大写环境变量（如 APP_NAME, DATABASE_URL）
        case_sensitive=False,
        # 自动从环境变量读取，无需前缀
        env_prefix="",
        # 允许环境变量覆盖默认值
        extra="ignore",
    )


settings = Settings()

