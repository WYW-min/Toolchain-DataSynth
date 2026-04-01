from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core.config import RuntimeConfig


class RuntimeComponentConfigTest(unittest.TestCase):
    """运行配置中的组件配置加载测试。"""

    def test_from_toml_loads_component_and_runtime_paths(self) -> None:
        """应从 TOML 读取组件配置与显式日志路径。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config_path = base / "runtime.toml"
            config_path.write_text(
                """
[runtime]
input_dir = "./data/in/pdf"
output_dir = "./data/out"
logs_root_base = "./logs"
doc_limit = 2

[components.sampler]
name = "greedy_addition"
chunk_size = 900
min_sentence_len = 15
paragraph_separators = ["\\n\\n", "\\n"]

[components.generator]
name = "simple_qa"
llm_model = "doubao-flash"

[components.adapter.pdf]
name = "pdf_gpu"
server_url = "http://127.0.0.1:8000"

[components.adapter.pdf.parse_options]
backend = "hybrid-auto-engine"
parse_method = "auto"

[components.gate]
name = "simple_composite"
validators = ["simple_schema", "evidence", "label"]

[components.validator.evidence]
min_evidence_len = 120
""".strip(),
                encoding="utf-8",
            )

            config = RuntimeConfig.from_toml(config_path)

            self.assertIn("sampler", config.components)
            self.assertEqual(config.components["sampler"]["name"], "greedy_addition")
            self.assertEqual(config.components["sampler"]["chunk_size"], 900)
            self.assertEqual(config.components["sampler"]["min_sentence_len"], 15)
            self.assertIn("generator", config.components)
            self.assertEqual(config.components["generator"]["name"], "simple_qa")
            self.assertEqual(config.components["generator"]["llm_model"], "doubao-flash")
            self.assertIn("adapter", config.components)
            self.assertEqual(config.components["adapter"]["pdf"]["name"], "pdf_gpu")
            self.assertEqual(
                config.components["adapter"]["pdf"]["server_url"],
                "http://127.0.0.1:8000",
            )
            self.assertEqual(
                config.components["adapter"]["pdf"]["parse_options"]["backend"],
                "hybrid-auto-engine",
            )
            self.assertIn("gate", config.components)
            self.assertEqual(
                config.components["gate"]["validators"],
                ["simple_schema", "evidence", "label"],
            )
            self.assertIn("validator", config.components)
            self.assertEqual(
                config.components["validator"]["evidence"]["min_evidence_len"], 120
            )
            self.assertEqual(config.logs_root_base, Path("./logs"))
            self.assertEqual(config.doc_limit, 2)
