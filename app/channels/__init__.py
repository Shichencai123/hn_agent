"""IM 渠道桥接：飞书 / Slack / Telegram 消息桥接。"""

from app.channels.base import Attachment, Channel, ChannelMessage
from app.channels.manager import ChannelManager
from app.channels.message_bus import MessageBus
from app.channels.service import ChannelService, HealthCheckResult, ServiceStatus
from app.channels.store import ChannelStore

__all__ = [
    "Attachment",
    "Channel",
    "ChannelManager",
    "ChannelMessage",
    "ChannelService",
    "ChannelStore",
    "HealthCheckResult",
    "MessageBus",
    "ServiceStatus",
]
