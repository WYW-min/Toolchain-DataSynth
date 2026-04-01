from __future__ import annotations

import unittest
from dataclasses import dataclass

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.gate import SimpleCompositeGate, SimpleCompositeGateConfig
from tc_datasynth.pipeline.validator import ValidatorBase, ValidatorConfigBase


@dataclass(slots=True)
class _StubValidatorConfig(ValidatorConfigBase):
    pass


class _StubValidator(ValidatorBase[_StubValidatorConfig]):
    def __init__(self, errors: list[str]) -> None:
        super().__init__(_StubValidatorConfig())
        self._errors = errors

    @classmethod
    def default_config(cls) -> _StubValidatorConfig:
        return _StubValidatorConfig()

    def validate(self, qa: QAPair) -> ValidationResult:
        return ValidationResult(qa=qa, errors=list(self._errors))


class SimpleCompositeGateTest(unittest.TestCase):
    """SimpleCompositeGate 单元测试。"""

    def test_evaluate_stops_on_first_error_by_default(self) -> None:
        qa = _make_qa()
        gate = SimpleCompositeGate(
            validators=[
                _StubValidator(["error:first"]),
                _StubValidator(["error:second"]),
            ]
        )

        result = gate.evaluate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.action, "reject")
        self.assertEqual(result.stage, "gate")
        self.assertEqual(result.errors, ["error:first"])

    def test_evaluate_can_aggregate_all_errors(self) -> None:
        qa = _make_qa()
        gate = SimpleCompositeGate(
            validators=[
                _StubValidator(["error:first"]),
                _StubValidator(["error:second"]),
            ],
            config=SimpleCompositeGateConfig(stop_on_first_error=False),
        )

        result = gate.evaluate(qa)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.action, "reject")
        self.assertEqual(result.errors, ["error:first", "error:second"])

    def test_evaluate_passes_when_all_validators_pass(self) -> None:
        qa = _make_qa()
        gate = SimpleCompositeGate(validators=[_StubValidator([])])

        result = gate.evaluate(qa)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.action, "pass")
        self.assertEqual(result.errors, [])


def _make_qa() -> QAPair:
    return QAPair(
        question="Q?",
        answer="A.",
        evidences=["e1"],
        source_doc_id="doc1",
        chunk_id="chunk1",
        metadata={},
    )
