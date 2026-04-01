"""ChannelManager：渠道核心调度器。"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from app.channels.base import Channel, ChannelMessage
from app.channels.message_bus import MessageBus
from app.channels.store import ChannelStore

logger = logging.getLogger(__name__)


class ChannelManager:
    """管理多个 Channel 实例，调度消息处理流程。

    职责：
    - 注册/注销 Channel 实例
    - 接收 Webhook 消息并路由到对应 Channel
    - 查找或创建 Agent 线程
    - 将解析后的消息投递到 MessageBus
    """

    def __init__(
        self,
        message_bus: MessageBus | None = None,
        store: ChannelStore | None = None,
    ) -> None:
        self._channels: dict[str, Channel] = {}
        self._message_bus = message_bus or MessageBus()
        self._store = store or ChannelStore()

    def register_channel(self, channel: Channel) -> None:
        """注册一个 Channel 实例。"""
        self._channels[channel.channel_type] = channel

    def unregister_channel(self, channel_type: str) -> None:
        """注销一个 Channel 实例。"""
        self._channels.pop(channel_type, None)

    def get_channel(self, channel_type: str) -> Channel | None:
        """获取已注册的 Channel 实例。"""
        return self._channels.get(channel_type)

    @property
    def registered_channels(self) -> list[str]:
        """已注册的渠道类型列表。"""
        return list(self._channels.keys())

    async def handle_message(self, channel_type: str, payload: dict) -> None:
        """处理来自 IM 平台的 Webhook 消息。

        1. 查找对应的 Channel 实现
        2. 解析原始载荷为 ChannelMessage
        3. 查找或创建 Agent 线程 ID
        4. 投递消息到 MessageBus
        """
        channel = self._channels.get(channel_type)
        if channel is None:
            logger.warning("未注册的渠道类型: %s", channel_type)
            return

        try:
            message = await channel.receive_message(payload)
        except Exception:
            logger.exception("解析消息失败: channel_type=%s", channel_type)
            return

        # 查找或创建线程映射
        thread_id = self._store.get_thread_id(
            channel_type, message.channel_session_id
        )
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            self._store.set_thread_id(
                channel_type, message.channel_session_id, thread_id
            )

        await self._message_bus.publish(message)

    async def send_response(
        self, channel_type: str, channel_id: str, content: str
    ) -> None:
        """通过对应 Channel 发送响应消息。"""
        channel = self._channels.get(channel_type)
        if channel is None:
            logger.warning("未注册的渠道类型: %s", channel_type)
            return
        await channel.send_message(channel_id, content)
