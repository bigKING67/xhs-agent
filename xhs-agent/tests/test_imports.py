"""Smoke tests for package-level imports."""

from __future__ import annotations

import importlib
import unittest


class TestPackageImports(unittest.TestCase):
    def test_import_xhs_agent_package(self) -> None:
        module = importlib.import_module("xhs_agent")
        self.assertTrue(hasattr(module, "__all__"))
        self.assertTrue(hasattr(module, "__version__"))

    def test_import_core_symbols(self) -> None:
        from xhs_agent.pipelines.collection import (
            CelebAggregator,
            CommentAggregator,
            NoteAggregator,
        )
        from xhs_agent.storage import JSONStorage
        from xhs_agent.strategy import StrategyGenerator

        self.assertIsNotNone(NoteAggregator)
        self.assertIsNotNone(CommentAggregator)
        self.assertIsNotNone(CelebAggregator)
        self.assertIsNotNone(StrategyGenerator)
        self.assertIsNotNone(JSONStorage)


if __name__ == "__main__":
    unittest.main()
