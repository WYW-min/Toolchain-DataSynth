"""
统一入口：子命令分发到 CLI 或 API。
"""

import sys

from tc_datasynth.access.cli_app import CLIApp
from tc_datasynth.access.api_app import APIApp
from tc_datasynth.arg_parser import get_parsers
from tc_datasynth.utilities.dict_dataclass import ddataclass


@ddataclass(slots=True)
class Apps:
    local: type[CLIApp]
    server: type[APIApp]


APP_NAME = "tc-datasynth"
APP_CLASSES = Apps(local=CLIApp, server=APIApp)


def main():
    parsers = get_parsers()
    args, remaining = parsers.main.parse_known_args()
    if args.root_help and args.command is None:
        parsers.main.print_help()
        for name, app_cls in APP_CLASSES.items():
            app_cls.print_help(prog=f"{APP_NAME} {name}")
        return 0

    app_command = getattr(args, "command", None) or "local"
    if app_command in APP_CLASSES:
        if getattr(args, f"{app_command}_help", False):
            APP_CLASSES[app_command].print_help(prog=f"{APP_NAME} {app_command}")
            return 0
        app = APP_CLASSES[app_command]()
        return app.run(remaining)

    parsers.main.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
