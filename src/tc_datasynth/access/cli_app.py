from __future__ import annotations

"""
CLI 封装：参数解析与配置构建。
"""

import argparse
from pathlib import Path

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.core.logging import configure_logger
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
        log = configure_logger(config.log_level)
        if not config.input_dir.exists():
            log.error(f"Input directory not found: {config.input_dir}")
            return 1

        service = DataSynthService(config=config)
        response = service.run(SynthesisRequest(doc_limit=config.doc_limit))
        if not response.success:
            log.error(f"Pipeline run failed: {response.error}")
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
            "--mode",
            type=str,
            choices=["mock", "real"],
            default=None,
            help="运行模式：mock 或 real（可覆盖配置）",
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
        parser.add_argument(
            "-c", "--config", type=Path, help="可选：通过 TOML 加载默认参数"
        )
        parser.add_argument(
            "--doc-limit",
            "--max-docs",
            dest="doc_limit",
            type=int,
            default=None,
            help="限制处理的文档数量（可覆盖配置）",
        )
        parser.add_argument(
            "--limit",
            type=str,
            default=None,
            help="限制最终生成的最大 QA 数量（0/none=全量）",
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
        parser.add_argument(
            "--llm-config",
            type=Path,
            default=None,
            help="LLM 配置文件路径（可覆盖配置）",
        )
        parser.add_argument(
            "--llm-model",
            type=str,
            default=None,
            help="LLM 模型名（可覆盖配置）",
        )
        parser.add_argument(
            "--generator-name",
            "--generator-backend",
            dest="generator_name",
            type=str,
            choices=["mock", "simple_qa", "concurrent_qa"],
            default=None,
            help="生成器实现名：mock、simple_qa 或 concurrent_qa（可覆盖配置）",
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
                doc_limit=args.doc_limit,
                log_level=args.log_level or "INFO",
            )
        # 仅覆盖关键运行时参数
        if args.input_dir:
            config.input_dir = args.input_dir
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.doc_limit is not None:
            config.doc_limit = args.doc_limit
        if args.limit is not None:
            config.limit = RuntimeConfig.normalize_batch_size(
                args.limit, default=config.limit
            )
        if args.log_level:
            config.log_level = args.log_level
        if args.mode:
            config.mode = args.mode
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
        if args.llm_config:
            config.llm_config_path = args.llm_config
        if args.llm_model:
            config.llm_model = args.llm_model
            config.components.setdefault("generator", {})["llm_model"] = args.llm_model
        if args.generator_name:
            generator_overrides = {"name": args.generator_name}
            if args.llm_model:
                generator_overrides["llm_model"] = args.llm_model
            config.components["generator"] = generator_overrides
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
