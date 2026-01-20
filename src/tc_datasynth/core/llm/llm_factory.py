from __future__ import annotations

"""
LLM 工厂：基于 TOML 配置动态加载模型。
"""

import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from langchain.chat_models import init_chat_model


class LlmFactory:
    """LLM 工厂，单例模式，基于配置文件管理模型实例。"""

    _instance: Optional["LlmFactory"] = None

    def __new__(cls, config_path: Path | str | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Path | str | None = None) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._models: Dict[str, Any] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._timeout: int = 360

        # 加载配置
        if config_path is None:
            config_path = Path(__file__).resolve().parents[4] / "configs" / "llm.toml"
        self._load_config(Path(config_path))

    def _load_config(self, config_path: Path) -> None:
        """从 TOML 文件加载配置。"""
        if not config_path.exists():
            raise FileNotFoundError(f"LLM 配置文件不存在: {config_path}")

        with config_path.open("rb") as f:
            raw = tomllib.load(f)

        # 全局设置
        settings = raw.get("settings", {})
        self._timeout = settings.get("timeout", 360)

        # 模型配置
        models = raw.get("models", {})
        for name, cfg in models.items():
            self._configs[name] = self._resolve_config(cfg)

    def _resolve_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """解析配置，将环境变量引用替换为实际值。"""
        resolved: Dict[str, Any] = {}

        for key, value in cfg.items():
            if key.endswith("_env"):
                # 将 base_url_env -> base_url，并从环境变量读取
                actual_key = key[:-4]  # 移除 _env 后缀
                env_value = os.getenv(value)
                if env_value is None:
                    raise ValueError(f"环境变量未设置: {value}")
                resolved[actual_key] = env_value
            elif isinstance(value, dict):
                # 递归处理嵌套字典（如 extra_body）
                resolved[key] = value
            else:
                resolved[key] = value

        # 添加全局 timeout
        if "timeout" not in resolved:
            resolved["timeout"] = self._timeout

        return resolved

    def __getitem__(self, model_name: str) -> Any:
        """通过模型名获取对应的模型实例（懒加载）。"""
        if model_name not in self._models:
            if model_name not in self._configs:
                available = ", ".join(self._configs.keys())
                raise KeyError(
                    f"模型 '{model_name}' 未在配置中定义。可用模型: {available}"
                )
            self._models[model_name] = init_chat_model(**self._configs[model_name])
        return self._models[model_name]

    def get(self, model_name: str, default: Any = None) -> Any:
        """安全获取模型，不存在时返回默认值。"""
        try:
            return self[model_name]
        except KeyError:
            return default

    def get_config(self, model_name: str) -> Dict[str, Any]:
        """获取模型的解析后配置。"""
        return self._configs.get(model_name, {})

    def list_models(self) -> list[str]:
        """列出所有可用模型名。"""
        return list(self._configs.keys())

    def reload(self, config_path: Path | str | None = None) -> None:
        """重新加载配置（清空缓存的模型实例）。"""
        self._models.clear()
        self._configs.clear()
        if config_path:
            self._load_config(Path(config_path))


# 模块级单例（延迟初始化）
_factory: Optional[LlmFactory] = None


def get_llm_factory(config_path: Path | str | None = None) -> LlmFactory:
    """获取 LLM 工厂单例。"""
    global _factory
    if _factory is None:
        _factory = LlmFactory(config_path)
    return _factory


def get_llm(model_name: str) -> Any:
    """快捷方式：获取指定模型。"""
    return get_llm_factory()[model_name]
