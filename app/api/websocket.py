"""WebSocket 连接处理."""

import asyncio
import json
import logging
import threading
from typing import Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.timezone import now

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self) -> None:
        """初始化连接管理器."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = threading.Lock()
        self._main_event_loop: Optional[asyncio.AbstractEventLoop] = None

    def set_main_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        设置主事件循环（用于从后台线程调度任务）.

        Args:
            loop: 主事件循环
        """
        self._main_event_loop = loop

    def has_active_connections(self) -> bool:
        """
        检查是否有活动的 WebSocket 连接.

        Returns:
            bool: 是否有活动连接
        """
        with self._lock:
            return len(self.active_connections) > 0

    async def connect(self, websocket: WebSocket) -> None:
        """
        接受新的 WebSocket 连接.

        Args:
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        with self._lock:
            self.active_connections.add(websocket)
            # 存储主事件循环（第一次连接时）
            if self._main_event_loop is None:
                self._main_event_loop = asyncio.get_event_loop()
        logger.info(f"新的 WebSocket 连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接.

        Args:
            websocket: WebSocket 连接对象
        """
        with self._lock:
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

        # 获取连接快照以避免在迭代时修改
        with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
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
    # 尝试使用主事件循环（如果已设置）
    if manager._main_event_loop is not None and manager._main_event_loop.is_running():
        try:
            # 使用 run_coroutine_threadsafe 安全地在主事件循环中调度任务
            future = asyncio.run_coroutine_threadsafe(
                broadcast_reminder_async(reminder_data), manager._main_event_loop
            )

            # 添加异常处理回调
            def log_exception(fut: asyncio.Future) -> None:
                try:
                    fut.result()
                except Exception as e:
                    logger.error(f"广播提醒消息时出错: {e}")

            future.add_done_callback(log_exception)
            return
        except Exception as e:
            logger.warning(f"使用主事件循环广播失败，回退到默认方式: {e}")

    # 回退到原来的逻辑
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_reminder_async(reminder_data))
        else:
            loop.run_until_complete(broadcast_reminder_async(reminder_data))
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        asyncio.run(broadcast_reminder_async(reminder_data))
