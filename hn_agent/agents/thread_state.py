"""线程状态 Schema：Agent 运行时的状态定义，包含自定义 reducer。"""

from __future__ import annotations

import operator
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Annotated, Any

from langgraph.graph import MessagesState
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    message_to_dict,
)


# ── 数据模型 ─────────────────────────────────────────────


@dataclass
class Artifact:
    """Agent 生成的 artifact（代码、文档等）。"""

    id: str
    type: str
    title: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """序列化为可 JSON 化的字典。"""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Artifact:
        """从字典反序列化。"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
        return cls(
            id=data["id"],
            type=data["type"],
            title=data["title"],
            content=data["content"],
            created_at=created_at,
        )


@dataclass
class ImageData:
    """Agent 生成或引用的图片数据。"""

    id: str
    url: str
    alt_text: str
    data: bytes | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为可 JSON 化的字典。"""
        import base64

        result: dict[str, Any] = {
            "id": self.id,
            "url": self.url,
            "alt_text": self.alt_text,
        }
        if self.data is not None:
            result["data"] = base64.b64encode(self.data).decode("ascii")
        else:
            result["data"] = None
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ImageData:
        """从字典反序列化。"""
        import base64

        raw = data.get("data")
        decoded: bytes | None = None
        if isinstance(raw, str):
            decoded = base64.b64decode(raw)
        elif isinstance(raw, bytes):
            decoded = raw
        return cls(
            id=data["id"],
            url=data["url"],
            alt_text=data["alt_text"],
            data=decoded,
        )


# ── Reducer ──────────────────────────────────────────────


def artifacts_reducer(
    existing: list[Artifact], new: list[Artifact]
) -> list[Artifact]:
    """自定义 reducer：增量追加 + 按 ID 更新。

    - 如果 new 中的 artifact ID 已存在于 existing，则替换（更新）。
    - 否则追加到末尾。
    """
    by_id: dict[str, int] = {a.id: idx for idx, a in enumerate(existing)}
    result = list(existing)
    for artifact in new:
        if artifact.id in by_id:
            result[by_id[artifact.id]] = artifact
        else:
            by_id[artifact.id] = len(result)
            result.append(artifact)
    return result


# ── ThreadState ──────────────────────────────────────────


class ThreadState(MessagesState):
    """Agent 运行时线程状态 Schema。

    继承 MessagesState 获得 messages 字段（使用 add_messages reducer）。
    额外字段通过 Annotated 指定 reducer 保证并发修改的一致性。
    """

    artifacts: Annotated[list[Artifact], artifacts_reducer]
    images: Annotated[list[ImageData], operator.add]
    title: str | None
    thread_data: dict[str, Any]


# ── JSON 序列化 / 反序列化 ────────────────────────────────


def thread_state_to_json(state: dict[str, Any]) -> str:
    """将 ThreadState 字典序列化为 JSON 字符串。"""
    return json.dumps(_state_to_serializable(state), ensure_ascii=False)


def thread_state_from_json(json_str: str) -> dict[str, Any]:
    """从 JSON 字符串反序列化为 ThreadState 兼容的字典。"""
    raw = json.loads(json_str)
    return _state_from_serializable(raw)


def _state_to_serializable(state: dict[str, Any]) -> dict[str, Any]:
    """将 state 字典转换为纯 JSON 可序列化的字典。"""
    result: dict[str, Any] = {}

    # messages
    if "messages" in state:
        result["messages"] = [message_to_dict(m) for m in state["messages"]]

    # artifacts
    if "artifacts" in state:
        result["artifacts"] = [a.to_dict() for a in state["artifacts"]]

    # images
    if "images" in state:
        result["images"] = [img.to_dict() for img in state["images"]]

    # title
    if "title" in state:
        result["title"] = state["title"]

    # thread_data
    if "thread_data" in state:
        result["thread_data"] = state["thread_data"]

    return result


def _state_from_serializable(raw: dict[str, Any]) -> dict[str, Any]:
    """从纯字典恢复为包含领域对象的 state 字典。"""
    result: dict[str, Any] = {}

    # messages
    if "messages" in raw:
        result["messages"] = messages_from_dict(raw["messages"])

    # artifacts
    if "artifacts" in raw:
        result["artifacts"] = [Artifact.from_dict(a) for a in raw["artifacts"]]

    # images
    if "images" in raw:
        result["images"] = [ImageData.from_dict(img) for img in raw["images"]]

    # title
    if "title" in raw:
        result["title"] = raw["title"]

    # thread_data
    if "thread_data" in raw:
        result["thread_data"] = raw["thread_data"]

    return result
