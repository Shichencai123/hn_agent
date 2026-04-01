"""护栏系统单元测试。"""

from __future__ import annotations

import pytest

from hn_agent.guardrails import (
    AuthorizationResult,
    GuardrailContext,
    GuardrailProvider,
    GuardrailRule,
    RuleBasedGuardrailProvider,
)


# ── 数据模型测试 ──────────────────────────────────────────


class TestAuthorizationResult:
    def test_authorized_default(self):
        result = AuthorizationResult(authorized=True)
        assert result.authorized is True
        assert result.reason is None

    def test_denied_with_reason(self):
        result = AuthorizationResult(authorized=False, reason="blocked")
        assert result.authorized is False
        assert result.reason == "blocked"


class TestGuardrailContext:
    def test_defaults(self):
        ctx = GuardrailContext()
        assert ctx.thread_id == ""
        assert ctx.user_id == ""
        assert ctx.agent_id == ""
        assert ctx.metadata == {}

    def test_custom_values(self):
        ctx = GuardrailContext(
            thread_id="t1", user_id="u1", agent_id="a1", metadata={"k": "v"}
        )
        assert ctx.thread_id == "t1"
        assert ctx.user_id == "u1"
        assert ctx.metadata == {"k": "v"}


class TestGuardrailRule:
    def test_defaults(self):
        rule = GuardrailRule(tool_pattern="*", action="allow")
        assert rule.tool_pattern == "*"
        assert rule.action == "allow"
        assert rule.conditions == {}

    def test_with_conditions(self):
        rule = GuardrailRule(
            tool_pattern="bash*",
            action="deny",
            conditions={"args_blocked": ["rm"]},
        )
        assert rule.conditions == {"args_blocked": ["rm"]}


# ── Protocol 兼容性测试 ───────────────────────────────────


class TestProtocolCompliance:
    def test_rule_based_provider_is_guardrail_provider(self):
        provider = RuleBasedGuardrailProvider(rules=[])
        assert isinstance(provider, GuardrailProvider)


# ── RuleBasedGuardrailProvider 测试 ──────────────────────


class TestRuleBasedGuardrailProvider:
    @pytest.fixture()
    def ctx(self) -> GuardrailContext:
        return GuardrailContext(thread_id="t1", user_id="u1")

    # -- 无规则时默认允许 --

    @pytest.mark.asyncio
    async def test_no_rules_allows(self, ctx: GuardrailContext):
        provider = RuleBasedGuardrailProvider(rules=[])
        result = await provider.check_authorization("bash", {}, ctx)
        assert result.authorized is True

    # -- 精确匹配 deny --

    @pytest.mark.asyncio
    async def test_exact_deny(self, ctx: GuardrailContext):
        rules = [GuardrailRule(tool_pattern="bash", action="deny")]
        provider = RuleBasedGuardrailProvider(rules=rules)
        result = await provider.check_authorization("bash", {}, ctx)
        assert result.authorized is False
        assert result.reason is not None
        assert "bash" in result.reason

    # -- 精确匹配 allow --

    @pytest.mark.asyncio
    async def test_exact_allow(self, ctx: GuardrailContext):
        rules = [GuardrailRule(tool_pattern="read", action="allow")]
        provider = RuleBasedGuardrailProvider(rules=rules)
        result = await provider.check_authorization("read", {}, ctx)
        assert result.authorized is True

    # -- 通配符匹配 --

    @pytest.mark.asyncio
    async def test_wildcard_deny(self, ctx: GuardrailContext):
        rules = [GuardrailRule(tool_pattern="sandbox.*", action="deny")]
        provider = RuleBasedGuardrailProvider(rules=rules)
        result = await provider.check_authorization("sandbox.exec", {}, ctx)
        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_wildcard_no_match_allows(self, ctx: GuardrailContext):
        rules = [GuardrailRule(tool_pattern="sandbox.*", action="deny")]
        provider = RuleBasedGuardrailProvider(rules=rules)
        result = await provider.check_authorization("read", {}, ctx)
        assert result.authorized is True

    # -- 规则顺序：首条匹配生效 --

    @pytest.mark.asyncio
    async def test_first_match_wins(self, ctx: GuardrailContext):
        rules = [
            GuardrailRule(tool_pattern="bash", action="allow"),
            GuardrailRule(tool_pattern="*", action="deny"),
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        # bash 匹配第一条 allow
        result = await provider.check_authorization("bash", {}, ctx)
        assert result.authorized is True
        # 其他工具匹配第二条 deny
        result = await provider.check_authorization("write", {}, ctx)
        assert result.authorized is False

    # -- 条件：args_blocked --

    @pytest.mark.asyncio
    async def test_args_blocked_condition_triggers(self, ctx: GuardrailContext):
        rules = [
            GuardrailRule(
                tool_pattern="bash",
                action="deny",
                conditions={"args_blocked": ["dangerous_flag"]},
            )
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        # 包含被禁止的参数 → deny
        result = await provider.check_authorization(
            "bash", {"dangerous_flag": True}, ctx
        )
        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_args_blocked_condition_not_triggered(self, ctx: GuardrailContext):
        rules = [
            GuardrailRule(
                tool_pattern="bash",
                action="deny",
                conditions={"args_blocked": ["dangerous_flag"]},
            )
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        # 不包含被禁止的参数 → 条件不满足，规则不匹配，默认允许
        result = await provider.check_authorization("bash", {"safe": True}, ctx)
        assert result.authorized is True

    # -- 条件：user_id --

    @pytest.mark.asyncio
    async def test_user_id_condition_match(self):
        rules = [
            GuardrailRule(
                tool_pattern="*",
                action="deny",
                conditions={"user_id": "blocked_user"},
            )
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        ctx = GuardrailContext(user_id="blocked_user")
        result = await provider.check_authorization("bash", {}, ctx)
        assert result.authorized is False

    @pytest.mark.asyncio
    async def test_user_id_condition_no_match(self):
        rules = [
            GuardrailRule(
                tool_pattern="*",
                action="deny",
                conditions={"user_id": "blocked_user"},
            )
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        ctx = GuardrailContext(user_id="normal_user")
        result = await provider.check_authorization("bash", {}, ctx)
        assert result.authorized is True

    # -- deny 原因包含条件信息 --

    @pytest.mark.asyncio
    async def test_deny_reason_includes_conditions(self, ctx: GuardrailContext):
        rules = [
            GuardrailRule(
                tool_pattern="bash",
                action="deny",
                conditions={"args_blocked": ["rm"]},
            )
        ]
        provider = RuleBasedGuardrailProvider(rules=rules)
        result = await provider.check_authorization("bash", {"rm": True}, ctx)
        assert result.authorized is False
        assert "条件" in result.reason

    # -- rules 属性返回副本 --

    def test_rules_property_returns_copy(self):
        rules = [GuardrailRule(tool_pattern="*", action="allow")]
        provider = RuleBasedGuardrailProvider(rules=rules)
        returned = provider.rules
        assert returned == rules
        assert returned is not provider._rules
