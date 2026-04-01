"""Channel 抽象基类：定义 IM 渠道的统一接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Attachment:
    """消息附件。"""

    type: str  # image, file, audio, video
    url: str
    filename: str | None = None
    size: int | None = None


@dataclass
class ChannelMessage:
    """渠道消息：统一的跨平台消息模型。"""

    channel_type: str
    channel_session_id: str
    sender_id: str
    content: str
    attachments: list[Attachment] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_utcnow)
    raw_payload: dict[str, Any] = field(default_factory=dict)


class Channel(ABC):
    """IM 渠道抽象基类。

    每个 IM 平台（飞书、Slack、Telegram）需实现此接口，
    提供消息解析、响应发送和 Webhook 设置能力。
    """

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """渠道类型标识（如 feishu, slack, telegram）。"""
        ...

    @abstractmethod
    async def receive_message(self, raw_payload: dict) -> ChannelMessage:
        """解析平台原始 Webhook 载荷为统一 ChannelMessage。"""
        ...

    @abstractmethod
    async def send_message(self, channel_id: str, content: str) -> None:
        """向指定会话发送文本消息。"""
        ...

    @abstractmethod
    async def setup_webhook(self, webhook_url: str) -> None:
        """配置平台 Webhook 回调地址。"""
        ...
