"""
采集管道 (Collection Pipeline)。

负责从小红书 API 采集数据：
- 达人数据
- 笔记数据
- 评论数据
"""

from .base import BaseCollector
from .celebrity import CelebAggregator
from .notes import NoteAggregator
from .comments import CommentAggregator
from .batchers import BatchCollector

__all__ = [
    "BaseCollector",
    "CelebAggregator",
    "NoteAggregator",
    "CommentAggregator",
    "BatchCollector",
]
