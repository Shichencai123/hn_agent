"""Lead Agent 核心：基于 LangGraph 的主 Agent 引擎。"""

from hn_agent.agents.lead_agent.agent import create_lead_agent
from hn_agent.agents.lead_agent.prompt import build_system_prompt

__all__ = ["create_lead_agent", "build_system_prompt"]
