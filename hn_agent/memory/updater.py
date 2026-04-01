"""
记忆更新器：使用 LLM 从对话中提取关键信息并更新记忆。

MemoryUpdater 负责调用 LLM 分析对话内容，提取用户偏好、关键事实等信息，
并将其合并到现有记忆中。
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    """LLM 客户端协议，用于记忆提取。"""

    async def ainvoke(self, input: Any) -> Any:
        """异步调用 LLM。"""
        ...


class MemoryUpdater:
    """使用 LLM 从对话中提取关键信息并更新记忆。

    Parameters
    ----------
    llm : LLMClient | None
        LLM 客户端实例。为 None 时使用 stub 实现（直接返回现有记忆）。
    """

    _EXTRACTION_PROMPT = (
        "你是一个记忆提取助手。请从以下对话中提取关键信息（用户偏好、重要事实、"
        "待办事项等），并将其合并到现有记忆中。\n\n"
        "现有记忆:\n{existing_memory}\n\n"
        "对话内容:\n{conversation}\n\n"
        "请输出更新后的完整记忆文本（纯文本，不要 Markdown 标题）:"
    )

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def extract_and_update(
        self,
        messages: list[Any],
        existing_memory: str,
    ) -> str:
        """使用 LLM 从对话中提取关键信息并更新记忆。

        Parameters
        ----------
        messages : list
            对话消息列表（BaseMessage 或类似对象）。
        existing_memory : str
            当前已有的记忆文本。

        Returns
        -------
        str
            更新后的记忆文本。
        """
        if not messages:
            return existing_memory

        if self._llm is None:
            logger.debug("LLM 未配置，返回现有记忆")
            return existing_memory

        conversation = self._format_messages(messages)
        prompt = self._EXTRACTION_PROMPT.format(
            existing_memory=existing_memory or "(空)",
            conversation=conversation,
        )

        try:
            result = await self._llm.ainvoke(prompt)
            # LLM 返回值可能是字符串或带 .content 属性的对象
            content = getattr(result, "content", None) or str(result)
            return content.strip()
        except Exception:
            logger.exception("LLM 记忆提取失败，保留现有记忆")
            return existing_memory

    @staticmethod
    def _format_messages(messages: list[Any]) -> str:
        """将消息列表格式化为对话文本。"""
        lines: list[str] = []
        for msg in messages:
            role = getattr(msg, "type", None) or getattr(msg, "role", "unknown")
            content = getattr(msg, "content", None) or str(msg)
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines)
