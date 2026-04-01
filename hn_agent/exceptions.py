"""
hn-agent 异常层次结构。

所有自定义异常均继承自 HarnessError，按功能域分组。
"""


class HarnessError(Exception):
    """所有 hn-agent 异常的基类。"""


# ── 配置相关 ──────────────────────────────────────────────


class ConfigurationError(HarnessError):
    """配置相关错误：缺失必需项、格式错误。"""

    def __init__(self, message: str = "", *, missing_fields: list[str] | None = None):
        self.missing_fields: list[str] = missing_fields or []
        if not message and self.missing_fields:
            message = f"缺失必需配置项: {', '.join(self.missing_fields)}"
        super().__init__(message)


# ── 模型工厂相关 ──────────────────────────────────────────


class UnsupportedProviderError(HarnessError):
    """不支持的模型提供商。"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        super().__init__(f"不支持的模型提供商: {provider_name}")


class CredentialError(HarnessError):
    """API 凭证缺失或无效。"""

    def __init__(self, provider_name: str, detail: str = ""):
        self.provider_name = provider_name
        msg = f"凭证错误 ({provider_name})"
        if detail:
            msg += f": {detail}"
        super().__init__(msg)


# ── 沙箱相关 ─────────────────────────────────────────────


class SandboxError(HarnessError):
    """沙箱执行错误基类。"""


class SandboxTimeoutError(SandboxError):
    """沙箱执行超时。"""


class PathEscapeError(SandboxError):
    """路径逃逸尝试。"""


# ── 技能系统相关 ──────────────────────────────────────────


class SkillValidationError(HarnessError):
    """技能文件验证失败。"""

    def __init__(self, message: str = "", *, errors: list[dict] | None = None):
        self.errors: list[dict] = errors or []
        super().__init__(message)


# ── 护栏系统相关 ──────────────────────────────────────────


class AuthorizationDeniedError(HarnessError):
    """护栏授权拒绝。"""

    def __init__(self, tool_name: str, reason: str = ""):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"授权拒绝 - 工具: {tool_name}, 原因: {reason}")


# ── MCP 相关 ─────────────────────────────────────────────


class MCPConnectionError(HarnessError):
    """MCP 服务器连接失败。"""


# ── 向量存储相关 ──────────────────────────────────────────


class VectorStoreError(HarnessError):
    """向量存储连接失败或查询超时。"""
