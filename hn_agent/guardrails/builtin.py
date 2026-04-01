"""
护栏系统：内置规则引擎实现。

RuleBasedGuardrailProvider 基于配置规则进行授权检查。
规则按顺序评估，首条匹配的规则决定授权结果。
若无规则匹配，默认允许。
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Any

from hn_agent.guardrails.provider import AuthorizationResult, GuardrailContext


@dataclass
class GuardrailRule:
    """单条护栏规则。

    Attributes:
        tool_pattern: 工具名称匹配模式，支持 fnmatch 通配符（如 "bash*", "sandbox.*"）。
        action: 匹配后的动作，"allow" 或 "deny"。
        conditions: 附加条件字典，可包含 "args_blocked"（禁止的参数键列表）等。
    """

    tool_pattern: str
    action: str  # "allow" or "deny"
    conditions: dict[str, Any] = field(default_factory=dict)


class RuleBasedGuardrailProvider:
    """基于配置规则的授权检查实现。

    规则按列表顺序逐条评估：
    1. 工具名称通过 fnmatch 与 tool_pattern 匹配
    2. 若匹配且存在 conditions，检查附加条件
    3. 首条完全匹配的规则决定结果
    4. 无规则匹配时默认允许
    """

    def __init__(self, rules: list[GuardrailRule]) -> None:
        self._rules = list(rules)

    @property
    def rules(self) -> list[GuardrailRule]:
        return list(self._rules)

    async def check_authorization(
        self, tool_name: str, args: dict[str, Any], context: GuardrailContext
    ) -> AuthorizationResult:
        for rule in self._rules:
            if not fnmatch.fnmatch(tool_name, rule.tool_pattern):
                continue

            if not self._check_conditions(rule, tool_name, args, context):
                continue

            if rule.action == "deny":
                reason = self._build_deny_reason(rule, tool_name)
                return AuthorizationResult(authorized=False, reason=reason)

            # action == "allow"
            return AuthorizationResult(authorized=True)

        # 无规则匹配，默认允许
        return AuthorizationResult(authorized=True)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    @staticmethod
    def _check_conditions(
        rule: GuardrailRule,
        tool_name: str,
        args: dict[str, Any],
        context: GuardrailContext,
    ) -> bool:
        """检查规则的附加条件是否满足。"""
        conditions = rule.conditions
        if not conditions:
            return True

        # 条件：禁止的参数键
        args_blocked: list[str] | None = conditions.get("args_blocked")
        if args_blocked is not None:
            for key in args_blocked:
                if key in args:
                    return True
            # 没有命中任何被禁止的参数键 → 条件不满足
            return False

        # 条件：要求特定用户
        required_user: str | None = conditions.get("user_id")
        if required_user is not None:
            return context.user_id == required_user

        return True

    @staticmethod
    def _build_deny_reason(rule: GuardrailRule, tool_name: str) -> str:
        """构建拒绝原因描述。"""
        reason = f"工具 '{tool_name}' 被规则 '{rule.tool_pattern}' 拒绝"
        if rule.conditions:
            reason += f"（条件: {rule.conditions}）"
        return reason
