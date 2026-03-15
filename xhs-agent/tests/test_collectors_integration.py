"""Integration-style tests for collector adapters with mocked XHS ports."""

from __future__ import annotations

import asyncio
import unittest

from xhs_agent.pipelines.collection.celebrity import CelebAggregator
from xhs_agent.pipelines.collection.comments import CommentAggregator
from xhs_agent.pipelines.collection.notes import NoteAggregator


class _DummyNoteClient:
    def __init__(self) -> None:
        self.search_calls: list[dict] = []

    def search_notes(self, keyword: str, sort: str, page: int, page_size: int) -> dict:
        self.search_calls.append(
            {
                "keyword": keyword,
                "sort": sort,
                "page": page,
                "page_size": page_size,
            }
        )
        if page == 1:
            return {
                "items": [
                    {"note_card": {"note_id": "note-1", "time": 1_700_000_000}},
                    {"note_card": {"note_id": "note-2", "time": 1_700_000_005}},
                ],
                "has_more": True,
            }
        if page == 2:
            return {
                "items": [{"note_card": {"note_id": "note-3", "time": 1_700_000_010}}],
                "has_more": False,
            }
        return {"items": []}

    def get_note_detail(self, note_id: str) -> dict:
        return {
            "items": [
                {
                    "note_card": {
                        "note_id": note_id,
                        "title": "detail-title",
                        "desc": "detail-content",
                        "user": {"user_id": "user-1", "nickname": "tester"},
                        "interact_info": {
                            "liked_count": 11,
                            "comment_count": 2,
                            "share_count": 1,
                        },
                        "time": 1_700_000_000,
                    }
                }
            ]
        }

    def close(self) -> None:
        return None


class _DummyCommentClient:
    def __init__(self) -> None:
        self.last_max_pages = None

    def get_all_comments(self, note_id: str, max_pages: int = 20) -> dict:
        self.last_max_pages = max_pages
        return {
            "comments": [
                {
                    "id": "comment-1",
                    "content": "hello",
                    "user_info": {"user_id": "user-2", "nickname": "commenter"},
                    "liked_count": 3,
                    "sub_comment_count": 1,
                    "create_time": 1_700_000_000,
                }
            ]
        }

    def close(self) -> None:
        return None


class _DummyCelebClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict:
        self.calls.append(cursor)
        if cursor == "":
            return {
                "notes": [{"note_card": {"title": "n1", "interact_info": {}}}],
                "has_more": True,
                "cursor": "c1",
            }
        if cursor == "c1":
            return {
                "notes": [{"note_card": {"title": "n2", "interact_info": {}}}],
                "has_more": False,
                "cursor": "",
            }
        return {"notes": [], "has_more": False, "cursor": ""}

    def get_user_info(self, user_id: str) -> dict:
        return {"user_info": {"user_id": user_id, "nickname": "tester"}}

    def close(self) -> None:
        return None


class TestCollectorsIntegration(unittest.TestCase):
    def test_note_search_pagination_and_limit(self) -> None:
        dummy = _DummyNoteClient()
        aggregator = NoteAggregator(xhs_port=dummy)

        result = asyncio.run(aggregator._search_notes(keyword="kw", sort="general", limit=3))

        self.assertEqual(len(result["items"]), 3)
        self.assertEqual(result["items"][0]["note_card"]["note_id"], "note-1")
        self.assertEqual(result["items"][1]["note_card"]["note_id"], "note-2")
        self.assertEqual(result["items"][2]["note_card"]["note_id"], "note-3")
        self.assertEqual(len(dummy.search_calls), 2)
        self.assertEqual(dummy.search_calls[0]["page"], 1)
        self.assertEqual(dummy.search_calls[1]["page"], 2)

    def test_note_detail_extracts_first_note_card(self) -> None:
        aggregator = NoteAggregator(xhs_port=_DummyNoteClient())

        detail = asyncio.run(aggregator._get_note_detail("note-x"))
        self.assertIsInstance(detail, dict)
        self.assertEqual(detail["note_id"], "note-x")
        self.assertEqual(detail["title"], "detail-title")

    def test_comment_collect_single_is_explicitly_unsupported(self) -> None:
        aggregator = CommentAggregator()

        with self.assertRaises(NotImplementedError):
            asyncio.run(aggregator.collect_single("comment-id"))

    def test_comment_fetch_uses_paged_endpoint(self) -> None:
        dummy = _DummyCommentClient()
        aggregator = CommentAggregator(xhs_port=dummy)

        comments = asyncio.run(aggregator._get_note_comments("note-1", limit=45))

        self.assertEqual(dummy.last_max_pages, 3)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["id"], "comment-1")

    def test_celeb_notes_pagination(self) -> None:
        dummy = _DummyCelebClient()
        aggregator = CelebAggregator(xhs_port=dummy)

        notes = asyncio.run(aggregator._get_user_notes("user-1", limit=5))

        self.assertEqual(len(notes), 2)
        self.assertEqual(dummy.calls, ["", "c1"])


if __name__ == "__main__":
    unittest.main()
