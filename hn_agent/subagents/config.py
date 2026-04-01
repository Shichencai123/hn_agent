"""
子 Agent 系统数据模型：SubagentDefinition, SubagentTask, SubagentResult。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskType(str, Enum):
    """任务类型：区分 I/O 密集型和 CPU 密集型。"""

    IO = "io"
    CPU = "cpu"


@dataclass
class SubagentDefinition:
    """子 Agent 定义，描述一个可注册的子 Agent。"""

    name: str
    description: str
    task_type: TaskType = TaskType.IO
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubagentTask:
    """子 Agent 任务，描述一次委派请求。"""

    task_id: str
    agent_name: str
    instruction: str
    parent_thread_id: str
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @staticmethod
    def create(
        agent_name: str,
        instruction: str,
        parent_thread_id: str,
        context: dict[str, Any] | None = None,
    ) -> SubagentTask:
        """工厂方法：自动生成 task_id。"""
        return SubagentTask(
            task_id=uuid4().hex,
            agent_name=agent_name,
            instruction=instruction,
            parent_thread_id=parent_thread_id,
            context=context or {},
        )


@dataclass
class SubagentResult:
    """子 Agent 任务执行结果。"""

    task_id: str
    success: bool
    output: str
    error: str | None = None
