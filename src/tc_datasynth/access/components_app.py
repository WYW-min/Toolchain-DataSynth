from __future__ import annotations

"""
组件目录命令：展示当前可用的组件注册信息。
"""

import argparse

from tc_datasynth.component_catalog import format_component_catalog
from tc_datasynth.core.logging import configure_logger


class ComponentsApp:
    """组件目录应用封装。"""

    @staticmethod
    def print_help(prog: str) -> None:
        print("\n[components] 组件目录说明")
        ComponentsApp.build_parser(prog=prog).print_help()

    @staticmethod
    def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=prog,
            description="展示当前已注册的组件目录",
        )
        return parser

    @staticmethod
    def parse_args(args: list[str] | None = None) -> argparse.Namespace:
        parser = ComponentsApp.build_parser()
        return parser.parse_args(args)

    def run(self, args: list[str] | None = None) -> int:
        ComponentsApp.parse_args(args)
        log = configure_logger("INFO")
        log.info(format_component_catalog())
        return 0
