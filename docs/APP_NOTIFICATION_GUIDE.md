# App 通知发送指南

本文档描述如何在 Jarvis 平台中为新增的 App 实现通知功能，将提醒消息发送到启动台的通知中心。

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [方法一：通过 ReminderService 创建提醒](#方法一通过-reminderservice-创建提醒)
- [方法二：直接创建 ReminderLog 并发送通知](#方法二直接创建-reminderlog-并发送通知)
- [WebSocket 实时通知](#websocket-实时通知)
- [完整示例](#完整示例)
- [最佳实践](#最佳实践)
- [API 参考](#api-参考)

## 概述

Jarvis 的通知系统由以下组件组成：

1. **ReminderLog 模型**：存储提醒记录
2. **ReminderService**：提供创建提醒的服务方法
3. **WebSocket 服务**：实时推送通知到前端
4. **通知中心**：启动台右侧显示所有未读提醒

通知流程：
```
App 业务逻辑 → 创建 ReminderLog → 发送 WebSocket 通知 → 前端接收并显示
```

## 快速开始

最简单的发送通知方式：

```python
from app.services.reminder_service import ReminderService
from app.api.websocket import broadcast_reminder
from app.database import get_db

# 在您的 API 路由或服务中
def send_notification():
    db = next(get_db())
    
    # 1. 创建提醒记录
    reminder = ReminderService.create_reminder_log(
        db=db,
        task_id=0,  # 如果与任务无关，使用 0
        reminder_type="custom",  # 自定义类型
        content="这是一条来自我的 App 的通知",
        app_id="my_app"  # 您的 app_id
    )
    
    # 2. 发送实时通知
    reminder_data = {
        "id": reminder.id,
        "task_id": reminder.task_id,
        "type": reminder.reminder_type,
        "content": reminder.content,
        "time": reminder.reminder_time.isoformat(),
        "app_id": reminder.app_id,
    }
    broadcast_reminder(reminder_data)
```

## 方法一：通过 ReminderService 创建提醒

这是推荐的方式，使用 `ReminderService.create_reminder_log()` 方法。

### 基本用法

```python
from app.services.reminder_service import ReminderService
from app.database import get_db

def my_app_notification_handler(db: Session):
    """发送通知的示例函数"""
    
    # 创建提醒记录
    reminder = ReminderService.create_reminder_log(
        db=db,
        task_id=0,  # 任务ID，如果与任务无关使用 0
        reminder_type="my_app_notification",  # 提醒类型
        content="您有一条新消息",  # 提醒内容
        app_id="my_app"  # 您的应用ID
    )
    
    return reminder
```

### 参数说明

- `db` (Session): 数据库会话对象
- `task_id` (int): 关联的任务ID。如果通知与任务无关，使用 `0`
- `reminder_type` (str): 提醒类型，可以是：
  - 系统内置类型：`interval`, `daily`, `subtask`, `todo`, `todo_daily`
  - 自定义类型：如 `my_app_notification`, `alert`, `warning` 等
- `content` (Optional[str]): 提醒内容，支持多行文本
- `app_id` (Optional[str]): 来源应用ID。如果不提供，系统会根据 `reminder_type` 自动判断：
  - `interval`, `daily`, `subtask` → `"tasks"`
  - `todo`, `todo_daily` → `"todo"`
  - 其他类型 → `None`

### 示例：发送不同类型的通知

```python
from app.services.reminder_service import ReminderService
from app.database import get_db

def send_various_notifications(db: Session):
    """发送多种类型的通知示例"""
    
    # 1. 信息通知
    ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="info",
        content="操作成功完成",
        app_id="my_app"
    )
    
    # 2. 警告通知
    ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="warning",
        content="请注意：数据量较大，处理可能需要一些时间",
        app_id="my_app"
    )
    
    # 3. 错误通知
    ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="error",
        content="处理失败：连接超时",
        app_id="my_app"
    )
    
    # 4. 成功通知
    ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="success",
        content="文件已成功上传",
        app_id="my_app"
    )
```

## 方法二：直接创建 ReminderLog 并发送通知

如果需要更多控制，可以直接创建 `ReminderLog` 对象：

```python
from app.models import ReminderLog
from app.database import get_db
from app.utils.timezone import now

def create_custom_reminder(db: Session):
    """直接创建提醒记录"""
    
    reminder = ReminderLog(
        task_id=0,
        reminder_type="custom",
        content="自定义提醒内容",
        app_id="my_app",
        reminder_time=now(),
        is_read=False
    )
    
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    return reminder
```

## WebSocket 实时通知

创建提醒记录后，需要发送 WebSocket 通知以实时推送到前端。

### 发送 WebSocket 通知

```python
from app.api.websocket import broadcast_reminder
from app.services.reminder_service import ReminderService

def send_notification_with_websocket(db: Session):
    """创建提醒并发送实时通知"""
    
    # 1. 创建提醒记录
    reminder = ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="my_app_notification",
        content="您有一条新消息",
        app_id="my_app"
    )
    
    # 2. 准备通知数据
    reminder_data = {
        "id": reminder.id,
        "task_id": reminder.task_id,
        "type": reminder.reminder_type,
        "content": reminder.content,
        "time": reminder.reminder_time.isoformat(),
        "app_id": reminder.app_id,
    }
    
    # 3. 发送 WebSocket 通知
    broadcast_reminder(reminder_data)
    
    return reminder
```

### WebSocket 消息格式

发送到前端的消息格式：

```json
{
  "type": "reminder",
  "data": {
    "id": 123,
    "task_id": 0,
    "type": "my_app_notification",
    "content": "您有一条新消息",
    "time": "2025-01-15T10:30:00",
    "app_id": "my_app"
  },
  "timestamp": "2025-01-15T10:30:00"
}
```

## 完整示例

### 示例 1：在 API 路由中发送通知

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.reminder_service import ReminderService
from app.api.websocket import broadcast_reminder

router = APIRouter(prefix="/api/my-app", tags=["my-app"])

@router.post("/send-notification")
def send_notification(
    message: str,
    db: Session = Depends(get_db)
):
    """发送通知的 API 端点"""
    
    try:
        # 创建提醒记录
        reminder = ReminderService.create_reminder_log(
            db=db,
            task_id=0,
            reminder_type="my_app_notification",
            content=message,
            app_id="my_app"
        )
        
        # 发送实时通知
        reminder_data = {
            "id": reminder.id,
            "task_id": reminder.task_id,
            "type": reminder.reminder_type,
            "content": reminder.content,
            "time": reminder.reminder_time.isoformat(),
            "app_id": reminder.app_id,
        }
        broadcast_reminder(reminder_data)
        
        return {
            "success": True,
            "reminder_id": reminder.id,
            "message": "通知已发送"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 示例 2：在后台任务中发送通知

```python
from app.services.reminder_service import ReminderService
from app.api.websocket import broadcast_reminder
from app.database import SessionLocal

def background_task():
    """后台任务示例"""
    db = SessionLocal()
    try:
        # 执行某些操作
        result = do_something()
        
        # 操作完成后发送通知
        if result.success:
            reminder = ReminderService.create_reminder_log(
                db=db,
                task_id=0,
                reminder_type="task_completed",
                content=f"任务已完成：{result.message}",
                app_id="my_app"
            )
            
            reminder_data = {
                "id": reminder.id,
                "task_id": reminder.task_id,
                "type": reminder.reminder_type,
                "content": reminder.content,
                "time": reminder.reminder_time.isoformat(),
                "app_id": reminder.app_id,
            }
            broadcast_reminder(reminder_data)
    finally:
        db.close()
```

### 示例 3：定时任务发送通知

```python
from app.services.reminder_service import ReminderService
from app.api.websocket import broadcast_reminder
from app.database import SessionLocal
from app.utils.timezone import now
import schedule
import time

def send_daily_report():
    """每日报告通知"""
    db = SessionLocal()
    try:
        # 生成报告内容
        report_content = generate_daily_report()
        
        # 创建提醒
        reminder = ReminderService.create_reminder_log(
            db=db,
            task_id=0,
            reminder_type="daily_report",
            content=report_content,
            app_id="my_app"
        )
        
        # 发送通知
        reminder_data = {
            "id": reminder.id,
            "task_id": reminder.task_id,
            "type": reminder.reminder_type,
            "content": reminder.content,
            "time": reminder.reminder_time.isoformat(),
            "app_id": reminder.app_id,
        }
        broadcast_reminder(reminder_data)
    finally:
        db.close()

# 每天上午 9 点发送
schedule.every().day.at("09:00").do(send_daily_report)
```

## 最佳实践

### 1. 使用有意义的提醒类型

```python
# ✅ 好的做法
reminder_type="file_upload_completed"
reminder_type="data_processing_failed"
reminder_type="user_action_required"

# ❌ 不好的做法
reminder_type="msg"
reminder_type="notify"
reminder_type="1"
```

### 2. 提供清晰的提醒内容

```python
# ✅ 好的做法
content = f"文件 '{filename}' 已成功上传到 {destination}"
content = f"处理失败：{error_message}。请检查配置后重试。"

# ❌ 不好的做法
content = "完成"
content = "错误"
```

### 3. 始终设置 app_id

```python
# ✅ 好的做法
ReminderService.create_reminder_log(
    db=db,
    task_id=0,
    reminder_type="my_notification",
    content="消息内容",
    app_id="my_app"  # 明确指定
)

# ❌ 不好的做法（依赖自动判断，可能不准确）
ReminderService.create_reminder_log(
    db=db,
    task_id=0,
    reminder_type="my_notification",
    content="消息内容"
    # 缺少 app_id
)
```

### 4. 错误处理

```python
from app.services.reminder_service import ReminderService
from app.api.websocket import broadcast_reminder
import logging

logger = logging.getLogger(__name__)

def safe_send_notification(db: Session, content: str):
    """安全地发送通知，包含错误处理"""
    try:
        reminder = ReminderService.create_reminder_log(
            db=db,
            task_id=0,
            reminder_type="notification",
            content=content,
            app_id="my_app"
        )
        
        reminder_data = {
            "id": reminder.id,
            "task_id": reminder.task_id,
            "type": reminder.reminder_type,
            "content": reminder.content,
            "time": reminder.reminder_time.isoformat(),
            "app_id": reminder.app_id,
        }
        broadcast_reminder(reminder_data)
        
        logger.info(f"通知已发送: {reminder.id}")
    except Exception as e:
        logger.error(f"发送通知失败: {e}", exc_info=True)
        # 不要因为通知失败而影响主业务流程
```

### 5. 避免发送过多通知

```python
# ✅ 好的做法：合并多个事件为一个通知
def send_batch_notification(db: Session, events: list):
    """批量事件合并为一个通知"""
    if not events:
        return
    
    content = f"共 {len(events)} 个事件：\n"
    content += "\n".join([f"• {event}" for event in events])
    
    ReminderService.create_reminder_log(
        db=db,
        task_id=0,
        reminder_type="batch_events",
        content=content,
        app_id="my_app"
    )

# ❌ 不好的做法：每个事件都发送一个通知
def send_too_many_notifications(db: Session, events: list):
    for event in events:
        ReminderService.create_reminder_log(
            db=db,
            task_id=0,
            reminder_type="event",
            content=str(event),
            app_id="my_app"
        )
```

## API 参考

### ReminderService.create_reminder_log()

创建提醒记录的服务方法。

**签名：**
```python
@staticmethod
def create_reminder_log(
    db: Session,
    task_id: int,
    reminder_type: str,
    content: Optional[str] = None,
    app_id: Optional[str] = None,
) -> ReminderLog
```

**参数：**
- `db` (Session): 数据库会话
- `task_id` (int): 任务ID，无关任务使用 0
- `reminder_type` (str): 提醒类型
- `content` (Optional[str]): 提醒内容
- `app_id` (Optional[str]): 应用ID

**返回：**
- `ReminderLog`: 创建的提醒记录对象

### broadcast_reminder()

发送 WebSocket 实时通知。

**签名：**
```python
def broadcast_reminder(reminder_data: dict) -> None
```

**参数：**
- `reminder_data` (dict): 提醒数据字典，包含：
  - `id` (int): 提醒ID
  - `task_id` (int): 任务ID
  - `type` (str): 提醒类型
  - `content` (str): 提醒内容
  - `time` (str): 提醒时间（ISO 格式）
  - `app_id` (str): 应用ID

## 前端显示

通知发送后，会在启动台右侧的"通知中心"中显示：

1. **应用标识**：显示应用图标和名称
2. **提醒类型**：显示提醒类型（如"间隔提醒"、"自定义通知"等）
3. **提醒内容**：显示完整的提醒内容
4. **时间戳**：显示提醒创建时间
5. **操作按钮**：用户可以标记为已读

## 常见问题

### Q: 如何确保通知一定会显示？

A: 创建 `ReminderLog` 记录后，即使 WebSocket 发送失败，用户刷新页面时也会在通知中心看到未读提醒。

### Q: 可以发送富文本或 HTML 内容吗？

A: 目前支持纯文本和多行文本。内容会原样显示，支持换行。

### Q: 如何删除已发送的通知？

A: 通知一旦创建，只能标记为已读，不能删除。这是设计上的考虑，用于保留通知历史。

### Q: 可以发送图片或附件吗？

A: 目前不支持。可以在 `content` 中包含链接，用户点击后跳转到相关页面。

### Q: 如何限制通知频率？

A: 在应用层面实现限流逻辑，例如：

```python
from datetime import datetime, timedelta
from app.models import ReminderLog

def can_send_notification(db: Session, app_id: str, minutes: int = 5) -> bool:
    """检查是否可以发送通知（限流）"""
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    recent_count = db.query(ReminderLog).filter(
        ReminderLog.app_id == app_id,
        ReminderLog.reminder_time >= cutoff_time
    ).count()
    
    return recent_count < 10  # 5分钟内最多10条
```

## 总结

发送通知到启动台的步骤：

1. ✅ 导入必要的模块
2. ✅ 获取数据库会话
3. ✅ 使用 `ReminderService.create_reminder_log()` 创建提醒
4. ✅ 使用 `broadcast_reminder()` 发送实时通知
5. ✅ 处理可能的错误

遵循最佳实践，您的 App 就可以轻松地向用户发送通知了！

---

**需要帮助？** 查看项目文档或提交 Issue。

