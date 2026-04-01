from __future__ import annotations

"""
预检通用 Mixin：为依赖外部能力的组件提供统一预检接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PreflightStage(str, Enum):
    """预检阶段枚举。"""

    CONFIG = "config"
    SERVICE = "service"
    LOAD = "load"
    PING = "ping"


@dataclass(slots=True)
class PreflightCheckResult:
    """单个组件的预检结果。"""

    component_type: str
    component_name: str
    ok: bool
    stage: PreflightStage
    message: str
    target: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class PreflightCheckMixin(ABC):
    """预检能力 Mixin，仅适用于有外部依赖的组件。"""

    @abstractmethod
    def preflight_check(self) -> PreflightCheckResult:
        """执行组件级预检并返回结构化结果。"""
        raise NotImplementedError
