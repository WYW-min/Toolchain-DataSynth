from __future__ import annotations

"""
结构化 QA 生成辅助：集中封装 core/llm 交互、payload 构建与 QAPair 组装。
"""

from pathlib import Path
from typing import Any, Dict, List, Type

from pydantic import BaseModel

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.llm.llm_factory import get_llm_manager
from tc_datasynth.core.llm.prompt_factory import get_prompt_manager
from tc_datasynth.core.llm.structured_chain import StructuredChain
from tc_datasynth.core.models import DocumentChunk, QAPair, build_qa_id
from tc_datasynth.pipeline.enhance.mixin import (
    PreflightCheckResult,
    PreflightStage,
)
from tc_datasynth.utilities.tiny_tool import format_dict


class StructuredQaSupport:
    """Simple/Concurrent QA 生成器共享的辅助能力。"""

    def __init__(self) -> None:
        self._chain: StructuredChain | None = None

    def get_chain(
        self,
        *,
        ctx: RunContext,
        prompt_id: str,
        llm_model: str,
        llm_output_structure: Type[BaseModel],
    ) -> StructuredChain:
        """获取或创建结构化链路。"""
        if self._chain is None:
            prompt_template = get_prompt_manager()[prompt_id]
            llm = get_llm_manager(ctx.config.llm_config_path)[llm_model]
            self._chain = StructuredChain(
                prompt_template=prompt_template,
                data_model=llm_output_structure,
                llm=llm,
            )
        return self._chain

    @staticmethod
    def run_preflight_check(
        *,
        llm_config_path: Path,
        llm_model: str,
        prompt_id: str,
        component_name: str,
    ) -> PreflightCheckResult:
        """执行生成器的轻量预检：prompt + 单模型。"""
        if not llm_config_path.exists():
            return PreflightCheckResult(
                component_type="generator",
                component_name=component_name,
                ok=False,
                stage=PreflightStage.CONFIG,
                message=f"LLM 配置文件不存在: {llm_config_path}",
                details={"llm_config_path": str(llm_config_path)},
            )

        try:
            get_prompt_manager()[prompt_id]
        except Exception as exc:  # noqa: BLE001
            return PreflightCheckResult(
                component_type="generator",
                component_name=component_name,
                ok=False,
                stage=PreflightStage.CONFIG,
                message=f"提示词模板不可用: {prompt_id}",
                details={"prompt_id": prompt_id, "error": str(exc)},
            )

        result = get_llm_manager(config_path=llm_config_path).check_only(llm_model)
        return PreflightCheckResult(
            component_type="generator",
            component_name=component_name,
            ok=result.ok,
            stage=PreflightStage(result.stage),
            message=result.message,
            target=str(llm_config_path),
            details={
                "llm_model": llm_model,
                "prompt_id": prompt_id,
                "llm_config_path": str(llm_config_path),
                **result.details,
            },
        )

    @staticmethod
    def build_payload(
        *,
        chain: StructuredChain,
        chunk: DocumentChunk,
        meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """构建 prompt 输入数据，尽量匹配模板变量。"""
        required = chain.required_inputs
        payload: Dict[str, Any] = {}
        prompt_meta = meta.get("prompt_meta", {}) if isinstance(meta, dict) else {}

        if "text" in required:
            payload["text"] = chunk.content
        if "chunk_info" in required:
            payload["chunk_info"] = format_dict(
                {
                    "doc_id": chunk.source_doc_id,
                    "chunk_id": chunk.chunk_id,
                    "section": chunk.section,
                }
            )
        if "meta" in required:
            payload["meta"] = format_dict(prompt_meta)
        return payload

    @staticmethod
    def build_qa(
        *,
        chunk: DocumentChunk,
        result: Dict[str, Any],
        ctx: RunContext,
        meta: Dict[str, Any],
        qa_index: int,
        generator_name: str,
        llm_model: str,
        prompt_id: str,
    ) -> QAPair:
        """将结构化链输出组装为标准 QAPair。"""
        parsed = StructuredQaSupport.extract_parse(result)
        question = (parsed.get("question") or "").strip() or "请基于文本回答问题。"
        answer = (parsed.get("answer") or "").strip() or "参考原文内容作答。"
        evidences = parsed.get("evidences") or []
        if isinstance(evidences, str):
            evidences = [evidences]
        if not evidences:
            evidences = [
                StructuredQaSupport.ensure_min_len(
                    chunk.content[:280], ctx.plan.min_evidence_len
                )
            ]

        system_meta = meta.get("system_meta", {}) if isinstance(meta, dict) else {}
        prompt_meta = meta.get("prompt_meta", {}) if isinstance(meta, dict) else {}
        labels: Dict[str, Any] = {}
        for key in ("difficulty", "question_type"):
            value = prompt_meta.get(key)
            if value:
                labels[key] = str(value)
        planner = system_meta.get("planner")
        provenance: Dict[str, Any] = {
            "run_id": ctx.run_id,
            "source_doc_id": chunk.source_doc_id,
            "chunk_id": chunk.chunk_id,
            "qa_index": qa_index,
            "line_start": chunk.metadata.get("line_start"),
            "line_end": chunk.metadata.get("line_end"),
            "generator": generator_name,
            "planner": str(planner) if planner else None,
            "plan_index": system_meta.get("plan_index"),
            "llm_name": llm_model,
            "prompt_id": prompt_id,
        }
        if result.get("error"):
            provenance["extra"] = {"error": result.get("error")}
        return QAPair(
            qa_id=build_qa_id(
                ctx.run_id,
                chunk.source_doc_id,
                chunk.chunk_id,
                qa_index,
            ),
            qa_info={
                "question": question,
                "answer": answer,
                "evidences": evidences,
                "labels": labels,
            },
            provenance=provenance,
        )

    @staticmethod
    def ensure_min_len(text: str, min_len: int) -> str:
        """保证证据文本满足最小长度要求。"""
        if len(text) >= min_len:
            return text
        return text + "." * max(0, min_len - len(text))

    @staticmethod
    def extract_parse(result: Dict[str, Any]) -> Dict[str, Any]:
        """从 StructuredChain 输出中提取 parse 字段。"""
        parsed = result.get("parse")
        if isinstance(parsed, dict):
            return parsed
        return {}

    @staticmethod
    def normalize_metas(
        metas: List[Dict[str, Any]] | None, total: int
    ) -> List[Dict[str, Any]]:
        """规范化 chunk 级元信息列表。"""
        if metas is None:
            return [{} for _ in range(total)]
        if len(metas) != total:
            raise ValueError(f"metas 长度({len(metas)})与 chunks 数量({total})不一致")
        normalized: List[Dict[str, Any]] = []
        for meta in metas:
            normalized.append(meta if isinstance(meta, dict) else {"value": meta})
        return normalized
