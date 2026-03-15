"""Unit tests for collection-layer payload normalization."""

from __future__ import annotations

import unittest

from xhs_agent.pipelines.collection.celebrity import CelebAggregator
from xhs_agent.pipelines.collection.comments import CommentAggregator
from xhs_agent.pipelines.collection.notes import NoteAggregator


class TestCollectionTransformers(unittest.TestCase):
    def test_note_converter_from_search_payload(self) -> None:
        aggregator = NoteAggregator()
        note = aggregator._convert_to_note_data(
            {
                "note_card": {
                    "note_id": "note-1",
                    "display_title": "title-a",
                    "desc": "content-a",
                    "type": "normal",
                    "user": {"user_id": "user-1", "nickname": "alice"},
                    "interact_info": {
                        "liked_count": "10",
                        "comment_count": 2,
                        "share_count": 1,
                        "collected_count": "4",
                    },
                    "time": 1_700_000_000,
                }
            },
            source_keyword="keyword-a",
        )

        self.assertEqual(note.note_id, "note-1")
        self.assertEqual(note.author_id, "user-1")
        self.assertEqual(note.author_name, "alice")
        self.assertEqual(note.likes, 10)
        self.assertEqual(note.comments_count, 2)
        self.assertEqual(note.shares, 1)
        self.assertEqual(note.collects, 4)
        self.assertEqual(note.source_search_keyword, "keyword-a")

    def test_comment_converter_from_comment_payload(self) -> None:
        aggregator = CommentAggregator()
        comment = aggregator._convert_to_comment(
            {
                "id": "comment-1",
                "content": "hello",
                "user_info": {"user_id": "user-2", "nickname": "bob"},
                "liked_count": "8",
                "sub_comment_count": 3,
                "create_time": 1_700_000_000,
            },
            note_id="note-1",
        )

        self.assertEqual(comment.comment_id, "comment-1")
        self.assertEqual(comment.note_id, "note-1")
        self.assertEqual(comment.author_id, "user-2")
        self.assertEqual(comment.author_name, "bob")
        self.assertEqual(comment.likes, 8)
        self.assertEqual(comment.replies_count, 3)

    def test_celeb_stats_from_basic_payload(self) -> None:
        aggregator = CelebAggregator()
        celeb = aggregator._calculate_celeb_stats(
            {
                "user_info": {
                    "user_id": "celeb-1",
                    "nickname": "creator",
                    "followers": "2000",
                    "signature": "bio",
                }
            },
            [
                {
                    "note_card": {
                        "title": "教程分享",
                        "desc": "如何使用产品",
                        "interact_info": {
                            "liked_count": 20,
                            "comment_count": 5,
                            "share_count": 2,
                        },
                        "time": 1_700_000_000,
                    }
                }
            ],
        )

        self.assertEqual(celeb.celeb_id, "celeb-1")
        self.assertEqual(celeb.name, "creator")
        self.assertEqual(celeb.followers, 2000)
        self.assertGreaterEqual(celeb.avg_likes_per_note, 20.0)
        self.assertTrue(len(celeb.content_styles) >= 1)


if __name__ == "__main__":
    unittest.main()
