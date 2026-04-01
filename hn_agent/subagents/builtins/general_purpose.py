"""
内置子 Agent：general_purpose — 通用 Agent。

处理通用任务委派，适用于不需要特定专业能力的子任务。
"""

from __future__ import annotations

from hn_agent.subagents.config import SubagentDefinition, SubagentTask, TaskType

GENERAL_PURPOSE_DEF = SubagentDefinition(
    name="general_purpose",
    description="通用子 Agent，处理不需要特定专业能力的通用子任务。",
    task_type=TaskType.IO,
    metadata={"category": "builtin"},
)


def general_purpose_handler(task: SubagentTask) -> str:
    """通用子 Agent 执行处理函数。

    桩实现：返回任务确认信息。实际实现将创建独立的 LangGraph Agent 进行推理。

    Args:
        task: 子 Agent 任务。

    Returns:
        执行结果字符串。
    """
    return (
        f"[general_purpose] 已处理任务: {task.instruction} "
        f"(thread={task.parent_thread_id})"
    )
