"""单元测试：异常层次结构。"""

import pytest

from hn_agent.exceptions import (
    AuthorizationDeniedError,
    ConfigurationError,
    CredentialError,
    HarnessError,
    MCPConnectionError,
    PathEscapeError,
    SandboxError,
    SandboxTimeoutError,
    SkillValidationError,
    UnsupportedProviderError,
    VectorStoreError,
)


class TestExceptionHierarchy:
    """验证所有异常均继承自 HarnessError。"""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            ConfigurationError,
            UnsupportedProviderError,
            CredentialError,
            SandboxError,
            SandboxTimeoutError,
            PathEscapeError,
            SkillValidationError,
            AuthorizationDeniedError,
            MCPConnectionError,
            VectorStoreError,
        ],
    )
    def test_all_exceptions_inherit_harness_error(self, exc_cls):
        assert issubclass(exc_cls, HarnessError)

    def test_sandbox_timeout_inherits_sandbox_error(self):
        assert issubclass(SandboxTimeoutError, SandboxError)

    def test_path_escape_inherits_sandbox_error(self):
        assert issubclass(PathEscapeError, SandboxError)
