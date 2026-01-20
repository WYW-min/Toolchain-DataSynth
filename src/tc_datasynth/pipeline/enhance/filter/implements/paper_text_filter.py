from __future__ import annotations

"""
简单文本过滤器：掐头去尾（去掉引言/摘要前内容，删除致谢/引用列表之后内容）。
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from tc_datasynth.pipeline.enhance.filter.base import (
    TextFilterBase,
    TextFilterConfigBase,
)

# 论文正文起始标记（按优先级排序，先匹配的优先）
DEFAULT_START_MARKERS: List[str] = [
    # 中文
    "摘要",
    "摘 要",
    "内容摘要",
    "论文摘要",
    "中文摘要",
    "引言",
    "前言",
    "绪论",
    "第一章",
    "第1章",
    "一、",
    "1 引言",
    "1. 引言",
    "1 绪论",
    # 英文
    "Abstract",
    "ABSTRACT",
    "Summary",
    "SUMMARY",
    "Introduction",
    "INTRODUCTION",
    "1 Introduction",
    "1. Introduction",
    "I. Introduction",
    "Chapter 1",
    "CHAPTER 1",
]

# 论文正文结束标记（匹配后截断）
DEFAULT_END_MARKERS: List[str] = [
    # 中文
    "致谢",
    "致 谢",
    "鸣谢",
    "感谢",
    "参考文献",
    "参 考 文 献",
    "引用文献",
    "文献",
    "注释",
    "附录",
    "附 录",
    # 英文
    "Acknowledgment",
    "Acknowledgments",
    "Acknowledgement",
    "Acknowledgements",
    "ACKNOWLEDGMENT",
    "ACKNOWLEDGMENTS",
    "References",
    "REFERENCES",
    "Bibliography",
    "BIBLIOGRAPHY",
    "Works Cited",
    "Literature Cited",
    "Appendix",
    "APPENDIX",
    "Appendices",
    "Notes",
    "Endnotes",
    "Footnotes",
    "Supporting Information",
    "Supplementary Materials",
]


@dataclass(slots=True)
class PaperTextFilterConfig(TextFilterConfigBase):
    """简单文本过滤配置。"""

    start_markers: List[str] = field(
        default_factory=lambda: DEFAULT_START_MARKERS.copy()
    )
    end_markers: List[str] = field(default_factory=lambda: DEFAULT_END_MARKERS.copy())
    case_insensitive: bool = True
    strip_whitespace: bool = True
    include_start_marker: bool = True
    include_end_marker: bool = False

    # 上下文特征配置
    max_heading_length: int = 50  # 标题行最大长度
    require_short_line: bool = True  # 要求行较短（像标题）
    check_surrounding_blank: bool = True  # 检查前后是否有空行
    forbid_sentence_punctuation: bool = True  # 禁止包含正文标点


class PaperTextFilter(TextFilterBase[PaperTextFilterConfig]):
    """按指定标记掐头去尾的文本过滤器。"""

    # 预编译的清理正则
    _HEADING_PREFIX_PATTERN = re.compile(
        r"^"
        r"(?:#{1,6}\s*)?"  # Markdown 标题
        r"(?:第[一二三四五六七八九十\d]+[章节篇部]\s*)?"
        r"(?:[一二三四五六七八九十]+[、.．]\s*)?"
        r"(?:\d+(?:[.\-．]\d+)*[.\s]*\s*)?"
        r"(?:[IVXivx]+[.\s]+)?"
        r"(?:[A-Za-z][.\s]+)?"
    )

    # 正文标点（出现这些说明是正文句子，不是标题）
    _SENTENCE_PUNCTUATION = re.compile(r"[，,；;：。…、（）()]")

    # 空行判断
    _BLANK_LINE = re.compile(r"^\s*$")

    @classmethod
    def default_config(cls) -> PaperTextFilterConfig:
        return PaperTextFilterConfig()

    def _apply(self, text: str) -> str:
        """应用掐头去尾规则，返回处理结果。"""
        if not text:
            return text

        lines = text.splitlines(keepends=True)
        start_line_idx = self._find_marker_line(
            lines, self.config.start_markers, find_first=True
        )
        end_line_idx = self._find_marker_line(
            lines,
            self.config.end_markers,
            find_first=True,
            search_from=start_line_idx or 0,
        )

        # 确定起始位置
        if start_line_idx is not None:
            start = (
                start_line_idx
                if self.config.include_start_marker
                else start_line_idx + 1
            )
        else:
            start = 0

        # 确定结束位置
        if end_line_idx is not None and end_line_idx > start:
            end = end_line_idx + 1 if self.config.include_end_marker else end_line_idx
        else:
            end = len(lines)

        filtered = "".join(lines[start:end])
        return filtered.strip() if self.config.strip_whitespace else filtered

    def _find_marker_line(
        self,
        lines: List[str],
        markers: List[str],
        find_first: bool = True,
        search_from: int = 0,
    ) -> Optional[int]:
        """查找匹配标记的行索引，带上下文验证。"""
        if not markers:
            return None
        for idx in range(search_from, len(lines)):
            line = lines[idx]
            if self._is_heading_line(lines, idx, markers):
                return idx
        return None

    def _is_heading_line(
        self,
        lines: List[str],
        idx: int,
        markers: List[str],
    ) -> bool:
        """判断某行是否为标题行（综合上下文特征）。"""
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            return False

        # 1. 检查是否匹配标记关键词
        if not self._line_matches_marker(stripped, markers):
            return False

        # 2. 检查行长度（标题通常较短）
        if self.config.require_short_line:
            if len(stripped) > self.config.max_heading_length:
                return False

        # 3. 检查是否包含正文标点（标题通常不含逗号、句号等）
        if self.config.forbid_sentence_punctuation:
            # 排除标记本身后，检查剩余部分
            normalized = self._normalize_line(stripped)
            # 如果标准化后的内容与 marker 接近，允许通过
            # 如果有额外内容且包含正文标点，则不是标题
            remaining = self._get_remaining_content(stripped, markers)
            if remaining and self._SENTENCE_PUNCTUATION.search(remaining):
                return False

        # 4. 检查前后是否有空行（标题通常独立）
        if self.config.check_surrounding_blank:
            has_blank_context = self._has_surrounding_blank(lines, idx)
            # 如果没有空行上下文，降低置信度但不完全排除
            # 这里我们要求至少满足其他条件
            if not has_blank_context and len(stripped) > 30:
                return False

        return True

    def _has_surrounding_blank(self, lines: List[str], idx: int) -> bool:
        """检查行前后是否有空行。"""
        has_blank_before = False
        has_blank_after = False

        # 检查前面（跳过连续空行找最近非空行）
        for i in range(idx - 1, -1, -1):
            if self._BLANK_LINE.match(lines[i]):
                has_blank_before = True
                break
            else:
                break  # 遇到非空行就停止

        # 检查后面
        for i in range(idx + 1, len(lines)):
            if self._BLANK_LINE.match(lines[i]):
                has_blank_after = True
                break
            else:
                break

        # 至少一侧有空行，或者是文档开头/结尾
        return has_blank_before or has_blank_after or idx == 0 or idx == len(lines) - 1

    def _get_remaining_content(self, line: str, markers: List[str]) -> str:
        """获取移除标记后的剩余内容。"""
        normalized = self._normalize_line(line)
        for marker in markers:
            target = marker.strip()
            if self.config.case_insensitive:
                lower_norm = normalized.lower()
                lower_target = target.lower()
                if lower_norm.startswith(lower_target):
                    return normalized[len(target) :].strip()
                if lower_norm == lower_target:
                    return ""
            else:
                if normalized.startswith(target):
                    return normalized[len(target) :].strip()
                if normalized == target:
                    return ""
        return normalized

    def _normalize_line(self, line: str) -> str:
        """标准化行内容：去除编号、标点、空白。"""
        content = line.strip()
        content = self._HEADING_PREFIX_PATTERN.sub("", content)
        content = re.sub(r"[:：\s]+$", "", content)
        return content

    def _line_matches_marker(self, line: str, markers: List[str]) -> bool:
        """判断某行是否匹配标记关键词。"""
        normalized = self._normalize_line(line)
        if not normalized:
            return False

        for marker in markers:
            target = marker.strip()
            if self.config.case_insensitive:
                lower_norm = normalized.lower()
                lower_target = target.lower()
                if lower_norm.startswith(lower_target) or lower_norm == lower_target:
                    return True
            else:
                if normalized.startswith(target) or normalized == target:
                    return True
        return False
