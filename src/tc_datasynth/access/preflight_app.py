from __future__ import annotations

"""
预检命令：运行前检查外部依赖与关键配置，不启动主流程。
"""

import argparse
import sys

from tc_datasynth.access.cli_app import CLIApp
from tc_datasynth.core.logging import configure_logger
from tc_datasynth.pipeline.enhance.mixin import PreflightCheckResult
from tc_datasynth.service import DataSynthService


class PreflightApp:
    """预检命令封装。"""

    @staticmethod
    def print_help(prog: str) -> None:
        """输出 preflight 参数说明。"""
        print("\n[preflight] 运行前预检参数说明")
        PreflightApp.build_parser(prog=prog).print_help()

    @staticmethod
    def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
        """构建预检参数解析器。"""
        parser = CLIApp.build_parser(prog=prog)
        parser.description = "TC-DataSynth 运行前预检，不启动主流程"
        return parser

    @staticmethod
    def parse_args(args: list[str] | None = None) -> argparse.Namespace:
        """解析预检参数。"""
        parser = PreflightApp.build_parser()
        return parser.parse_args(args)

    @staticmethod
    def _format_result(result: PreflightCheckResult) -> str:
        """格式化单个预检结果。"""
        status = "OK" if result.ok else "FAIL"
        component = f"{result.component_type}.{result.component_name}"
        target_text = f" | target={result.target}" if result.target else ""
        return (
            f"[{status}] {component} | stage={result.stage.value}"
            f"{target_text} | {result.message}"
        )

    def run(self, args: list[str] | None = None) -> int:
        """执行预检。"""
        parsed = PreflightApp.parse_args(args)
        config = CLIApp.build_runtime_config(parsed)
        log = configure_logger(config.log_level)
        service = DataSynthService(config=config)
        response = service.preflight()
        if response.error:
            log.error(f"Preflight failed: {response.error}")
            return 1

        if not response.results:
            log.info("No preflight checks found.")
            return 0

        log.info("Preflight checks:")
        for result in response.results:
            line = self._format_result(result)
            if result.ok:
                log.success(line)
            else:
                log.error(line)
            if not result.ok and result.details:
                log.warning(f"details: {result.details}")

        return 0 if response.success else 1
