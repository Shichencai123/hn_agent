"""IM 渠道桥接单元测试。"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime

import pytest

from app.channels.base import Attachment, Channel, ChannelMessage
from app.channels.feishu import FeishuChannel
from app.channels.manager import ChannelManager
from app.channels.message_bus import MessageBus
from app.channels.service import ChannelService, ServiceStatus
from app.channels.slack import SlackChannel
from app.channels.store import ChannelStore
from app.channels.telegram import TelegramChannel


# ── ChannelMessage 数据模型 ──────────────────────────────


class TestChannelMessage:
    def test_defaults(self):
        msg = ChannelMessage(
            channel_type="test",
            channel_session_id="sess-1",
            sender_id="user-1",
            content="hello",
        )
        assert msg.channel_type == "test"
        assert msg.channel_session_id == "sess-1"
        assert msg.sender_id == "user-1"
        assert msg.content == "hello"
        assert msg.attachments == []
        assert isinstance(msg.timestamp, datetime)
        assert msg.raw_payload == {}

    def test_with_attachments(self):
        att = Attachment(type="image", url="https://example.com/img.png", filename="img.png", size=1024)
        msg = ChannelMessage(
            channel_type="slack",
            channel_session_id="C123",
            sender_id="U456",
            content="check this",
            attachments=[att],
        )
        assert len(msg.attachments) == 1
        assert msg.attachments[0].type == "image"
        assert msg.attachments[0].size == 1024


# ── ChannelStore ─────────────────────────────────────────


class TestChannelStore:
    @pytest.fixture
    def store(self, tmp_path):
        path = str(tmp_path / "store.json")
        return ChannelStore(store_path=path)

    def test_get_nonexistent(self, store):
        assert store.get_thread_id("feishu", "sess-1") is None

    def test_set_and_get(self, store):
        store.set_thread_id("feishu", "sess-1", "thread-abc")
        assert store.get_thread_id("feishu", "sess-1") == "thread-abc"

    def test_multiple_channels(self, store):
        store.set_thread_id("feishu", "sess-1", "t1")
        store.set_thread_id("slack", "sess-1", "t2")
        assert store.get_thread_id("feishu", "sess-1") == "t1"
        assert store.get_thread_id("slack", "sess-1") == "t2"

    def test_overwrite(self, store):
        store.set_thread_id("feishu", "sess-1", "t1")
        store.set_thread_id("feishu", "sess-1", "t2")
        assert store.get_thread_id("feishu", "sess-1") == "t2"

    def test_remove(self, store):
        store.set_thread_id("feishu", "sess-1", "t1")
        assert store.remove("feishu", "sess-1") is True
        assert store.get_thread_id("feishu", "sess-1") is None

    def test_remove_nonexistent(self, store):
        assert store.remove("feishu", "nope") is False

    def test_persistence(self, tmp_path):
        path = str(tmp_path / "store.json")
        s1 = ChannelStore(store_path=path)
        s1.set_thread_id("slack", "ch-1", "thread-x")

        s2 = ChannelStore(store_path=path)
        assert s2.get_thread_id("slack", "ch-1") == "thread-x"

    def test_list_sessions(self, store):
        store.set_thread_id("feishu", "s1", "t1")
        store.set_thread_id("feishu", "s2", "t2")
        sessions = store.list_sessions("feishu")
        assert sessions == {"s1": "t1", "s2": "t2"}

    def test_list_sessions_empty(self, store):
        assert store.list_sessions("unknown") == {}


# ── MessageBus ───────────────────────────────────────────


class TestMessageBus:
    @pytest.fixture
    def bus(self):
        return MessageBus()

    @pytest.mark.asyncio
    async def test_publish_subscribe(self, bus):
        received: list[ChannelMessage] = []

        async def handler(msg: ChannelMessage) -> None:
            received.append(msg)

        await bus.subscribe(handler)
        await bus.start()

        msg = ChannelMessage(
            channel_type="test",
            channel_session_id="s1",
            sender_id="u1",
            content="hi",
        )
        await bus.publish(msg)

        # Give the consume loop time to process
        await asyncio.sleep(0.2)
        await bus.stop()

        assert len(received) == 1
        assert received[0].content == "hi"

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, bus):
        results_a: list[str] = []
        results_b: list[str] = []

        async def handler_a(msg: ChannelMessage) -> None:
            results_a.append(msg.content)

        async def handler_b(msg: ChannelMessage) -> None:
            results_b.append(msg.content)

        await bus.subscribe(handler_a)
        await bus.subscribe(handler_b)
        await bus.start()

        msg = ChannelMessage(
            channel_type="test",
            channel_session_id="s1",
            sender_id="u1",
            content="broadcast",
        )
        await bus.publish(msg)
        await asyncio.sleep(0.2)
        await bus.stop()

        assert results_a == ["broadcast"]
        assert results_b == ["broadcast"]

    @pytest.mark.asyncio
    async def test_handler_error_does_not_block(self, bus):
        received: list[str] = []

        async def bad_handler(msg: ChannelMessage) -> None:
            raise RuntimeError("boom")

        async def good_handler(msg: ChannelMessage) -> None:
            received.append(msg.content)

        await bus.subscribe(bad_handler)
        await bus.subscribe(good_handler)
        await bus.start()

        msg = ChannelMessage(
            channel_type="test",
            channel_session_id="s1",
            sender_id="u1",
            content="ok",
        )
        await bus.publish(msg)
        await asyncio.sleep(0.2)
        await bus.stop()

        assert received == ["ok"]

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, bus):
        await bus.stop()  # should not raise
        await bus.start()
        await bus.stop()
        await bus.stop()  # double stop should be fine


# ── FeishuChannel ────────────────────────────────────────


class TestFeishuChannel:
    @pytest.fixture
    def channel(self):
        return FeishuChannel(app_id="test_id", app_secret="test_secret")

    def test_channel_type(self, channel):
        assert channel.channel_type == "feishu"

    @pytest.mark.asyncio
    async def test_receive_message(self, channel):
        payload = {
            "event": {
                "message": {
                    "chat_id": "oc_123",
                    "content": '{"text": "你好"}',
                    "message_type": "text",
                },
                "sender": {"sender_id": {"user_id": "ou_456"}},
            }
        }
        msg = await channel.receive_message(payload)
        assert msg.channel_type == "feishu"
        assert msg.channel_session_id == "oc_123"
        assert msg.sender_id == "ou_456"
        assert msg.content == "你好"
        assert msg.attachments == []

    @pytest.mark.asyncio
    async def test_receive_image_message(self, channel):
        payload = {
            "event": {
                "message": {
                    "chat_id": "oc_123",
                    "content": "{}",
                    "message_type": "image",
                    "image_key": "img_key_abc",
                },
                "sender": {"sender_id": {"user_id": "ou_456"}},
            }
        }
        msg = await channel.receive_message(payload)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].type == "image"

    @pytest.mark.asyncio
    async def test_receive_empty_payload(self, channel):
        msg = await channel.receive_message({})
        assert msg.channel_type == "feishu"
        assert msg.content == ""

    @pytest.mark.asyncio
    async def test_send_message(self, channel):
        # Stub — should not raise
        await channel.send_message("oc_123", "reply")

    @pytest.mark.asyncio
    async def test_setup_webhook(self, channel):
        await channel.setup_webhook("https://example.com/webhook")


# ── SlackChannel ─────────────────────────────────────────


class TestSlackChannel:
    @pytest.fixture
    def channel(self):
        return SlackChannel(bot_token="xoxb-test", signing_secret="secret")

    def test_channel_type(self, channel):
        assert channel.channel_type == "slack"

    @pytest.mark.asyncio
    async def test_receive_message(self, channel):
        payload = {
            "event": {
                "type": "message",
                "channel": "C0123456",
                "user": "U0123456",
                "text": "hello slack",
            }
        }
        msg = await channel.receive_message(payload)
        assert msg.channel_type == "slack"
        assert msg.channel_session_id == "C0123456"
        assert msg.sender_id == "U0123456"
        assert msg.content == "hello slack"

    @pytest.mark.asyncio
    async def test_receive_with_files(self, channel):
        payload = {
            "event": {
                "type": "message",
                "channel": "C01",
                "user": "U01",
                "text": "see file",
                "files": [
                    {
                        "filetype": "pdf",
                        "url_private": "https://files.slack.com/f.pdf",
                        "name": "doc.pdf",
                        "size": 2048,
                    }
                ],
            }
        }
        msg = await channel.receive_message(payload)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].filename == "doc.pdf"
        assert msg.attachments[0].size == 2048

    @pytest.mark.asyncio
    async def test_send_message(self, channel):
        await channel.send_message("C01", "reply")

    @pytest.mark.asyncio
    async def test_setup_webhook(self, channel):
        await channel.setup_webhook("https://example.com/slack/events")


# ── TelegramChannel ─────────────────────────────────────


class TestTelegramChannel:
    @pytest.fixture
    def channel(self):
        return TelegramChannel(bot_token="123:ABC")

    def test_channel_type(self, channel):
        assert channel.channel_type == "telegram"

    @pytest.mark.asyncio
    async def test_receive_text_message(self, channel):
        payload = {
            "message": {
                "chat": {"id": 12345},
                "from": {"id": 67890},
                "text": "hello telegram",
            }
        }
        msg = await channel.receive_message(payload)
        assert msg.channel_type == "telegram"
        assert msg.channel_session_id == "12345"
        assert msg.sender_id == "67890"
        assert msg.content == "hello telegram"

    @pytest.mark.asyncio
    async def test_receive_photo_message(self, channel):
        payload = {
            "message": {
                "chat": {"id": 111},
                "from": {"id": 222},
                "text": "",
                "photo": [
                    {"file_id": "small", "file_size": 100},
                    {"file_id": "large", "file_size": 5000},
                ],
            }
        }
        msg = await channel.receive_message(payload)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].url == "large"
        assert msg.attachments[0].size == 5000

    @pytest.mark.asyncio
    async def test_receive_document(self, channel):
        payload = {
            "message": {
                "chat": {"id": 111},
                "from": {"id": 222},
                "text": "",
                "document": {
                    "file_id": "doc_id",
                    "file_name": "report.pdf",
                    "file_size": 4096,
                },
            }
        }
        msg = await channel.receive_message(payload)
        assert len(msg.attachments) == 1
        assert msg.attachments[0].type == "file"
        assert msg.attachments[0].filename == "report.pdf"

    @pytest.mark.asyncio
    async def test_send_message(self, channel):
        await channel.send_message("12345", "reply")

    @pytest.mark.asyncio
    async def test_setup_webhook(self, channel):
        await channel.setup_webhook("https://example.com/tg/webhook")


# ── ChannelManager ───────────────────────────────────────


class TestChannelManager:
    @pytest.fixture
    def bus(self):
        return MessageBus()

    @pytest.fixture
    def store(self, tmp_path):
        return ChannelStore(store_path=str(tmp_path / "store.json"))

    @pytest.fixture
    def manager(self, bus, store):
        return ChannelManager(message_bus=bus, store=store)

    def test_register_channel(self, manager):
        ch = FeishuChannel()
        manager.register_channel(ch)
        assert "feishu" in manager.registered_channels
        assert manager.get_channel("feishu") is ch

    def test_unregister_channel(self, manager):
        ch = FeishuChannel()
        manager.register_channel(ch)
        manager.unregister_channel("feishu")
        assert "feishu" not in manager.registered_channels

    @pytest.mark.asyncio
    async def test_handle_message_creates_thread(self, manager, store):
        ch = FeishuChannel()
        manager.register_channel(ch)

        payload = {
            "event": {
                "message": {"chat_id": "oc_1", "content": '{"text": "hi"}', "message_type": "text"},
                "sender": {"sender_id": {"user_id": "ou_1"}},
            }
        }
        await manager.handle_message("feishu", payload)

        # Should have created a thread mapping
        thread_id = store.get_thread_id("feishu", "oc_1")
        assert thread_id is not None

    @pytest.mark.asyncio
    async def test_handle_message_unknown_channel(self, manager):
        # Should not raise, just log warning
        await manager.handle_message("unknown", {})

    @pytest.mark.asyncio
    async def test_send_response(self, manager):
        ch = SlackChannel()
        manager.register_channel(ch)
        # Stub — should not raise
        await manager.send_response("slack", "C01", "hello")

    @pytest.mark.asyncio
    async def test_send_response_unknown_channel(self, manager):
        # Should not raise
        await manager.send_response("unknown", "ch1", "hello")


# ── ChannelService ───────────────────────────────────────


class TestChannelService:
    @pytest.fixture
    def service(self, tmp_path):
        store = ChannelStore(store_path=str(tmp_path / "store.json"))
        bus = MessageBus()
        manager = ChannelManager(message_bus=bus, store=store)
        return ChannelService(manager=manager, message_bus=bus)

    def test_initial_status(self, service):
        assert service.status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_start_stop(self, service):
        await service.start()
        assert service.status == ServiceStatus.RUNNING

        await service.stop()
        assert service.status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_start_idempotent(self, service):
        await service.start()
        await service.start()  # should not raise
        assert service.status == ServiceStatus.RUNNING
        await service.stop()

    @pytest.mark.asyncio
    async def test_stop_idempotent(self, service):
        await service.stop()  # already stopped
        assert service.status == ServiceStatus.STOPPED

    @pytest.mark.asyncio
    async def test_health_check_running(self, service):
        service.manager.register_channel(FeishuChannel())
        await service.start()

        result = service.health_check()
        assert result.healthy is True
        assert result.status == ServiceStatus.RUNNING
        assert result.details["channel_count"] == 1
        assert "feishu" in result.details["registered_channels"]

        await service.stop()

    def test_health_check_stopped(self, service):
        result = service.health_check()
        assert result.healthy is False
        assert result.status == ServiceStatus.STOPPED
