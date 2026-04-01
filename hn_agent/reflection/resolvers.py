"""
反射解析器：通过字符串路径动态加载模块、解析类和变量。

支持格式：
  - resolve_module("os.path")          → <module 'posixpath'>
  - resolve_class("os.path:join")      → <function join>  (也可用于类)
  - resolve_variable("os.path:sep")    → "/"
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any


def resolve_module(module_path: str) -> ModuleType:
    """动态导入模块，失败抛出 ModuleNotFoundError。

    Args:
        module_path: 合法的 Python 模块路径，如 ``"os.path"``。

    Returns:
        导入后的模块对象。

    Raises:
        ModuleNotFoundError: 模块路径不存在时抛出，包含路径信息。
    """
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            f"模块不存在: {module_path!r}"
        ) from None


def resolve_class(class_path: str) -> type:
    """解析 ``"module.path:ClassName"`` 格式的类路径，返回类对象。

    Args:
        class_path: 格式为 ``"module.path:ClassName"`` 的字符串。

    Returns:
        对应的类对象。

    Raises:
        ValueError: 路径格式不包含 ``:`` 分隔符。
        ModuleNotFoundError: 模块路径不存在。
        AttributeError: 类名在模块中不存在。
    """
    module_path, attr_name = _split_path(class_path)
    module = resolve_module(module_path)
    try:
        obj = getattr(module, attr_name)
    except AttributeError:
        raise AttributeError(
            f"模块 {module_path!r} 中不存在属性 {attr_name!r}"
        ) from None
    return obj


def resolve_variable(var_path: str) -> Any:
    """解析变量路径，返回变量值。

    路径格式与 :func:`resolve_class` 相同：``"module.path:variable_name"``。

    Args:
        var_path: 格式为 ``"module.path:variable_name"`` 的字符串。

    Returns:
        对应的变量值。

    Raises:
        ValueError: 路径格式不包含 ``:`` 分隔符。
        ModuleNotFoundError: 模块路径不存在。
        AttributeError: 变量名在模块中不存在。
    """
    module_path, attr_name = _split_path(var_path)
    module = resolve_module(module_path)
    try:
        return getattr(module, attr_name)
    except AttributeError:
        raise AttributeError(
            f"模块 {module_path!r} 中不存在属性 {attr_name!r}"
        ) from None


# ── 内部工具 ──────────────────────────────────────────────


def _split_path(path: str) -> tuple[str, str]:
    """将 ``"module.path:Name"`` 拆分为 ``(module_path, name)``。"""
    if ":" not in path:
        raise ValueError(
            f"路径格式错误，缺少 ':' 分隔符: {path!r}"
        )
    module_path, _, attr_name = path.partition(":")
    if not module_path or not attr_name:
        raise ValueError(
            f"路径格式错误，模块路径或属性名为空: {path!r}"
        )
    return module_path, attr_name
