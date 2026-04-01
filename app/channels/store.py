"""ChannelStore：IM 会话 ID ↔ Agent 线程 ID 映射持久化。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class ChannelStore:
    """基于 JSON 文件的会话映射存储。

    将 (channel_type, channel_session_id) → thread_id 的映射
    持久化到 JSON 文件，支持原子写入。
    """

    def __init__(self, store_path: str = "./data/channels/store.json") -> None:
        self._store_path = Path(store_path)
        self._data: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """从 JSON 文件加载映射数据。"""
        if self._store_path.exists():
            try:
                with open(self._store_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """原子写入映射数据到 JSON 文件。"""
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._store_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, str(self._store_path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @staticmethod
    def _key(channel_type: str, channel_session_id: str) -> tuple[str, str]:
        return channel_type, channel_session_id

    def get_thread_id(
        self, channel_type: str, channel_session_id: str
    ) -> str | None:
        """查找 IM 会话对应的 Agent 线程 ID。"""
        channel_map = self._data.get(channel_type, {})
        return channel_map.get(channel_session_id)

    def set_thread_id(
        self, channel_type: str, channel_session_id: str, thread_id: str
    ) -> None:
        """设置 IM 会话与 Agent 线程 ID 的映射并持久化。"""
        if channel_type not in self._data:
            self._data[channel_type] = {}
        self._data[channel_type][channel_session_id] = thread_id
        self._save()

    def remove(self, channel_type: str, channel_session_id: str) -> bool:
        """移除映射，返回是否存在并移除成功。"""
        channel_map = self._data.get(channel_type, {})
        if channel_session_id in channel_map:
            del channel_map[channel_session_id]
            self._save()
            return True
        return False

    def list_sessions(self, channel_type: str) -> dict[str, str]:
        """列出指定渠道类型的所有会话映射。"""
        return dict(self._data.get(channel_type, {}))
