from __future__ import annotations

"""
API 入口兼容层：实际实现位于 tc_datasynth.access.api_app。
"""

from tc_datasynth.access.api_app import APIApp, create_app, run_server, run_serve

__all__ = ["APIApp", "create_app", "run_server", "run_serve"]
