"""Tests for configurable XHS integration factory."""

from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

from xhs_agent.integrations import (
    XHS_BACKEND_ENV,
    create_xhs_port,
    register_xhs_backend,
)
from xhs_agent.pipelines.collection.notes import NoteAggregator


class _DummyPort:
    def search_notes(self, keyword: str, sort: str, page: int, page_size: int) -> dict:
        return {"items": [], "has_more": False}

    def get_note_detail(self, note_id: str) -> dict:
        return {"items": []}

    def get_user_info(self, user_id: str) -> dict:
        return {"user_info": {"user_id": user_id}}

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict:
        return {"items": [], "has_more": False, "cursor": ""}

    def get_all_comments(self, note_id: str, max_pages: int = 20) -> dict:
        return {"comments": []}

    def close(self) -> None:
        return None


def _build_python_port() -> _DummyPort:
    return _DummyPort()


class TestXhsFactory(unittest.TestCase):
    def test_create_xhs_port_from_registered_backend(self) -> None:
        register_xhs_backend("dummy_reg", _build_python_port)

        port = create_xhs_port("dummy_reg")

        self.assertIsInstance(port, _DummyPort)

    def test_create_xhs_port_from_python_factory_path(self) -> None:
        port = create_xhs_port("python:tests.test_xhs_factory:_build_python_port")

        self.assertIsInstance(port, _DummyPort)

    def test_create_xhs_port_from_env_backend(self) -> None:
        with patch.dict(
            os.environ,
            {XHS_BACKEND_ENV: "python:tests.test_xhs_factory:_build_python_port"},
            clear=False,
        ):
            port = create_xhs_port()

        self.assertIsInstance(port, _DummyPort)

    def test_unknown_backend_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            create_xhs_port("unknown_backend_for_test")

    def test_collector_init_uses_configured_backend(self) -> None:
        aggregator = NoteAggregator(xhs_backend="dummy-backend")

        with patch(
            "xhs_agent.pipelines.collection.notes.create_xhs_port",
            return_value=_DummyPort(),
        ) as mock_factory:
            asyncio.run(aggregator.init_xhs_client())

        mock_factory.assert_called_once_with("dummy-backend")


if __name__ == "__main__":
    unittest.main()
