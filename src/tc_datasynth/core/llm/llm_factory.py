from __future__ import annotations

from dataclasses import dataclass, field
import os
import tomllib
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from collections.abc import MutableMapping

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from loguru import logger
from langchain_core.language_models import BaseChatModel
from tqdm import tqdm

from tc_datasynth.utilities.tiny_tool import format_dict


@dataclass(slots=True)
class ModelCheckResult:
    """单模型校验结果。"""

    model_name: str
    ok: bool
    stage: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class LlmFactory(MutableMapping[str, BaseChatModel]):
    """LLM 工厂，单例模式，基于配置文件管理模型实例。实现标准字典接口。"""

    _instance: Optional["LlmFactory"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        config_path: Path | str | None = None,
        *,
        check_all: bool = False,
        env_path: Path | str | None = None,
        dotenv_override: bool = True,
    ) -> None:
        """
        初始化 LLM 工厂。

        参数:
            config_path: 配置文件路径
            skip_invalid: 是否跳过无效配置（True 时记录错误但继续加载其他模型）
            preload_all: 是否预加载所有模型（False 时恢复懒加载）
        """
        if self._initialized:
            return

        self._initialized = True
        self._models: Dict[str, BaseChatModel] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._failed_configs: Dict[str, str] = {}  # 记录加载失败的模型
        self._timeout: int = 360
        self._config_path: Optional[Path] = None
        self._env_path: Optional[Path] = None
        self._check_all = check_all
        self._preload_all = False
        self._dotenv_override = dotenv_override

        # 加载配置
        if config_path is None:
            config_path = Path(__file__).resolve().parents[4] / "configs" / "llm.toml"
        self._config_path = Path(config_path)
        self._env_path = self._resolve_env_path(env_path, config_path=self._config_path)
        self._load_env_file(self._env_path, override=dotenv_override)
        self._load_config(self._config_path)

        # 校验所有模型，若存在无效配置则给出提示
        if self._check_all:
            self.check_models()

    def check_models(self) -> None:
        logs = {
            "summary": {"total": len(self), "OK": 0, "ERROR": 0},
            "detail": {"OK": [], "ERROR": {}},
        }
        pbar = tqdm(total=len(self), desc="检查模型连通性", unit="模型")
        for model_name in self.keys():
            result = self.check_only(model_name)
            if result.ok:
                logs["summary"]["OK"] += 1
                logs["detail"]["OK"].append(model_name)
            else:
                logs["summary"]["ERROR"] += 1
                logs["detail"]["ERROR"][model_name] = (
                    f"{result.stage}: {result.message}"
                )
            pbar.update(1)
        pbar.close()
        logger.info("【模型连通性检查结果】：\n" + format_dict(logs, mode="yaml"))

    def check_only(self, model_name: str) -> ModelCheckResult:
        """仅检查单个模型，避免全量初始化与全量连通测试。"""
        normalized_name = model_name.replace("_", "-")
        if normalized_name not in self._configs:
            available = ", ".join(sorted(self._configs.keys()))
            return ModelCheckResult(
                model_name=normalized_name,
                ok=False,
                stage="config",
                message=f"模型未在配置中定义: {normalized_name}",
                details={"available_models": available},
            )

        try:
            model = self[normalized_name]
        except Exception as exc:
            return ModelCheckResult(
                model_name=normalized_name,
                ok=False,
                stage="load",
                message=str(exc),
            )

        try:
            list(model.stream("这是一个连通测试消息，若能收到请快速回复1表示成功！"))
        except Exception as exc:
            return ModelCheckResult(
                model_name=normalized_name,
                ok=False,
                stage="ping",
                message=str(exc),
            )

        return ModelCheckResult(
            model_name=normalized_name,
            ok=True,
            stage="ping",
            message="模型连通性检查通过",
            details={"loaded": self.is_loaded(normalized_name)},
        )

    def _load_config(self, config_path: Path) -> None:
        """从 TOML 文件加载配置。"""
        if not config_path.exists():
            raise FileNotFoundError(f"LLM 配置文件不存在: {config_path}")

        try:
            with config_path.open("rb") as f:
                raw = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"TOML 配置文件解析失败: {config_path}\n错误: {e}")

        # 全局设置
        settings = raw.get("settings", {})
        self._timeout = settings.get("timeout", 360)

        # 模型配置
        models = raw.get("models", {})
        if not models:
            logger.warning(f"配置文件中未找到任何模型定义: {config_path}")
            return

        # 统计加载结果

        for name, cfg in models.items():
            try:
                # 规范化模型名称：将下划线转为连字符
                normalized_name = name.replace("_", "-")

                self._configs[normalized_name] = self._resolve_config(
                    normalized_name, cfg
                )
                logger.debug(f"已加载模型配置: {normalized_name}")
                # 如果原始名称与规范化名称不同，添加别名
                if name != normalized_name:
                    self._configs[name] = self._configs[normalized_name]
                    logger.debug(f"  添加别名: {name} -> {normalized_name}")
            except Exception as e:
                error_msg = str(e)
                self._failed_configs[name] = error_msg
                logger.error(f"加载模型 '{name}' 配置失败: {error_msg}")
                raise

    @staticmethod
    def _resolve_env_path(
        env_path: Path | str | None, *, config_path: Path
    ) -> Path:
        """解析 env 文件路径，优先级：参数 > llm.toml settings.env_path > 默认值。"""
        if env_path is not None:
            return Path(env_path)

        settings = LlmFactory._read_settings(config_path)
        configured = settings.get("env_path")
        if isinstance(configured, str) and configured.strip():
            configured_path = Path(configured.strip())
            if not configured_path.is_absolute():
                # 优先支持“相对于项目根目录”的写法，兼容旧的“相对于 llm.toml”写法。
                project_relative = LlmFactory._project_root() / configured_path
                config_relative = config_path.parent / configured_path
                if project_relative.exists():
                    configured_path = project_relative
                else:
                    configured_path = config_relative
            return configured_path

        return LlmFactory._project_root() / "configs" / "llm_manager.env"

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[4]

    @staticmethod
    def _read_settings(config_path: Path) -> Dict[str, Any]:
        """仅读取配置中的 settings 块。"""
        if not config_path.exists():
            return {}
        try:
            with config_path.open("rb") as f:
                raw = tomllib.load(f)
        except tomllib.TOMLDecodeError:
            return {}
        return raw.get("settings", {})

    @staticmethod
    def _load_env_file(env_path: Path, override: bool = False) -> None:
        """加载 env 文件（若不存在则静默跳过）。"""
        if not env_path.exists():
            return
        load_dotenv(dotenv_path=env_path, override=override)

    def _resolve_config(self, model_name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """递归解析配置，将环境变量引用替换为实际值。"""
        resolved: Dict[str, Any] = {}

        for key, value in cfg.items():
            if key.endswith("_env"):
                # 将 base_url_env -> base_url，并从环境变量读取
                actual_key = key[:-4]
                env_var_name = value
                env_value = os.getenv(env_var_name)

                if env_value is None:
                    raise ValueError(
                        f"环境变量 '{env_var_name}' 未设置 (配置键: {key})"
                    )
                resolved[actual_key] = env_value
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                resolved[key] = self._resolve_config(f"{model_name}.{key}", value)
            else:
                resolved[key] = value

        # 添加全局 timeout（如果未设置）
        if "timeout" not in resolved:
            resolved["timeout"] = self._timeout

        return resolved

    # ==================== MutableMapping 必需接口 ====================

    def __getitem__(self, model_name: str) -> BaseChatModel:
        """通过模型名获取对应的模型实例。"""
        # 规范化模型名称
        normalized_name = model_name.replace("_", "-")

        # 如果已加载，直接返回
        if normalized_name in self._models:
            return self._models[normalized_name]

        # 检查配置是否存在
        if normalized_name not in self._configs:
            available = ", ".join(sorted(self._configs.keys()))
            failed_info = ""
            if self._failed_configs:
                failed_list = ", ".join(sorted(self._failed_configs.keys()))
                failed_info = f"\n失败的模型: {failed_list}"

            raise KeyError(
                f"模型 '{model_name}' 未在配置中定义。\n"
                f"可用模型: {available}{failed_info}\n"
                f"配置文件: {self._config_path}"
            )

        # 初始化模型（仅在非预加载模式下会执行到这里）
        try:
            self._models[normalized_name] = init_chat_model(
                **self._configs[normalized_name]
            )
            logger.debug(f"模型 '{normalized_name}' 初始化成功")
        except Exception as e:
            logger.error(f"模型 '{normalized_name}' 初始化失败: {e}")
            raise RuntimeError(f"模型初始化失败: {normalized_name}") from e

        return self._models[normalized_name]

    def __setitem__(self, model_name: str, model: BaseChatModel) -> None:
        """
        设置模型实例（支持动态注册模型）。

        注意：这不会修改配置文件，只在运行时生效。
        """
        normalized_name = model_name.replace("_", "-")
        self._models[normalized_name] = model
        logger.debug(f"已注册模型实例: {normalized_name}")

    def __delitem__(self, model_name: str) -> None:
        """删除已加载的模型实例（释放内存）。"""
        normalized_name = model_name.replace("_", "-")
        if normalized_name in self._models:
            del self._models[normalized_name]
            logger.debug(f"已删除模型实例: {normalized_name}")
        else:
            raise KeyError(f"模型 '{model_name}' 未加载")

    def __iter__(self) -> Iterator[str]:
        """迭代所有可用的模型名称（配置中定义的）。"""
        return iter(self._configs)

    def __len__(self) -> int:
        """返回可用模型的数量。"""
        return len(self._configs)

    def __contains__(self, model_name: object) -> bool:
        """检查模型是否在配置中定义。"""
        if not isinstance(model_name, str):
            return False
        normalized_name = model_name.replace("_", "-")
        return normalized_name in self._configs

    def __repr__(self) -> str:
        """返回工厂的字符串表示。"""
        loaded_count = len(self._models)
        total_count = len(self._configs)
        failed_count = len(self._failed_configs)

        status = f"total={total_count}, loaded={loaded_count}"
        if failed_count > 0:
            status += f", failed={failed_count}"

        return f"LlmFactory({status}, config='{self._config_path}')"

    # ==================== 额外便捷方法 ====================

    def get(
        self, model_name: str, default: Optional[BaseChatModel] = None
    ) -> Optional[BaseChatModel]:
        """安全获取模型，不存在时返回默认值。"""
        try:
            return self[model_name]
        except (KeyError, RuntimeError) as e:
            logger.warning(f"获取模型失败: {e}")
            return default

    def keys(self) -> List[str]:
        """返回所有可用模型名称列表（覆盖 MutableMapping 的视图返回）。"""
        return sorted(self._configs.keys())

    def values(self) -> List[BaseChatModel]:
        """返回所有已加载的模型实例列表。"""
        return [self[name] for name in self._configs.keys()]

    def items(self) -> List[tuple[str, BaseChatModel]]:
        """返回所有模型名称和实例的元组列表。"""
        return [(name, self[name]) for name in self._configs.keys()]

    def get_config(self, model_name: str) -> Dict[str, Any]:
        """获取模型的解析后配置。"""
        normalized_name = model_name.replace("_", "-")
        if normalized_name not in self._configs:
            raise KeyError(f"模型 '{model_name}' 配置不存在")
        return self._configs[normalized_name].copy()

    def list_models(self) -> List[str]:
        """列出所有可用模型名（别名方法，等同于 keys()）。"""
        return self.keys()

    def list_failed_models(self) -> Dict[str, str]:
        """列出所有加载失败的模型及其错误信息。"""
        return self._failed_configs.copy()

    def is_loaded(self, model_name: str) -> bool:
        """检查模型是否已实例化。"""
        normalized_name = model_name.replace("_", "-")
        return normalized_name in self._models

    def unload(self, model_name: str) -> None:
        """卸载指定模型实例（释放内存）。等同于 del factory[model_name]。"""
        del self[model_name]

    def clear_loaded(self) -> None:
        """清空所有已加载的模型实例（但保留配置）。"""
        count = len(self._models)
        self._models.clear()
        logger.info(f"已清空 {count} 个已加载的模型实例")

    def reload(
        self,
        config_path: Path | str | None = None,
        env_path: Path | str | None = None,
        *,
        dotenv_override: bool | None = None,
    ) -> None:
        """重新加载配置（清空缓存的模型实例）。"""
        self._models.clear()
        self._configs.clear()
        self._failed_configs.clear()

        if config_path:
            self._config_path = Path(config_path)
        self._env_path = self._resolve_env_path(env_path, config_path=self._config_path)
        self._load_env_file(
            self._env_path,
            override=(
                self._dotenv_override if dotenv_override is None else dotenv_override
            ),
        )

        self._load_config(self._config_path)

        logger.info(f"配置已重新加载: {self._config_path}")

    def validate_config(self) -> Dict[str, List[str]]:
        """
        验证配置文件的完整性和一致性。

        返回:
            包含警告和错误的字典
        """
        issues = {"warnings": [], "errors": []}

        for model_name in self._configs.keys():
            # 检查命名一致性
            if "_" in model_name:
                suggested = model_name.replace("_", "-")
                if suggested != model_name and suggested in self._configs:
                    issues["warnings"].append(
                        f"模型名称 '{model_name}' 和 '{suggested}' 同时存在，可能造成混淆"
                    )

            # 检查必需的配置项
            config = self._configs[model_name]
            required_fields = ["model", "model_provider"]

            for field in required_fields:
                if field not in config:
                    issues["errors"].append(
                        f"模型 '{model_name}' 缺少必需字段: '{field}'"
                    )

        return issues


# 模块级单例
llm_manager: Optional[LlmFactory] = None


def get_llm_manager(
    config_path: Path | str | None = None,
    env_path: Path | str | None = None,
    *,
    skip_invalid: bool = True,
    preload_all: bool = True,
    dotenv_override: bool = True,
) -> LlmFactory:
    """
    获取 LLM 工厂单例。

    参数:
        config_path: 配置文件路径
        env_path: 环境变量文件路径（默认 configs/llm_manager.env）
        skip_invalid: 是否跳过无效配置
        preload_all: 是否预加载所有模型
        dotenv_override: 是否让 .env 覆盖进程已有环境变量（默认 True）
    """
    global llm_manager
    if llm_manager is None:
        llm_manager = LlmFactory(
            config_path,
            env_path=env_path,
            dotenv_override=dotenv_override,
        )
    elif config_path is not None or env_path is not None:
        llm_manager.reload(
            config_path=config_path,
            env_path=env_path,
            dotenv_override=dotenv_override,
        )
    return llm_manager
