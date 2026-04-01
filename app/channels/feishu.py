"""FeishuChannel：飞书 IM 渠道实现。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.channels.base import Attachment, Channel, ChannelMessage

logger = logging.getLogger(__name__)


class FeishuChannel(Channel):
    """飞书渠道实现（Stub）。

    解析飞书 Webhook 事件载荷，发送消息到飞书会话，
    配置飞书事件订阅 Webhook。
    """

    def __init__(self, app_id: str = "", app_secret: str = "") -> None:
        self._app_id = app_id
        self._app_secret = app_secret

    @property
    def channel_type(self) -> str:
        return "feishu"

    async def receive_message(self, raw_payload: dict) -> ChannelMessage:
        """解析飞书 Webhook 事件载荷。

        飞书事件格式示例:
        {
            "event": {
                "message": {
                    "chat_id": "oc_xxx",
                    "message_id": "om_xxx",
                    "content": "{\"text\": \"hello\"}",
                    "message_type": "text"
                },
                "sender": {"sender_id": {"user_id": "ou_xxx"}}
            }
        }
        """
        event = raw_payload.get("event", {})
        message_data = event.get("message", {})
        sender_data = event.get("sender", {})

        chat_id = message_data.get("chat_id", "")
        sender_id = sender_data.get("sender_id", {}).get("user_id", "")

        # 解析消息内容
        content = ""
        raw_content = message_data.get("content", "")
        if isinstance(raw_content, str):
            import json
            try:
                parsed = json.loads(raw_content)
                content = parsed.get("text", raw_content)
            except (json.JSONDecodeError, TypeError):
                content = raw_content
        else:
            content = str(raw_content)

        # 解析附件
        attachments: list[Attachment] = []
        msg_type = message_data.get("message_type", "text")
        if msg_type == "image":
            image_key = message_data.get("image_key", "")
            if image_key:
                attachments.append(
                    Attachment(type="image", url=image_key, filename=None)
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
        """发送消息到飞书会话（Stub）。"""
        logger.info(
            "FeishuChannel.send_message: channel_id=%s, content=%s",
            channel_id,
            content[:50],
        )

    async def setup_webhook(self, webhook_url: str) -> None:
        """配置飞书事件订阅 Webhook（Stub）。"""
        logger.info("FeishuChannel.setup_webhook: url=%s", webhook_url)
