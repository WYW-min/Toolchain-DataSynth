from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tc_datasynth.main import main
from tc_datasynth.pipeline.enhance.mixin import PreflightCheckResult, PreflightStage
from tc_datasynth.service import PreflightResponse


class PreflightCommandTest(unittest.TestCase):
    """preflight 子命令测试。"""

    def test_main_preflight_command_returns_zero_when_no_checks_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "mock.toml"
            config_path.write_text(
                """
[runtime]
mode = "mock"
input_dir = "."
output_dir = "data/out"
""".strip(),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["preflight", "--config", str(config_path)])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("No preflight checks found.", output)

    def test_main_preflight_command_returns_one_when_any_check_fails(self) -> None:
        result = PreflightCheckResult(
            component_type="generator",
            component_name="simple_qa",
            ok=False,
            stage=PreflightStage.PING,
            message="model ping failed",
            target="doubao-flash",
            details={"error": "timeout"},
        )
        response = PreflightResponse(results=[result], success=False)

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "mock.toml"
            config_path.write_text(
                """
[runtime]
mode = "mock"
input_dir = "."
output_dir = "data/out"
""".strip(),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch("tc_datasynth.access.preflight_app.DataSynthService.preflight", return_value=response),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = main(["preflight", "--config", str(config_path)])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("Preflight checks:", output)
        self.assertIn("[FAIL] generator.simple_qa", output)
        self.assertIn("stage=ping", output)

    def test_main_preflight_help_prints_command_help(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["preflight", "--help"])

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("[preflight] 运行前预检参数说明", output)
        self.assertIn("--config", output)

