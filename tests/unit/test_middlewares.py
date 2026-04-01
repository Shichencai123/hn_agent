"""
中间件系统单元测试。

覆盖：Middleware Protocol、MiddlewareChain（正序 pre / 逆序 post）、
14 个中间件 stub、DEFAULT_MIDDLEWARE_ORDER、create_default_chain。
"""

from __future__ import annotations

import pytest

from hn_agent.agents.middlewares.base import Middleware
from hn_agent.agents.middlewares.chain import MiddlewareChain
from hn_agent.agents.middlewares import (
    DEFAULT_MIDDLEWARE_ORDER,
    create_default_chain,
    ThreadDataMiddleware,
    UploadsMiddleware,
    SandboxMiddleware,
    DanglingToolCallMiddleware,
    GuardrailMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    TitleMiddleware,
    MemoryMiddleware,
    ViewImageMiddleware,
    SubagentLimitMiddleware,
    ClarificationMiddleware,
    LoopDetectionMiddleware,
    TokenUsageMiddleware,
)


# ── 辅助：可追踪执行顺序的中间件 ─────────────────────────


class TrackingMiddleware:
    """记录 pre/post 调用顺序的中间件。"""

    def __init__(self, name: str, log: list[str]) -> None:
        self.name = name
        self._log = log

    async def pre_process(self, state, config):
        self._log.append(f"pre:{self.name}")
        return state

    async def post_process(self, state, config):
        self._log.append(f"post:{self.name}")
        return state


class StateModifyingMiddleware:
    """在 state 中追加标记的中间件。"""

    def __init__(self, tag: str) -> None:
        self.tag = tag

    async def pre_process(self, state, config):
        state.setdefault("tags", []).append(f"pre:{self.tag}")
        return state

    async def post_process(self, state, config):
        state.setdefault("tags", []).append(f"post:{self.tag}")
        return state


# ── Middleware Protocol 测试 ──────────────────────────────


class TestMiddlewareProtocol:
    def test_tracking_middleware_is_middleware(self):
        log: list[str] = []
        mw = TrackingMiddleware("x", log)
        assert isinstance(mw, Middleware)

    def test_all_14_middlewares_satisfy_protocol(self):
        classes = [
            ThreadDataMiddleware,
            UploadsMiddleware,
            SandboxMiddleware,
            DanglingToolCallMiddleware,
            GuardrailMiddleware,
            SummarizationMiddleware,
            TodoListMiddleware,
            TitleMiddleware,
            MemoryMiddleware,
            ViewImageMiddleware,
            SubagentLimitMiddleware,
            ClarificationMiddleware,
            LoopDetectionMiddleware,
            TokenUsageMiddleware,
        ]
        for cls in classes:
            instance = cls()
            assert isinstance(instance, Middleware), f"{cls.__name__} 不满足 Middleware Protocol"


# ── MiddlewareChain 测试 ─────────────────────────────────


class TestMiddlewareChain:
    @pytest.mark.asyncio
    async def test_run_pre_executes_in_forward_order(self):
        log: list[str] = []
        chain = MiddlewareChain([
            TrackingMiddleware("A", log),
            TrackingMiddleware("B", log),
            TrackingMiddleware("C", log),
        ])
        await chain.run_pre({}, {})
        assert log == ["pre:A", "pre:B", "pre:C"]

    @pytest.mark.asyncio
    async def test_run_post_executes_in_reverse_order(self):
        log: list[str] = []
        chain = MiddlewareChain([
            TrackingMiddleware("A", log),
            TrackingMiddleware("B", log),
            TrackingMiddleware("C", log),
        ])
        await chain.run_post({}, {})
        assert log == ["post:C", "post:B", "post:A"]

    @pytest.mark.asyncio
    async def test_state_flows_through_pre(self):
        chain = MiddlewareChain([
            StateModifyingMiddleware("1"),
            StateModifyingMiddleware("2"),
        ])
        result = await chain.run_pre({}, {})
        assert result["tags"] == ["pre:1", "pre:2"]

    @pytest.mark.asyncio
    async def test_state_flows_through_post(self):
        chain = MiddlewareChain([
            StateModifyingMiddleware("1"),
            StateModifyingMiddleware("2"),
        ])
        result = await chain.run_post({}, {})
        # post 逆序: 2 先执行, 然后 1
        assert result["tags"] == ["post:2", "post:1"]

    @pytest.mark.asyncio
    async def test_empty_chain_returns_state_unchanged(self):
        chain = MiddlewareChain([])
        state = {"key": "value"}
        assert await chain.run_pre(state, {}) == {"key": "value"}
        assert await chain.run_post(state, {}) == {"key": "value"}

    @pytest.mark.asyncio
    async def test_single_middleware_chain(self):
        log: list[str] = []
        chain = MiddlewareChain([TrackingMiddleware("only", log)])
        await chain.run_pre({}, {})
        await chain.run_post({}, {})
        assert log == ["pre:only", "post:only"]

    def test_init_with_none(self):
        chain = MiddlewareChain(None)
        assert chain.middlewares == []

    def test_init_with_list(self):
        log: list[str] = []
        mws = [TrackingMiddleware("a", log)]
        chain = MiddlewareChain(mws)
        assert len(chain.middlewares) == 1
        # 确保是副本，不是同一个列表
        assert chain.middlewares is not mws


# ── 14 个中间件 stub 测试 ────────────────────────────────


class TestMiddlewareStubs:
    """验证每个中间件 stub 的 pre/post 都能正常执行并返回 state。"""

    ALL_CLASSES = [
        ThreadDataMiddleware,
        UploadsMiddleware,
        SandboxMiddleware,
        DanglingToolCallMiddleware,
        GuardrailMiddleware,
        SummarizationMiddleware,
        TodoListMiddleware,
        TitleMiddleware,
        MemoryMiddleware,
        ViewImageMiddleware,
        SubagentLimitMiddleware,
        ClarificationMiddleware,
        LoopDetectionMiddleware,
        TokenUsageMiddleware,
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("cls", ALL_CLASSES, ids=lambda c: c.__name__)
    async def test_pre_process_returns_state(self, cls):
        mw = cls()
        state = {"messages": [], "title": None}
        result = await mw.pre_process(state, {})
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("cls", ALL_CLASSES, ids=lambda c: c.__name__)
    async def test_post_process_returns_state(self, cls):
        mw = cls()
        state = {"messages": [], "title": None}
        result = await mw.post_process(state, {})
        assert isinstance(result, dict)


# ── DEFAULT_MIDDLEWARE_ORDER 测试 ─────────────────────────


class TestDefaultMiddlewareOrder:
    def test_has_14_middlewares(self):
        assert len(DEFAULT_MIDDLEWARE_ORDER) == 14

    def test_order_matches_spec(self):
        expected = [
            ThreadDataMiddleware,
            UploadsMiddleware,
            SandboxMiddleware,
            DanglingToolCallMiddleware,
            GuardrailMiddleware,
            SummarizationMiddleware,
            TodoListMiddleware,
            TitleMiddleware,
            MemoryMiddleware,
            ViewImageMiddleware,
            SubagentLimitMiddleware,
            ClarificationMiddleware,
            LoopDetectionMiddleware,
            TokenUsageMiddleware,
        ]
        assert DEFAULT_MIDDLEWARE_ORDER == expected

    def test_no_duplicates(self):
        assert len(set(DEFAULT_MIDDLEWARE_ORDER)) == 14


# ── create_default_chain 测试 ────────────────────────────


class TestCreateDefaultChain:
    def test_returns_middleware_chain(self):
        chain = create_default_chain()
        assert isinstance(chain, MiddlewareChain)

    def test_chain_has_14_middlewares(self):
        chain = create_default_chain()
        assert len(chain.middlewares) == 14

    def test_chain_middleware_types_match_order(self):
        chain = create_default_chain()
        for mw, expected_cls in zip(chain.middlewares, DEFAULT_MIDDLEWARE_ORDER):
            assert isinstance(mw, expected_cls), (
                f"Expected {expected_cls.__name__}, got {type(mw).__name__}"
            )

    @pytest.mark.asyncio
    async def test_full_chain_pre_post_roundtrip(self):
        """默认链的 pre + post 应能正常执行不报错。"""
        chain = create_default_chain()
        state: dict = {"messages": [], "title": None}
        state = await chain.run_pre(state, {})
        state = await chain.run_post(state, {})
        assert isinstance(state, dict)


# ── 导出测试 ──────────────────────────────────────────────


class TestMiddlewareExports:
    def test_exports_middleware_protocol(self):
        from hn_agent.agents.middlewares import Middleware
        assert Middleware is not None

    def test_exports_middleware_chain(self):
        from hn_agent.agents.middlewares import MiddlewareChain
        assert MiddlewareChain is not None

    def test_exports_all_14_middleware_classes(self):
        from hn_agent.agents.middlewares import (
            ThreadDataMiddleware,
            UploadsMiddleware,
            SandboxMiddleware,
            DanglingToolCallMiddleware,
            GuardrailMiddleware,
            SummarizationMiddleware,
            TodoListMiddleware,
            TitleMiddleware,
            MemoryMiddleware,
            ViewImageMiddleware,
            SubagentLimitMiddleware,
            ClarificationMiddleware,
            LoopDetectionMiddleware,
            TokenUsageMiddleware,
        )
        assert all([
            ThreadDataMiddleware,
            UploadsMiddleware,
            SandboxMiddleware,
            DanglingToolCallMiddleware,
            GuardrailMiddleware,
            SummarizationMiddleware,
            TodoListMiddleware,
            TitleMiddleware,
            MemoryMiddleware,
            ViewImageMiddleware,
            SubagentLimitMiddleware,
            ClarificationMiddleware,
            LoopDetectionMiddleware,
            TokenUsageMiddleware,
        ])

    def test_exports_default_order(self):
        from hn_agent.agents.middlewares import DEFAULT_MIDDLEWARE_ORDER
        assert len(DEFAULT_MIDDLEWARE_ORDER) == 14

    def test_exports_create_default_chain(self):
        from hn_agent.agents.middlewares import create_default_chain
        assert callable(create_default_chain)
