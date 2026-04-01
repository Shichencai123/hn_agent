"""中间件模块：14 个有序中间件 + 链管理器。"""

from hn_agent.agents.middlewares.base import Middleware
from hn_agent.agents.middlewares.chain import MiddlewareChain
from hn_agent.agents.middlewares.thread_data import ThreadDataMiddleware
from hn_agent.agents.middlewares.uploads import UploadsMiddleware
from hn_agent.agents.middlewares.sandbox import SandboxMiddleware
from hn_agent.agents.middlewares.dangling_tool_call import DanglingToolCallMiddleware
from hn_agent.agents.middlewares.guardrail import GuardrailMiddleware
from hn_agent.agents.middlewares.summarization import SummarizationMiddleware
from hn_agent.agents.middlewares.todolist import TodoListMiddleware
from hn_agent.agents.middlewares.title import TitleMiddleware
from hn_agent.agents.middlewares.memory import MemoryMiddleware
from hn_agent.agents.middlewares.view_image import ViewImageMiddleware
from hn_agent.agents.middlewares.subagent_limit import SubagentLimitMiddleware
from hn_agent.agents.middlewares.clarification import ClarificationMiddleware
from hn_agent.agents.middlewares.loop_detection import LoopDetectionMiddleware
from hn_agent.agents.middlewares.token_usage import TokenUsageMiddleware

# 默认中间件执行顺序（pre: 正序, post: 逆序）
DEFAULT_MIDDLEWARE_ORDER: list[type] = [
    ThreadDataMiddleware,      # 1
    UploadsMiddleware,         # 2
    SandboxMiddleware,         # 3
    DanglingToolCallMiddleware,  # 4
    GuardrailMiddleware,       # 5
    SummarizationMiddleware,   # 6
    TodoListMiddleware,        # 7
    TitleMiddleware,           # 8
    MemoryMiddleware,          # 9
    ViewImageMiddleware,       # 10
    SubagentLimitMiddleware,   # 11
    ClarificationMiddleware,   # 12
    LoopDetectionMiddleware,   # 13
    TokenUsageMiddleware,      # 14
]


def create_default_chain() -> MiddlewareChain:
    """创建包含全部 14 个中间件的默认链。"""
    return MiddlewareChain([cls() for cls in DEFAULT_MIDDLEWARE_ORDER])


__all__ = [
    "Middleware",
    "MiddlewareChain",
    "ThreadDataMiddleware",
    "UploadsMiddleware",
    "SandboxMiddleware",
    "DanglingToolCallMiddleware",
    "GuardrailMiddleware",
    "SummarizationMiddleware",
    "TodoListMiddleware",
    "TitleMiddleware",
    "MemoryMiddleware",
    "ViewImageMiddleware",
    "SubagentLimitMiddleware",
    "ClarificationMiddleware",
    "LoopDetectionMiddleware",
    "TokenUsageMiddleware",
    "DEFAULT_MIDDLEWARE_ORDER",
    "create_default_chain",
]
