# 反射系统深度分析

## 1. 功能概述

反射系统为 HN-Agent 提供通过字符串路径动态加载 Python 模块、解析类和变量的能力。支持三种解析模式：`resolve_module("os.path")` 导入模块、`resolve_class("module:ClassName")` 解析类/函数、`resolve_variable("module:var_name")` 获取变量值。路径格式统一使用 `"module.path:attribute_name"` 的冒号分隔语法。

## 2. 核心调用链

```
resolve_class("hn_agent.models.factory:create_model")
  → _split_path(path)                           # 分离 module_path 和 attr_name
  → resolve_module("hn_agent.models.factory")    # importlib.import_module()
  → getattr(module, "create_model")              # 获取属性
```

## 3. 关键代码位置索引

| 文件 | 关键内容 |
|------|---------|
| `hn_agent/reflection/resolvers.py` | resolve_module/resolve_class/resolve_variable |
