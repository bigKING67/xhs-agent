"""
分析管道的基类和接口定义。

负责对采集数据进行分析，生成结构化的洞察。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from xhs_agent.types import NoteWithComments, PerformanceMetrics, SentimentReport

logger = logging.getLogger(__name__)

T = TypeVar("T")  # 泛型，表示分析的输入类型
R = TypeVar("R")  # 泛型，表示分析的输出类型


class BaseAnalyzer(ABC, Generic[T, R]):
    """
    分析器基类。

    所有分析器都继承此类，实现：
    - 数据分析逻辑
    - 结果计算和验证
    - 日志记录
    """

    def __init__(self):
        """初始化分析器"""
        pass

    @abstractmethod
    def analyze(self, data: T) -> R:
        """
        同步分析（抽象方法）。

        Args:
            data: 输入数据

        Returns:
            分析结果
        """
        raise NotImplementedError("Subclass must implement analyze()")

    @abstractmethod
    def batch_analyze(self, data_list: list[T]) -> list[R]:
        """
        批量分析（抽象方法）。

        Args:
            data_list: 输入数据列表

        Returns:
            分析结果列表
        """
        raise NotImplementedError("Subclass must implement batch_analyze()")


class PerformanceAnalyzer(BaseAnalyzer[NoteWithComments, PerformanceMetrics]):
    """
    笔记表现分析器。

    分析笔记的互动表现、热度、传播力、转化潜力。
    """

    def __init__(self, heat_weights: dict | None = None):
        """
        初始化表现分析器。

        Args:
            heat_weights: 热度评分的权重字典
                {
                    "likes": 0.4,
                    "comments": 0.35,
                    "shares": 0.25,
                }
        """
        super().__init__()
        self.heat_weights = heat_weights or {
            "likes": 0.4,
            "comments": 0.35,
            "shares": 0.25,
        }

    def analyze(self, data: NoteWithComments) -> PerformanceMetrics:
        """分析单个笔记的表现"""
        pass

    def batch_analyze(self, data_list: list[NoteWithComments]) -> list[PerformanceMetrics]:
        """批量分析笔记表现"""
        pass


class SentimentAnalyzer(BaseAnalyzer[NoteWithComments, SentimentReport]):
    """
    评论情感分析器。

    分析评论的情感分布、用户痛点、话题提取、购买信号。
    """

    def __init__(
        self,
        positive_keywords: list[str] | None = None,
        negative_keywords: list[str] | None = None,
        purchase_signal_keywords: list[str] | None = None,
    ):
        """
        初始化情感分析器。

        Args:
            positive_keywords: 正面词汇列表
            negative_keywords: 负面词汇列表
            purchase_signal_keywords: 购买信号词汇列表
        """
        super().__init__()
        self.positive_keywords = positive_keywords or []
        self.negative_keywords = negative_keywords or []
        self.purchase_signal_keywords = purchase_signal_keywords or []

    def analyze(self, data: NoteWithComments) -> SentimentReport:
        """分析单个笔记的评论情感"""
        pass

    def batch_analyze(self, data_list: list[NoteWithComments]) -> list[SentimentReport]:
        """批量分析评论情感"""
        pass


class AnalysisLogger:
    """分析过程的日志和统计"""

    def __init__(self):
        self.total_items: int = 0
        self.success_count: int = 0
        self.failed_count: int = 0
        self.errors: list[str] = []

    def record_success(self, item_id: str):
        """记录成功的分析"""
        self.success_count += 1
        logger.debug("Analysis succeeded: %s", item_id)

    def record_failure(self, item_id: str, error: str):
        """记录失败的分析"""
        self.failed_count += 1
        self.errors.append(f"{item_id}: {error}")
        logger.warning("Analysis failed for %s: %s", item_id, error)

    def print_summary(self):
        """打印分析总结"""
        logger.info(
            "Analysis Summary: %d succeeded, %d failed",
            self.success_count,
            self.failed_count,
        )
        if self.errors and len(self.errors) <= 10:
            for error in self.errors:
                logger.warning("  Error: %s", error)
