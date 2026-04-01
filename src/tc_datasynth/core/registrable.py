from __future__ import annotations

"""
轻量可注册组件基类：统一 component_name / get_component_name 约定。
"""

from typing import ClassVar


class RegistrableComponent:
    """提供组件稳定标识，不介入业务接口。"""

    component_name: ClassVar[str] = ""

    @classmethod
    def get_component_name(cls) -> str:
        """返回组件稳定标识。"""
        if not cls.component_name:
            raise ValueError(f"{cls.__name__} 未声明 component_name")
        return cls.component_name
