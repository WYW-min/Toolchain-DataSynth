from __future__ import annotations

"""
CLI 封装：参数解析与配置构建。
"""

import argparse
import sys
from pathlib import Path

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.service import DataSynthService, SynthesisRequest


class CLIApp:
    """CLI 应用封装：提供 run 接口。"""

    @staticmethod
    def print_help(prog: str) -> None:
        """输出 CLI 的帮助信息。"""
        print("\n[local] CLI 参数说明")
        CLIApp.build_parser(prog=prog).print_help()

    def run(self, args: list[str] | None = None) -> int:
        """运行 CLI 流程。"""
        args = CLIApp.parse_args(args)
        config = CLIApp.build_runtime_config(args)
        if not config.input_dir.exists():
            print(
                f"Error: Input directory not found: {config.input_dir}", file=sys.stderr
            )
            return 1

        service = DataSynthService(config=config)
        response = service.run(SynthesisRequest(limit=config.max_docs))
        if not response.success:
            print(f"Error: {response.error}", file=sys.stderr)
            return 1
        return 0

    @staticmethod
    def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
        """构建 CLI 参数解析器。"""
        parser = argparse.ArgumentParser(
            prog=prog,
            description="TC-DataSynth CLI（W1 mock 流程）",
        )
        parser.add_argument(
            "--input-dir",
            type=Path,
            default=None,
            help="PDF 输入目录（可覆盖配置）",
        )
        parser.add_argument(
            "--output-dir",
            type=Path,
            default=None,
            help="运行产物输出目录（可覆盖配置）",
        )
        parser.add_argument("--config", type=Path, help="可选：通过 TOML 加载默认参数")
        parser.add_argument(
            "--max-docs",
            type=int,
            default=None,
            help="限制处理的文档数量（可覆盖配置）",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            default=None,
            help="日志级别：INFO/DEBUG/WARN/ERROR（可覆盖）",
        )
        parser.add_argument(
            "--parse-batch-size",
            "--parse_batch_size",
            "-pbs",
            type=str,
            default=None,
            help="解析批处理数量（1=流式，none/0=全量）",
        )
        parser.add_argument(
            "--generate-batch-size",
            "--generate_batch_size",
            "-gbs",
            type=str,
            default=None,
            help="生成批处理数量（1=流式，none/0=全量）",
        )
        parser.add_argument(
            "--mock", "-m", action="store_true", help="强制启用 mock 模式"
        )
        return parser

    @staticmethod
    def parse_args(args: list[str] | None = None) -> argparse.Namespace:
        """解析命令行参数。"""
        parser = CLIApp.build_parser()
        return parser.parse_args(args)

    @staticmethod
    def build_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
        """根据 CLI 或 TOML 构建运行配置。"""
        if args.config:
            config = RuntimeConfig.from_toml(args.config)
        else:
            config = RuntimeConfig(
                input_dir=args.input_dir
                or Path("/Data_two/wyw/data/TC-DATASYNTH/原始PDF"),
                output_dir=args.output_dir or Path("./data/out"),
                max_docs=args.max_docs,
                log_level=args.log_level or "INFO",
            )
        # 仅覆盖关键运行时参数
        if args.input_dir:
            config.input_dir = args.input_dir
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.max_docs is not None:
            config.max_docs = args.max_docs
        if args.log_level:
            config.log_level = args.log_level
        if args.parse_batch_size is not None:
            config.parse_batch_size = RuntimeConfig.normalize_batch_size(
                args.parse_batch_size, default=config.parse_batch_size
            )
        if args.generate_batch_size is not None:
            config.generate_batch_size = RuntimeConfig.normalize_batch_size(
                args.generate_batch_size, default=config.generate_batch_size
            )
        if args.mock:
            config.mode = "mock"
        config.ensure_output_dir()
        return config


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    """构建 CLI 参数解析器。"""
    return CLIApp.build_parser(prog=prog)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    return CLIApp.parse_args(args)


def build_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    """根据 CLI 或 TOML 构建运行配置。"""
    return CLIApp.build_runtime_config(args)


def run_cli(args: list[str] | None = None) -> int:
    """CLI 入口：解析参数，构建配置并执行流水线。"""
    app = CLIApp()
    return app.run(args)
