"""SlackChannel：Slack IM 渠道实现。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.channels.base import Attachment, Channel, ChannelMessage

logger = logging.getLogger(__name__)


class SlackChannel(Channel):
    """Slack 渠道实现（Stub）。

    解析 Slack Events API 载荷，发送消息到 Slack 频道，
    配置 Slack Event Subscriptions Webhook。
    """

    def __init__(self, bot_token: str = "", signing_secret: str = "") -> None:
        self._bot_token = bot_token
        self._signing_secret = signing_secret

    @property
    def channel_type(self) -> str:
        return "slack"

    async def receive_message(self, raw_payload: dict) -> ChannelMessage:
        """解析 Slack Events API 载荷。

        Slack 事件格式示例:
        {
            "event": {
                "type": "message",
                "channel": "C0123456",
                "user": "U0123456",
                "text": "hello",
                "ts": "1234567890.123456",
                "files": [...]
            }
        }
        """
        event = raw_payload.get("event", {})

        channel_id = event.get("channel", "")
        sender_id = event.get("user", "")
        content = event.get("text", "")

        # 解析附件
        attachments: list[Attachment] = []
        for file_info in event.get("files", []):
            attachments.append(
                Attachment(
                    type=file_info.get("filetype", "file"),
                    url=file_info.get("url_private", ""),
                    filename=file_info.get("name"),
                    size=file_info.get("size"),
                )
            )

        return ChannelMessage(
            channel_type=self.channel_type,
            channel_session_id=channel_id,
            sender_id=sender_id,
            content=content,
            attachments=attachments,
            timestamp=datetime.now(timezone.utc),
            raw_payload=raw_payload,
        )

    async def send_message(self, channel_id: str, content: str) -> None:
        """发送消息到 Slack 频道（Stub）。"""
        logger.info(
            "SlackChannel.send_message: channel_id=%s, content=%s",
            channel_id,
            content[:50],
        )

    async def setup_webhook(self, webhook_url: str) -> None:
        """配置 Slack Event Subscriptions Webhook（Stub）。"""
        logger.info("SlackChannel.setup_webhook: url=%s", webhook_url)
