"""
访问层入口：CLI / API 启动方式统一放置在此。
"""

from tc_datasynth.access.api_app import APIApp
from tc_datasynth.access.cli_app import CLIApp
from tc_datasynth.access.preflight_app import PreflightApp
from tc_datasynth.utilities.dict_dataclass import ddataclass

__all__ = ["APIApp", "CLIApp", "PreflightApp"]


@ddataclass(slots=True)
class Apps:
    local: type[CLIApp]
    server: type[APIApp]
    preflight: type[PreflightApp]
