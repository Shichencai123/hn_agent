"""反射系统单元测试。"""

from __future__ import annotations

import os
import sys
from types import ModuleType

import pytest

from hn_agent.reflection.resolvers import (
    resolve_class,
    resolve_module,
    resolve_variable,
)


# ── resolve_module ───────────────────────────────────────


class TestResolveModule:
    """resolve_module 动态导入模块。"""

    def test_stdlib_module(self):
        mod = resolve_module("os")
        assert isinstance(mod, ModuleType)
        assert mod is os

    def test_nested_stdlib_module(self):
        mod = resolve_module("os.path")
        assert isinstance(mod, ModuleType)
        assert hasattr(mod, "join")

    def test_project_module(self):
        mod = resolve_module("hn_agent.reflection.resolvers")
        assert isinstance(mod, ModuleType)
        assert hasattr(mod, "resolve_module")

    def test_nonexistent_module_raises(self):
        with pytest.raises(ModuleNotFoundError, match="no_such_module_xyz"):
            resolve_module("no_such_module_xyz")

    def test_nonexistent_nested_module_raises(self):
        with pytest.raises(ModuleNotFoundError, match="os.nonexistent_sub"):
            resolve_module("os.nonexistent_sub")


# ── resolve_class ────────────────────────────────────────


class TestResolveClass:
    """resolve_class 解析 'module.path:ClassName' 格式。"""

    def test_resolve_builtin_class(self):
        cls = resolve_class("collections:OrderedDict")
        from collections import OrderedDict

        assert cls is OrderedDict

    def test_resolve_exception_class(self):
        cls = resolve_class("hn_agent.exceptions:HarnessError")
        from hn_agent.exceptions import HarnessError

        assert cls is HarnessError

    def test_resolve_function_as_class(self):
        """resolve_class 也可以解析函数（函数也是模块属性）。"""
        fn = resolve_class("os.path:join")
        assert callable(fn)
        assert fn is os.path.join

    def test_nonexistent_class_raises_attribute_error(self):
        with pytest.raises(AttributeError, match="NoSuchClass"):
            resolve_class("os:NoSuchClass")

    def test_nonexistent_module_raises_module_not_found(self):
        with pytest.raises(ModuleNotFoundError, match="fake_module"):
            resolve_class("fake_module:SomeClass")

    def test_missing_colon_raises_value_error(self):
        with pytest.raises(ValueError, match=":"):
            resolve_class("os.path.join")

    def test_empty_attr_raises_value_error(self):
        with pytest.raises(ValueError, match="为空"):
            resolve_class("os:")

    def test_empty_module_raises_value_error(self):
        with pytest.raises(ValueError, match="为空"):
            resolve_class(":SomeClass")


# ── resolve_variable ─────────────────────────────────────


class TestResolveVariable:
    """resolve_variable 解析变量路径。"""

    def test_resolve_string_variable(self):
        sep = resolve_variable("os.path:sep")
        assert sep == os.path.sep

    def test_resolve_sys_variable(self):
        val = resolve_variable("sys:maxsize")
        assert val == sys.maxsize

    def test_resolve_project_variable(self):
        """解析项目内模块的 __all__ 变量。"""
        all_list = resolve_variable("hn_agent.reflection:__all__")
        assert isinstance(all_list, list)
        assert "resolve_module" in all_list

    def test_nonexistent_variable_raises_attribute_error(self):
        with pytest.raises(AttributeError, match="no_such_var"):
            resolve_variable("os:no_such_var")

    def test_nonexistent_module_raises_module_not_found(self):
        with pytest.raises(ModuleNotFoundError, match="nonexistent_pkg"):
            resolve_variable("nonexistent_pkg:some_var")

    def test_missing_colon_raises_value_error(self):
        with pytest.raises(ValueError, match=":"):
            resolve_variable("os.path.sep")


# ── __init__.py 公开接口 ─────────────────────────────────


class TestPublicInterface:
    """hn_agent.reflection 公开接口导出。"""

    def test_exports_available(self):
        from hn_agent import reflection

        assert hasattr(reflection, "resolve_module")
        assert hasattr(reflection, "resolve_class")
        assert hasattr(reflection, "resolve_variable")

    def test_all_contains_expected(self):
        import hn_agent.reflection as ref

        assert set(ref.__all__) == {
            "resolve_module",
            "resolve_class",
            "resolve_variable",
        }
