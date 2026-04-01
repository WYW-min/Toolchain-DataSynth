from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tc_datasynth.access.cli_app import CLIApp


class CliRuntimeModeTest(unittest.TestCase):
    """CLI 运行模式参数测试。"""

    def test_mode_argument_overrides_runtime_config(self) -> None:
        """`--mode real` 应覆盖默认 mock 模式。"""
        args = CLIApp.parse_args(
            [
                "--mode",
                "real",
                "--input-dir",
                str(Path(".")),
                "--output-dir",
                "data/out",
            ]
        )

        config = CLIApp.build_runtime_config(args)

        self.assertEqual(config.mode, "real")

    def test_doc_limit_argument_overrides_runtime_doc_limit(self) -> None:
        """`--doc-limit 2` 应覆盖文档处理上限。"""
        args = CLIApp.parse_args(
            [
                "--doc-limit",
                "2",
                "--input-dir",
                str(Path(".")),
                "--output-dir",
                "data/out",
            ]
        )

        config = CLIApp.build_runtime_config(args)

        self.assertEqual(config.doc_limit, 2)

    def test_generator_name_argument_overrides_generator_component(self) -> None:
        """`--generator-name simple_qa` 应覆盖 components.generator.name。"""
        args = CLIApp.parse_args(
            [
                "--generator-name",
                "simple_qa",
                "--input-dir",
                str(Path(".")),
                "--output-dir",
                "data/out",
            ]
        )

        config = CLIApp.build_runtime_config(args)

        self.assertEqual(config.components["generator"]["name"], "simple_qa")

    def test_limit_argument_overrides_runtime_limit(self) -> None:
        """`--limit 2` 应覆盖 QA 上限。"""
        args = CLIApp.parse_args(
            [
                "--limit",
                "2",
                "--input-dir",
                str(Path(".")),
                "--output-dir",
                "data/out",
            ]
        )

        config = CLIApp.build_runtime_config(args)

        self.assertEqual(config.limit, 2)

    def test_generator_name_override_replaces_existing_generator_params(self) -> None:
        """从 mock 切到 simple_qa 时，应清理不兼容的旧 generator 参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runtime.toml"
            config_path.write_text(
                """
[runtime]
input_dir = "."
output_dir = "data/out"

[components.generator]
name = "mock"
questions_per_doc = 3
""".strip(),
                encoding="utf-8",
            )
            args = CLIApp.parse_args(
                [
                    "--config",
                    str(config_path),
                    "--generator-name",
                    "simple_qa",
                    "--llm-model",
                    "doubao-flash",
                ]
            )

            config = CLIApp.build_runtime_config(args)

            self.assertEqual(config.components["generator"]["name"], "simple_qa")
            self.assertEqual(config.components["generator"]["llm_model"], "doubao-flash")
            self.assertNotIn("questions_per_doc", config.components["generator"])
