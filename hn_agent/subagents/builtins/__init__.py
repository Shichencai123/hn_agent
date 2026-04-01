"""内置子 Agent：general_purpose 和 bash_agent。"""

from hn_agent.subagents.builtins.bash_agent import BASH_AGENT_DEF, bash_agent_handler
from hn_agent.subagents.builtins.general_purpose import (
    GENERAL_PURPOSE_DEF,
    general_purpose_handler,
)

__all__ = [
    "GENERAL_PURPOSE_DEF",
    "general_purpose_handler",
    "BASH_AGENT_DEF",
    "bash_agent_handler",
]
