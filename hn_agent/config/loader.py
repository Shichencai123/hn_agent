"""
配置加载器：支持 YAML/JSON 加载、环境变量覆盖。

环境变量使用 HN_AGENT_ 前缀命名空间，双下划线分隔嵌套层级。
例如: HN_AGENT_APP__DEBUG=true → config["app"]["debug"] = "true"
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from hn_agent.config.models import AppConfig
from hn_agent.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

_ENV_PREFIX = "HN_AGENT_"
_ENV_SEP = "__"


class ConfigLoader:
    """统一配置加载器。

    支持从 YAML/JSON 文件加载配置，并用 HN_AGENT_ 前缀的环境变量覆盖。
    """

    def load(self, config_path: str) -> AppConfig:
        """从指定路径加载配置文件，支持 YAML/JSON 格式。

        Args:
            config_path: 配置文件路径（.yaml/.yml/.json）。

        Returns:
            解析后的 AppConfig 对象。

        Raises:
            ConfigurationError: 文件不存在、格式不支持或必需项缺失。
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(f"配置文件不存在: {config_path}")

        raw = self._read_file(path)
        raw = self._apply_env_overrides(raw)
        return self._parse_config(raw)

    def load_from_dict(self, data: dict[str, Any]) -> AppConfig:
        """从字典加载配置（用于测试和编程式配置）。"""
        data = self._apply_env_overrides(data)
        return self._parse_config(data)

    def _read_file(self, path: Path) -> dict[str, Any]:
        """读取并解析配置文件。"""
        suffix = path.suffix.lower()
        content = path.read_text(encoding="utf-8")

        if suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        elif suffix == ".json":
            data = json.loads(content)
        else:
            raise ConfigurationError(f"不支持的配置文件格式: {suffix}")

        if not isinstance(data, dict):
            raise ConfigurationError("配置文件内容必须是字典格式")

        return data

    def _apply_env_overrides(self, config: dict[str, Any]) -> dict[str, Any]:
        """用 HN_AGENT_ 前缀的环境变量覆盖配置项。

        环境变量命名规则:
            HN_AGENT_<SECTION>__<KEY> → config[section][key]
            例如: HN_AGENT_APP__DEBUG=true → config["app"]["debug"] = "true"
        """
        config = dict(config)  # shallow copy

        for key, value in os.environ.items():
            if not key.startswith(_ENV_PREFIX):
                continue

            # 去掉前缀，按双下划线分割为路径
            parts = key[len(_ENV_PREFIX) :].lower().split(_ENV_SEP)
            if not parts or not parts[0]:
                continue

            self._set_nested(config, parts, value)

        return config

    @staticmethod
    def _set_nested(data: dict[str, Any], keys: list[str], value: str) -> None:
        """在嵌套字典中按路径设置值。"""
        current = data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def _parse_config(self, raw: dict[str, Any]) -> AppConfig:
        """将原始字典解析为 AppConfig，处理未知键和验证错误。"""
        # 过滤未知顶层键并记录警告
        known_fields = set(AppConfig.model_fields.keys())
        unknown_keys = set(raw.keys()) - known_fields
        for uk in unknown_keys:
            logger.warning("忽略未知配置项: %s", uk)

        filtered = {k: v for k, v in raw.items() if k in known_fields}

        try:
            return AppConfig.model_validate(filtered)
        except ValidationError as exc:
            missing: list[str] = []
            for error in exc.errors():
                if error["type"] == "missing":
                    field_path = ".".join(str(p) for p in error["loc"])
                    missing.append(field_path)
            if missing:
                raise ConfigurationError(missing_fields=missing) from exc
            raise ConfigurationError(str(exc)) from exc
