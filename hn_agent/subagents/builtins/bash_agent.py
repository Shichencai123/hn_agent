"""
内置子 Agent：bash_agent — Bash 专家。

专门处理 Bash 命令执行和脚本编写相关的任务。
"""

from __future__ import annotations

from hn_agent.subagents.config import SubagentDefinition, SubagentTask, TaskType

BASH_AGENT_DEF = SubagentDefinition(
    name="bash_agent",
    description="Bash 专家子 Agent，专门处理命令行操作和脚本编写任务。",
    task_type=TaskType.IO,
    metadata={"category": "builtin"},
)


def bash_agent_handler(task: SubagentTask) -> str:
    """Bash 专家子 Agent 执行处理函数。

    桩实现：返回任务确认信息。实际实现将创建具有 Bash 工具的 LangGraph Agent。

    Args:
        task: 子 Agent 任务。

    Returns:
        执行结果字符串。
    """
    return (
        f"[bash_agent] 已处理任务: {task.instruction} "
        f"(thread={task.parent_thread_id})"
    )
