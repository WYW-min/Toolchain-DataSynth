from __future__ import annotations

"""
API 入口：暴露 create_app 作为服务启动接口，当前为 W1 占位。
"""

import argparse
import sys


class APIApp:
    """API 应用封装：提供 run 接口。"""

    @staticmethod
    def print_help(prog: str) -> None:
        """输出 server API 的帮助信息。"""
        print("\n[server] API 参数说明")
        APIApp.build_parser(prog=prog).print_help()

    @staticmethod
    def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
        """构建 API 参数解析器。"""
        parser = argparse.ArgumentParser(
            prog=prog,
            description="TC-DataSynth API 服务（W1 占位）",
        )
        parser.add_argument("--host", default="0.0.0.0", help="监听地址")
        parser.add_argument("--port", "-p", type=int, default=8000, help="监听端口")
        return parser

    @staticmethod
    def parse_args(args: list[str] | None = None) -> argparse.Namespace:
        """解析 API 参数。"""
        parser = APIApp.build_parser()
        return parser.parse_args(args)

    def create_app(self):
        """创建 FastAPI 应用（W1 占位）。"""
        try:
            from fastapi import FastAPI
        except ImportError as exc:  # pragma: no cover - 仅在缺依赖时触发
            raise ImportError("未安装 fastapi，请执行: pip install fastapi") from exc
        app = FastAPI(title="TC-DataSynth API", version="0.1.0")

        @app.get("/health")
        def health() -> dict[str, str]:
            """健康检查。"""
            return {"status": "ok"}

        return app

    def run(self, args: list[str] | None = None) -> int:
        """启动 API 服务。"""
        parsed = APIApp.parse_args(args)
        try:
            import uvicorn

            app = self.create_app()
        except ImportError as e:
            print(
                "Error: API 依赖未安装，请执行: pip install fastapi uvicorn\n" f"{e}",
                file=sys.stderr,
            )
            return 1

        print(f"Starting API server at http://{parsed.host}:{parsed.port}")
        uvicorn.run(app, host=parsed.host, port=parsed.port)
        return 0


def create_app():
    """创建 FastAPI 应用（W1 占位）。"""
    app = APIApp()
    return app.create_app()


def run_server(host: str = "0.0.0.0", port: int = 8000) -> int:
    """启动 API 服务。"""
    app = APIApp()
    return app.run(["--host", host, "--port", str(port)])


def run_serve(host: str = "0.0.0.0", port: int = 8000) -> int:
    """启动 API 服务。"""
    return run_server(host=host, port=port)
