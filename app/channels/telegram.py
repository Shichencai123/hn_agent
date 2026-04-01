"""TelegramChannel：Telegram IM 渠道实现。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.channels.base import Attachment, Channel, ChannelMessage

logger = logging.getLogger(__name__)


class TelegramChannel(Channel):
    """Telegram 渠道实现（Stub）。

    解析 Telegram Bot API Webhook 载荷，发送消息到 Telegram 聊天，
    配置 Telegram Bot Webhook。
    """

    def __init__(self, bot_token: str = "") -> None:
        self._bot_token = bot_token

    @property
    def channel_type(self) -> str:
        return "telegram"

    async def receive_message(self, raw_payload: dict) -> ChannelMessage:
        """解析 Telegram Bot API Webhook 载荷。

        Telegram Update 格式示例:
        {
            "message": {
                "chat": {"id": 123456},
                "from": {"id": 789012},
                "text": "hello",
                "photo": [...],
                "document": {...}
            }
        }
        """
        message_data = raw_payload.get("message", {})
        chat = message_data.get("chat", {})
        sender = message_data.get("from", {})

        chat_id = str(chat.get("id", ""))
        sender_id = str(sender.get("id", ""))
        content = message_data.get("text", "")

        # 解析附件
        attachments: list[Attachment] = []
        photos = message_data.get("photo", [])
        if photos:
            # Telegram 返回多个尺寸，取最大的
            largest = max(photos, key=lambda p: p.get("file_size", 0)) if photos else {}
            attachments.append(
                Attachment(
                    type="image",
                    url=largest.get("file_id", ""),
                    filename=None,
                    size=largest.get("file_size"),
                )
            )

        document = message_data.get("document")
        if document:
            attachments.append(
                Attachment(
                    type="file",
                    url=document.get("file_id", ""),
                    filename=document.get("file_name"),
                    size=document.get("file_size"),
                )
            )

        return ChannelMessage(
            channel_type=self.channel_type,
            channel_session_id=chat_id,
            sender_id=sender_id,
            content=content,
            attachments=attachments,
            timestamp=datetime.now(timezone.utc),
            raw_payload=raw_payload,
        )

    async def send_message(self, channel_id: str, content: str) -> None:
        """发送消息到 Telegram 聊天（Stub）。"""
        logger.info(
            "TelegramChannel.send_message: channel_id=%s, content=%s",
            channel_id,
            content[:50],
        )

    async def setup_webhook(self, webhook_url: str) -> None:
        """配置 Telegram Bot Webhook（Stub）。"""
        logger.info("TelegramChannel.setup_webhook: url=%s", webhook_url)
