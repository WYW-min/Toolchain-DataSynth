from __future__ import annotations

import unittest

from tc_datasynth.core.models import QAPair
from tc_datasynth.pipeline.validator import LabelValidator, LabelValidatorConfig


class LabelValidatorTest(unittest.TestCase):
    """LabelValidator 单元测试。"""

    def test_validate_reports_invalid_labels(self) -> None:
        validator = LabelValidator(LabelValidatorConfig(reasoning_min_evidence_len=10))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["valid-evidence"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "unknown", "question_type": "invalid"},
        )

        result = validator.validate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.errors,
            ["label.invalid_difficulty", "label.invalid_question_type"],
        )

    def test_validate_reports_reasoning_context_issue(self) -> None:
        validator = LabelValidator(LabelValidatorConfig(reasoning_min_evidence_len=20))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["too short"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "medium", "question_type": "reasoning"},
        )

        result = validator.validate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, ["label.reasoning_insufficient_context"])

    def test_validate_passes_for_allowed_labels(self) -> None:
        validator = LabelValidator(LabelValidatorConfig(reasoning_min_evidence_len=10))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["sufficient-context"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "hard", "question_type": "reasoning"},
        )

        result = validator.validate(qa)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
