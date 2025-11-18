"""WebSocket 连接处理."""

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.timezone import now

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self) -> None:
        """初始化连接管理器."""
        self.active_connections: Set[WebSocket] = set()

    def has_active_connections(self) -> bool:
        """
        检查是否有活动的 WebSocket 连接.

        Returns:
            bool: 是否有活动连接
        """
        return len(self.active_connections) > 0

    async def connect(self, websocket: WebSocket) -> None:
        """
        接受新的 WebSocket 连接.

        Args:
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"新的 WebSocket 连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接.

        Args:
            websocket: WebSocket 连接对象
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        向指定连接发送消息.

        Args:
            message: 消息内容
            websocket: WebSocket 连接对象
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict) -> None:
        """
        向所有连接广播消息.

        Args:
            message: 消息字典
        """
        disconnected = set()
        message_text = json.dumps(message, ensure_ascii=False)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.add(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket 端点，用于实时通知.

    Args:
        websocket: WebSocket 连接对象
    """
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息（心跳检测等）
            data = await websocket.receive_text()
            logger.debug(f"收到 WebSocket 消息: {data}")
            # 可以在这里处理客户端发送的消息
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        manager.disconnect(websocket)


async def broadcast_reminder_async(reminder_data: dict) -> None:
    """
    异步广播提醒消息到所有连接的客户端.

    Args:
        reminder_data: 提醒数据字典
    """
    message = {
        "type": "reminder",
        "data": reminder_data,
        "timestamp": now().isoformat(),
    }
    await manager.broadcast(message)


def broadcast_reminder(reminder_data: dict) -> None:
    """
    广播提醒消息到所有连接的客户端（同步包装）.

    Args:
        reminder_data: 提醒数据字典
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_reminder_async(reminder_data))
        else:
            loop.run_until_complete(broadcast_reminder_async(reminder_data))
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        asyncio.run(broadcast_reminder_async(reminder_data))

