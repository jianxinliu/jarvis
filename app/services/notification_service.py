"""系统通知服务."""

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """系统通知服务类."""

    @staticmethod
    def send_notification(
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: str = "default",
    ) -> bool:
        """
        发送系统通知.

        Args:
            title: 通知标题
            message: 通知内容
            subtitle: 通知副标题（可选）
            sound: 通知声音（默认 "default"）

        Returns:
            bool: 是否成功发送
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            return NotificationService._send_macos_notification(
                title=title, message=message, subtitle=subtitle, sound=sound
            )
        elif system == "Linux":
            return NotificationService._send_linux_notification(
                title=title, message=message
            )
        elif system == "Windows":
            return NotificationService._send_windows_notification(
                title=title, message=message
            )
        else:
            logger.warning(f"不支持的操作系统: {system}")
            return False

    @staticmethod
    def _send_macos_notification(
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: str = "default",
    ) -> bool:
        """
        发送 macOS 系统通知（使用 osascript）.

        Args:
            title: 通知标题
            message: 通知内容
            subtitle: 通知副标题
            sound: 通知声音

        Returns:
            bool: 是否成功发送
        """
        try:
            # 构建 AppleScript 命令
            # 转义特殊字符
            message_escaped = message.replace('"', '\\"').replace('\\', '\\\\')
            title_escaped = title.replace('"', '\\"').replace('\\', '\\\\')
            
            script = f'display notification "{message_escaped}" with title "{title_escaped}"'
            if subtitle:
                subtitle_escaped = subtitle.replace('"', '\\"').replace('\\', '\\\\')
                script += f' subtitle "{subtitle_escaped}"'
            if sound:
                script += f' sound name "{sound}"'

            # 执行 AppleScript
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                logger.info(f"macOS 通知已发送: {title}")
                return True
            else:
                logger.error(f"发送 macOS 通知失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("发送 macOS 通知超时")
            return False
        except Exception as e:
            logger.error(f"发送 macOS 通知时出错: {e}", exc_info=True)
            return False

    @staticmethod
    def _send_linux_notification(title: str, message: str) -> bool:
        """
        发送 Linux 系统通知（使用 notify-send）.

        Args:
            title: 通知标题
            message: 通知内容

        Returns:
            bool: 是否成功发送
        """
        try:
            result = subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.info(f"Linux 通知已发送: {title}")
                return True
            else:
                logger.error(f"发送 Linux 通知失败: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.warning("未找到 notify-send 命令，请安装 libnotify-bin")
            return False
        except Exception as e:
            logger.error(f"发送 Linux 通知时出错: {e}", exc_info=True)
            return False

    @staticmethod
    def _send_windows_notification(title: str, message: str) -> bool:
        """
        发送 Windows 系统通知（使用 plyer）.

        Args:
            title: 通知标题
            message: 通知内容

        Returns:
            bool: 是否成功发送
        """
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="Jarvis",
                timeout=10,
            )
            logger.info(f"Windows 通知已发送: {title}")
            return True
        except ImportError:
            logger.warning("未安装 plyer，无法发送 Windows 通知")
            return False
        except Exception as e:
            logger.error(f"发送 Windows 通知时出错: {e}", exc_info=True)
            return False

