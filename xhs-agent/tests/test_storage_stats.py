"""Tests for JSON storage stats and note counting behavior."""

from __future__ import annotations

import shutil
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from xhs_agent.storage import JSONStorage
from xhs_agent.types import Comment, NoteData, NoteWithComments


class TestJSONStorageStats(unittest.TestCase):
    def test_stats_count_notes_without_comments_files(self) -> None:
        temp_root = Path("tests") / ".tmp-storage-tests"
        temp_root.mkdir(parents=True, exist_ok=True)
        temp_dir = temp_root / f"case-{uuid4().hex}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            storage = JSONStorage(path=str(temp_dir))

            note = NoteData(
                note_id="note-1",
                title="title",
                content="content",
                author_id="user-1",
                author_name="alice",
                published_at=datetime(2026, 3, 14, 10, 0, 0),
            )
            comment = Comment(
                comment_id="comment-1",
                note_id="note-1",
                author_id="user-2",
                author_name="bob",
                content="nice",
                published_at=datetime(2026, 3, 14, 11, 0, 0),
            )

            self.assertTrue(storage.save_note_with_comments(NoteWithComments(note=note, comments=[comment])))

            stats = storage.get_stats()
            self.assertEqual(stats["notes"], 1)
            self.assertEqual(stats["celebrities"], 0)
            self.assertEqual(stats["strategy_plans"], 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
