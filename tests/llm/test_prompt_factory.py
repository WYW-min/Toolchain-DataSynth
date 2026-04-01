from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tc_datasynth.core.llm.prompt_factory as prompt_factory_module
from tc_datasynth.core.llm.prompt_factory import PromptFactory, get_prompt_manager


class PromptFactoryTest(unittest.TestCase):
    """PromptFactory 占位符校验测试。"""

    def setUp(self) -> None:
        prompt_factory_module.prompt_manager = None
        PromptFactory._instance = None

    def tearDown(self) -> None:
        prompt_factory_module.prompt_manager = None
        PromptFactory._instance = None

    def test_skips_prompt_missing_required_placeholders(self) -> None:
        """缺少 schema_define/meta/text 任一占位符时应跳过并 warning。"""
        with tempfile.TemporaryDirectory() as tmp:
            prompt_dir = Path(tmp)
            (prompt_dir / "valid.txt").write_text(
                "<system>{schema_define}</system>\n<user>{meta}\n{text}</user>\n",
                encoding="utf-8",
            )
            (prompt_dir / "invalid.txt").write_text(
                "<system>{schema_define}</system>\n<user>{text}</user>\n",
                encoding="utf-8",
            )

            with patch.object(prompt_factory_module.logger, "warning") as warning_mock:
                manager = get_prompt_manager(prompt_dir=prompt_dir)

            self.assertIn("valid", manager.keys())
            self.assertNotIn("invalid", manager.keys())
            warning_mock.assert_called()
            self.assertIn("跳过提示词", warning_mock.call_args[0][0])

    def test_valid_prompt_can_be_loaded(self) -> None:
        """合法 prompt 应成功注册并暴露完整输入变量。"""
        with tempfile.TemporaryDirectory() as tmp:
            prompt_dir = Path(tmp)
            (prompt_dir / "valid.txt").write_text(
                "<system>{schema_define}</system>\n<user>{meta}\n{text}</user>\n",
                encoding="utf-8",
            )

            manager = get_prompt_manager(prompt_dir=prompt_dir)
            template = manager["valid"]

            self.assertEqual(set(template.input_variables), {"schema_define", "meta", "text"})
