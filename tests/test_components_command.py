from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from tc_datasynth.component_catalog import format_component_catalog
from tc_datasynth.main import main


class ComponentsCommandTest(unittest.TestCase):
    """components 子命令测试。"""

    def test_format_component_catalog_contains_registered_rows(self) -> None:
        output = format_component_catalog()
        self.assertIn("sampler:", output)
        self.assertIn("  - greedy_addition | GreedyAdditionSampler", output)
        self.assertIn("  - simple_chunk | SimpleChunkSampler", output)
        self.assertIn("planner:", output)
        self.assertIn("  - simple | SimplePlanner", output)

    def test_main_components_command_prints_catalog(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["components"])
        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("已注册组件:", output)
        self.assertIn("generator:", output)
        self.assertIn("  - mock | MockQAGenerator", output)
