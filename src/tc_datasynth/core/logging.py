"""
基于 loguru 的日志配置工具，兼容 tqdm 输出。
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger
from tqdm import tqdm


def _tqdm_sink(message: str) -> None:
    """使用 tqdm.write 保证进度条不被日志覆盖。"""
    tqdm.write(message, end="")


def configure_logger(level: str = "INFO", log_file: Optional[Path] = None, logger_name: Optional[str] = None):
    """配置日志输出格式与级别，可同时输出到 stderr 和文件。"""
    logger.remove()
    logger.add(
        _tqdm_sink,
        level=level.upper(),
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    )
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.touch(exist_ok=True)
        logger.add(
            str(log_file),
            level=level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8",
        )
    return logger if logger_name is None else logger.bind(name=logger_name)
