"""护栏系统：工具调用前的授权检查机制。"""

from hn_agent.guardrails.builtin import GuardrailRule, RuleBasedGuardrailProvider
from hn_agent.guardrails.provider import (
    AuthorizationResult,
    GuardrailContext,
    GuardrailProvider,
)

__all__ = [
    "AuthorizationResult",
    "GuardrailContext",
    "GuardrailProvider",
    "GuardrailRule",
    "RuleBasedGuardrailProvider",
]
