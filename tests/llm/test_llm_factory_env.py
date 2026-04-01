from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tc_datasynth.core.llm.llm_factory as llm_factory_module


class LlmFactoryEnvLoadingTest(unittest.TestCase):
    """校验 llm_manager 的 .env 加载与重载行为。"""

    _ENV_KEYS = ("TEST_BASE_URL", "TEST_API_KEY")

    def setUp(self) -> None:
        self._saved_env = {key: os.environ.get(key) for key in self._ENV_KEYS}
        for key in self._ENV_KEYS:
            os.environ.pop(key, None)
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None

    def tearDown(self) -> None:
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_env_file_is_loaded_on_init(self) -> None:
        """初始化时应读取 env 文件并注入配置解析。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = self._write_llm_toml(base / "llm.toml")
            env1 = self._write_env(
                base / "llm_manager.env",
                base_url="https://env-one.example.com",
                api_key="env-one-key",
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ):
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env1,
                )
            cfg = manager.get_config("demo-model")

            self.assertEqual(cfg["base_url"], "https://env-one.example.com")
            self.assertEqual(cfg["api_key"], "env-one-key")
            self.assertEqual(os.environ.get("TEST_BASE_URL"), "https://env-one.example.com")
            self.assertEqual(os.environ.get("TEST_API_KEY"), "env-one-key")

    def test_reload_respects_env_path_and_dotenv_override(self) -> None:
        """重载时应支持切换 env 文件，并受 dotenv_override 控制。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = self._write_llm_toml(base / "llm.toml")
            env1 = self._write_env(
                base / "llm_manager_1.env",
                base_url="https://env-one.example.com",
                api_key="env-one-key",
            )
            env2 = self._write_env(
                base / "llm_manager_2.env",
                base_url="https://env-two.example.com",
                api_key="env-two-key",
            )

            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ):
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env1,
                )
                # override=False：不覆盖已有环境变量，仍保持 env1
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env2,
                    dotenv_override=False,
                )
                cfg_no_override = manager.get_config("demo-model")
                self.assertEqual(
                    cfg_no_override["base_url"], "https://env-one.example.com"
                )
                self.assertEqual(cfg_no_override["api_key"], "env-one-key")

                # override=True：允许覆盖，切换到 env2
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env2,
                    dotenv_override=True,
                )
                cfg_override = manager.get_config("demo-model")
                self.assertEqual(
                    cfg_override["base_url"], "https://env-two.example.com"
                )
                self.assertEqual(cfg_override["api_key"], "env-two-key")

    def test_env_path_can_be_loaded_from_llm_toml_settings(self) -> None:
        """当未显式传 env_path 时，应读取 settings.env_path。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            env_file = self._write_env(
                base / "llm_manager_from_toml.env",
                base_url="https://from-toml.example.com",
                api_key="from-toml-key",
            )
            config_path = self._write_llm_toml(
                base / "llm.toml",
                env_path=env_file.name,
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ):
                manager = llm_factory_module.get_llm_manager(config_path=config_path)
            cfg = manager.get_config("demo-model")

            self.assertEqual(cfg["base_url"], "https://from-toml.example.com")
            self.assertEqual(cfg["api_key"], "from-toml-key")

    def test_env_path_supports_project_root_relative_setting(self) -> None:
        """settings.env_path 应优先支持相对于项目根目录的写法。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            env_file = self._write_env(
                base / "configs" / "llm_manager.env",
                base_url="https://from-project-root.example.com",
                api_key="from-project-root-key",
            )
            config_path = self._write_llm_toml(
                base / "configs" / "llm.toml",
                env_path="configs/llm_manager.env",
            )
            with (
                patch.object(
                    llm_factory_module.LlmFactory,
                    "_project_root",
                    return_value=base,
                ),
                patch.object(
                    llm_factory_module, "init_chat_model", return_value=object()
                ),
            ):
                manager = llm_factory_module.get_llm_manager(config_path=config_path)
            cfg = manager.get_config("demo-model")

            self.assertEqual(env_file.exists(), True)
            self.assertEqual(cfg["base_url"], "https://from-project-root.example.com")
            self.assertEqual(cfg["api_key"], "from-project-root-key")

    def test_default_override_prefers_dotenv_over_system_env(self) -> None:
        """默认行为应为 .env 覆盖系统环境变量。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            os.environ["TEST_BASE_URL"] = "https://from-system.example.com"
            os.environ["TEST_API_KEY"] = "from-system-key"
            env_file = self._write_env(
                base / "llm_manager_from_toml.env",
                base_url="https://from-dotenv.example.com",
                api_key="from-dotenv-key",
            )
            config_path = self._write_llm_toml(
                base / "llm.toml",
                env_path=env_file.name,
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ):
                manager = llm_factory_module.get_llm_manager(config_path=config_path)
            cfg = manager.get_config("demo-model")

            self.assertEqual(cfg["base_url"], "https://from-dotenv.example.com")
            self.assertEqual(cfg["api_key"], "from-dotenv-key")

    def test_init_does_not_preload_all_models(self) -> None:
        """初始化时不应直接实例化所有模型。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = self._write_llm_toml(base / "llm.toml")
            env1 = self._write_env(
                base / "llm_manager.env",
                base_url="https://env-one.example.com",
                api_key="env-one-key",
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ) as mock_init:
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env1,
                )
            self.assertEqual(mock_init.call_count, 0)
            self.assertFalse(manager.is_loaded("demo-model"))

    def test_check_only_checks_single_model(self) -> None:
        """check_only 应只检查目标模型并返回结构化结果。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = self._write_llm_toml(base / "llm.toml")
            env1 = self._write_env(
                base / "llm_manager.env",
                base_url="https://env-one.example.com",
                api_key="env-one-key",
            )

            class _FakeModel:
                def stream(self, _: str):
                    yield "1"

            with patch.object(
                llm_factory_module, "init_chat_model", return_value=_FakeModel()
            ) as mock_init:
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env1,
                )
                result = manager.check_only("demo-model")

            self.assertTrue(result.ok)
            self.assertEqual(result.stage, "ping")
            self.assertEqual(result.model_name, "demo-model")
            self.assertEqual(mock_init.call_count, 1)

    def test_check_only_returns_config_error_for_unknown_model(self) -> None:
        """未知模型应返回 config 阶段错误，不触发实例化。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = self._write_llm_toml(base / "llm.toml")
            env1 = self._write_env(
                base / "llm_manager.env",
                base_url="https://env-one.example.com",
                api_key="env-one-key",
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=object()
            ) as mock_init:
                manager = llm_factory_module.get_llm_manager(
                    config_path=config_path,
                    env_path=env1,
                )
                result = manager.check_only("missing-model")

            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "config")
            self.assertEqual(mock_init.call_count, 0)

    @staticmethod
    def _write_llm_toml(path: Path, env_path: str | None = None) -> Path:
        settings_lines = ["[settings]", "timeout = 123"]
        if env_path:
            settings_lines.append(f'env_path = "{env_path}"')
        path.write_text(
            (
                "\n".join(settings_lines)
                + "\n\n"
                "[models.demo_model]\n"
                'model = "dummy"\n'
                'model_provider = "openai"\n'
                'base_url_env = "TEST_BASE_URL"\n'
                'api_key_env = "TEST_API_KEY"\n'
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _write_env(path: Path, *, base_url: str, api_key: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"TEST_BASE_URL={base_url}\nTEST_API_KEY={api_key}\n",
            encoding="utf-8",
        )
        return path
