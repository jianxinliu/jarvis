"""时区工具模块 - 统一使用 UTC+8 时区."""

from datetime import datetime, timezone, timedelta

# UTC+8 时区
UTC_PLUS_8 = timezone(timedelta(hours=8))


def now() -> datetime:
    """
    获取当前 UTC+8 时区的时间.

    Returns:
        datetime: 当前 UTC+8 时区的时间
    """
    return datetime.now(UTC_PLUS_8)


def utc_to_local(utc_dt: datetime) -> datetime:
    """
    将 UTC 时间转换为 UTC+8 时区时间.

    Args:
        utc_dt: UTC 时间

    Returns:
        datetime: UTC+8 时区时间
    """
    if utc_dt.tzinfo is None:
        # 如果没有时区信息，假设是 UTC+8 时区
        return utc_dt.replace(tzinfo=UTC_PLUS_8)
    return utc_dt.astimezone(UTC_PLUS_8)


def local_to_utc(local_dt: datetime) -> datetime:
    """
    将 UTC+8 时区时间转换为 UTC 时间.

    Args:
        local_dt: UTC+8 时区时间

    Returns:
        datetime: UTC 时间
    """
    if local_dt.tzinfo is None:
        # 如果没有时区信息，假设是 UTC+8 时区
        local_dt = local_dt.replace(tzinfo=UTC_PLUS_8)
    return local_dt.astimezone(timezone.utc)


def make_aware(dt: datetime) -> datetime:
    """
    为 datetime 对象添加 UTC+8 时区信息（如果还没有）.

    Args:
        dt: datetime 对象

    Returns:
        datetime: 带时区信息的 datetime 对象
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC_PLUS_8)
    return dt


def today() -> datetime:
    """
    获取今天 UTC+8 时区的日期（时间设为 00:00:00）.

    Returns:
        datetime: 今天的日期
    """
    return now().replace(hour=0, minute=0, second=0, microsecond=0)

