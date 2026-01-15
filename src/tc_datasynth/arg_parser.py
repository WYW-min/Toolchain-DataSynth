import argparse
from dataclasses import dataclass

from tc_datasynth.access.api_app import APIApp
from tc_datasynth.access.cli_app import CLIApp


@dataclass(slots=True)
class Parsers:
    main: argparse.ArgumentParser
    local: argparse.ArgumentParser
    server: argparse.ArgumentParser


def get_parsers(
    local_prog: str | None = "tc-datasynth local",
    server_prog: str | None = "tc-datasynth server",
) -> Parsers:
    """构建主入口参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="tc-datasynth",
        description="TC-DataSynth 数据合成工具",
        add_help=False,
    )
    parser.add_argument(
        "-h", "--help", action="store_true", dest="root_help", help="显示帮助"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    _get_local_parser(subparsers)
    _get_server_parser(subparsers)
    return Parsers(
        main=parser,
        local=CLIApp.build_parser(prog=local_prog),
        server=APIApp.build_parser(prog=server_prog),
    )


def _get_local_parser(subparsers) -> argparse.ArgumentParser:
    """子命令: local (CLI 模式)。"""
    local_parser = subparsers.add_parser(
        "local", help="运行数据合成流程（CLI）", add_help=False
    )
    local_parser.add_argument(
        "-h", "--help", action="store_true", dest="local_help", help="显示帮助"
    )
    return local_parser


def _get_server_parser(subparsers) -> argparse.ArgumentParser:
    """子命令: server (API 模式)"""
    server_parser = subparsers.add_parser(
        "server", help="启动 API 服务", add_help=False
    )
    server_parser.add_argument(
        "-h", "--help", action="store_true", dest="server_help", help="显示帮助"
    )
    return server_parser
