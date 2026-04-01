from __future__ import annotations

import unittest

from tc_datasynth.core.models import QAPair
from tc_datasynth.pipeline.validator import EvidenceValidator, EvidenceValidatorConfig


class EvidenceValidatorTest(unittest.TestCase):
    """EvidenceValidator 单元测试。"""

    def test_validate_reports_empty_evidence(self) -> None:
        validator = EvidenceValidator(EvidenceValidatorConfig(min_evidence_len=10))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=[],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "easy", "question_type": "definition"},
        )

        result = validator.validate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, ["evidence.empty"])

    def test_validate_reports_too_short_evidence(self) -> None:
        validator = EvidenceValidator(EvidenceValidatorConfig(min_evidence_len=10))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["short"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "easy", "question_type": "definition"},
        )

        result = validator.validate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, ["evidence.too_short"])

    def test_validate_passes_when_long_enough(self) -> None:
        validator = EvidenceValidator(EvidenceValidatorConfig(min_evidence_len=10))
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["long-enough-evidence"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={"difficulty": "easy", "question_type": "definition"},
        )

        result = validator.validate(qa)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
