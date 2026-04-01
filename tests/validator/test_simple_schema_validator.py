from __future__ import annotations

import unittest

from tc_datasynth.core.models import QAPair
from tc_datasynth.pipeline.validator import SimpleSchemaValidator


class SimpleSchemaValidatorTest(unittest.TestCase):
    """SimpleSchemaValidator 单元测试。"""

    def test_validate_passes_complete_qa(self) -> None:
        """字段完整时应通过。"""
        validator = SimpleSchemaValidator()
        qa = QAPair(
            question="Q?",
            answer="A.",
            evidences=["e1"],
            source_doc_id="doc1",
            chunk_id="chunk1",
            metadata={},
        )

        result = validator.validate(qa)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_validate_reports_missing_fields(self) -> None:
        """缺失字段时应产出对应错误码。"""
        validator = SimpleSchemaValidator()
        qa = QAPair(
            question="",
            answer="A.",
            evidences=[],
            source_doc_id="doc1",
            chunk_id="",
            metadata={},
        )

        result = validator.validate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.errors,
            [
                "schema.missing_question",
                "schema.missing_evidences",
                "schema.missing_chunk_id",
            ],
        )
