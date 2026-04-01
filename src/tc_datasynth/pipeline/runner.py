from __future__ import annotations

"""
编排器：串联各个组件并输出产物。
"""

from time import perf_counter
from typing import List, Tuple

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, QAPair, RunArtifacts, SourceDocument
from tc_datasynth.pipeline.batching import (
    BatchExecutor,
    batch_items,
    format_batch_size,
    normalize_batch_size,
)
from tc_datasynth.pipeline.components import PipelineComponents
from tc_datasynth.pipeline.progress import ProgressTracker
from tc_datasynth.reporting import write_run_report, write_stage_manifests


class PipelineRunner:
    """负责 orchestrate 全流程，从发现输入到落盘产物。"""

    def __init__(
        self,
        components: PipelineComponents,
        context: RunContext,
    ) -> None:
        """注入流水线组件与运行上下文。"""
        self.components = components
        self.ctx = context
        self.logger = context.logger

    def run(self, doc_limit: int | None = None) -> RunArtifacts:
        """执行完整流水线，可限制处理文档数量。"""
        start_time = perf_counter()
        components = self.components
        run_id = self.ctx.run_id
        components.writer.prepare(run_id)
        documents = components.reader.discover(limit=doc_limit)
        doc_count = len(documents)
        self.logger.info(f"发现文档数量: {doc_count}")
        self.logger.info(
            f"Plan: difficulty={self.ctx.plan.difficulty_profile}, "
            f"qtypes={self.ctx.plan.question_type_mix}, "
            f"min_evidence_len={self.ctx.plan.min_evidence_len}"
        )
        parse_batch_size = normalize_batch_size(self.ctx.config.parse_batch_size)
        generate_batch_size = normalize_batch_size(self.ctx.config.generate_batch_size)
        qa_limit = RuntimeConfig.normalize_batch_size(self.ctx.config.limit, default=None)
        self.logger.info(
            "批处理设置: "
            f"parse_batch_size={format_batch_size(parse_batch_size)}, "
            f"generate_batch_size={format_batch_size(generate_batch_size)}"
        )
        self.logger.info(f"QA 上限: {format_batch_size(qa_limit)}")

        final_records: List[QAPair] = []
        failed_records: List[dict] = []

        progress = ProgressTracker.create(doc_count)
        executor = BatchExecutor(components=components, ctx=self.ctx, logger=self.logger)
        pending: List[Tuple[SourceDocument, IntermediateRepresentation]] = []
        parsed_total = 0
        generated_total = 0
        limit_reached = False
        for batch in batch_items(documents, parse_batch_size):
            parsed_items = executor.parse_documents(batch, progress)
            parsed_total += len(parsed_items)
            pending.extend(parsed_items)
            if generate_batch_size is None:
                continue
            while len(pending) >= generate_batch_size:
                current_batch = pending[:generate_batch_size]
                del pending[:generate_batch_size]
                generated_docs, limit_reached = executor.generate_from_parsed(
                    current_batch,
                    final_records,
                    failed_records,
                    progress,
                    qa_limit=qa_limit,
                )
                generated_total += generated_docs
                if limit_reached:
                    break
            if limit_reached:
                break
        self.logger.info(f"解析阶段完成: parsed={parsed_total}")
        if pending and not limit_reached:
            generated_docs, limit_reached = executor.generate_from_parsed(
                pending,
                final_records,
                failed_records,
                progress,
                qa_limit=qa_limit,
            )
            generated_total += generated_docs
        self.logger.info(f"生成阶段完成: generated_docs={generated_total}")
        progress.close()

        final_path, failed_path = components.writer.write(final_records, failed_records)
        self.logger.info(f"产物写入完成: final={final_path}, failed={failed_path}")
        manifest_paths = write_stage_manifests(
            components.writer.output_dir,
            self.ctx.extras.get("stage_manifests", {}),
            plan=self.ctx.plan,
        )
        self.logger.info(f"阶段索引生成完成: count={len(manifest_paths)}")
        runtime_seconds = round(perf_counter() - start_time, 4)
        report_path = write_run_report(
            components.writer.output_dir,
            run_id,
            generated_total,
            final_records,
            failed_records,
            final_path,
            failed_path,
            manifest_paths,
            intermediate_path=self.ctx.temp_root,
            runtime_seconds=runtime_seconds,
        )
        self.logger.info(f"报告生成完成: {report_path}")

        artifacts = RunArtifacts(
            run_id=run_id,
            output_dir=components.writer.output_dir,
            final_qa_path=final_path,
            failed_cases_path=failed_path,
            report_path=report_path,
            documents_processed=generated_total,
            qa_count=len(final_records),
            failed_count=len(failed_records),
            runtime_seconds=runtime_seconds,
        )
        self.logger.info(
            f"运行完成 {run_id}: QA={artifacts.qa_count}, 失败={artifacts.failed_count}, 耗时={artifacts.runtime_seconds}s, 输出目录={artifacts.output_dir}"
        )
        return artifacts
