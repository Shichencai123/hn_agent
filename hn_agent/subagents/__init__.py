"""子 Agent 系统：异步任务委派和双线程池并发执行。"""

from hn_agent.subagents.config import (
    SubagentDefinition,
    SubagentResult,
    SubagentTask,
    TaskType,
)
from hn_agent.subagents.executor import SubagentExecutor
from hn_agent.subagents.registry import SubagentRegistry

__all__ = [
    "SubagentDefinition",
    "SubagentResult",
    "SubagentTask",
    "TaskType",
    "SubagentExecutor",
    "SubagentRegistry",
]
