"""
简单文本过滤器：等值映射。
"""

from tc_datasynth.pipeline.enhance.filter.base import (
    TextFilterBase,
    TextFilterConfigBase,
)


class SimpleTextFilter(TextFilterBase[TextFilterConfigBase]):

    @classmethod
    def default_config(cls) -> TextFilterConfigBase:
        return TextFilterConfigBase()

    def _apply(self, text: str) -> str:
        return text
