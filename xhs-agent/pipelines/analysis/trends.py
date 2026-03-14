"""
趋势分析模块。

分析多个笔记的聚合数据，识别：
- 热词趋势
- 内容风格转变
- 季节性模式
- 竞品对标
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Optional

from xhs_agent.types import NoteWithComments, PerformanceMetrics, SentimentReport
from .base import AnalysisLogger

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    趋势分析器。

    分析多个笔记的聚合表现，识别内容和市场趋势。

    使用方式:
        analyzer = TrendAnalyzer()
        trends = analyzer.analyze_trend(notes_with_comments)
        print(f"热词: {trends['hot_keywords']}")
    """

    def __init__(self):
        """初始化趋势分析器"""
        pass

    def analyze_trend(
        self,
        notes_with_comments: list[NoteWithComments],
        metrics: Optional[list[PerformanceMetrics]] = None,
        sentiments: Optional[list[SentimentReport]] = None,
    ) -> dict:
        """
        分析多个笔记的聚合趋势。

        Args:
            notes_with_comments: 笔记列表
            metrics: 表现指标列表（可选）
            sentiments: 情感分析报告列表（可选）

        Returns:
            趋势分析结果字典
        """
        try:
            logger.info("Analyzing trends for %d notes", len(notes_with_comments))

            result = {
                "hot_keywords": self._extract_hot_keywords(notes_with_comments),
                "content_styles": self._analyze_content_styles(notes_with_comments),
                "top_performers": self._identify_top_performers(
                    notes_with_comments, metrics
                ),
                "common_pain_points": self._aggregate_pain_points(sentiments),
                "trending_emotions": self._aggregate_emotions(sentiments),
                "seasonal_pattern": self._detect_seasonal_pattern(notes_with_comments),
                "competitor_insights": self._identify_competitor_insights(
                    notes_with_comments
                ),
            }

            return result

        except Exception as e:
            logger.error("Failed to analyze trends: %s", str(e))
            raise

    def _extract_hot_keywords(
        self,
        notes_with_comments: list[NoteWithComments],
    ) -> list[tuple[str, int]]:
        """
        提取热词。

        从所有笔记和评论中提取高频词汇。

        Args:
            notes_with_comments: 笔记列表

        Returns:
            热词及其频率列表 [(keyword, count), ...]
        """
        keyword_counter = Counter()

        # 从笔记标题和内容中提取
        for item in notes_with_comments:
            note = item.note

            # 笔记标题权重高
            for word in self._tokenize(note.title):
                keyword_counter[word] += 3

            # 笔记内容
            for word in self._tokenize(note.content):
                keyword_counter[word] += 1

            # 评论内容
            for comment in item.comments:
                for word in self._tokenize(comment.content):
                    keyword_counter[word] += 1

        # 过滤掉停用词和短词
        filtered = {
            word: count
            for word, count in keyword_counter.items()
            if len(word) >= 2 and word not in self._get_stopwords()
        }

        # 返回频率最高的 20 个
        return sorted(
            filtered.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:20]

    def _analyze_content_styles(
        self,
        notes_with_comments: list[NoteWithComments],
    ) -> dict[str, int]:
        """
        分析内容风格分布。

        统计不同内容风格的笔记数量。

        Args:
            notes_with_comments: 笔记列表

        Returns:
            风格及其频率
        """
        styles = {
            "tutorial": 0,  # 教程型
            "story": 0,  # 故事型
            "daily": 0,  # 日常型
            "expert": 0,  # 专家型
            "review": 0,  # 评测型
        }

        for item in notes_with_comments:
            note = item.note
            content = (note.title + note.content).lower()

            # 教程型
            if any(w in content for w in ["教程", "步骤", "怎么", "如何", "指南"]):
                styles["tutorial"] += 1

            # 故事型
            if any(w in content for w in ["分享", "我的", "经历", "故事", "日常"]):
                styles["story"] += 1

            # 专家型
            if any(w in content for w in ["分析", "原理", "科学", "成分", "原因"]):
                styles["expert"] += 1

            # 评测型
            if any(w in content for w in ["评测", "对比", "测评", "试用", "体验"]):
                styles["review"] += 1

            # 默认日常型
            if styles.get("daily", 0) == 0:
                styles["daily"] += 1

        return styles

    def _identify_top_performers(
        self,
        notes_with_comments: list[NoteWithComments],
        metrics: Optional[list[PerformanceMetrics]] = None,
    ) -> list[dict]:
        """
        识别表现最好的笔记。

        Args:
            notes_with_comments: 笔记列表
            metrics: 表现指标列表

        Returns:
            表现最好的笔记信息
        """
        if not metrics:
            # 如果没有提供指标，使用基础互动数估计
            scored_notes = [
                {
                    "note_id": item.note.note_id,
                    "title": item.note.title,
                    "engagement": (
                        item.note.likes +
                        item.note.comments_count +
                        item.note.collects
                    ),
                }
                for item in notes_with_comments
            ]
        else:
            scored_notes = [
                {
                    "note_id": m.note_id,
                    "title": next(
                        (item.note.title for item in notes_with_comments
                         if item.note.note_id == m.note_id),
                        ""
                    ),
                    "heat_score": m.heat_score,
                    "virality_score": m.virality_score,
                }
                for m in metrics
            ]

        # 排序并返回前 5 个
        if metrics:
            sorted_notes = sorted(
                scored_notes,
                key=lambda x: x.get("heat_score", 0),
                reverse=True,
            )
        else:
            sorted_notes = sorted(
                scored_notes,
                key=lambda x: x.get("engagement", 0),
                reverse=True,
            )

        return sorted_notes[:5]

    def _aggregate_pain_points(
        self,
        sentiments: Optional[list[SentimentReport]],
    ) -> list[str]:
        """
        聚合所有笔记的用户痛点。

        Args:
            sentiments: 情感分析报告列表

        Returns:
            按频率排序的痛点列表
        """
        if not sentiments:
            return []

        pain_point_counter = Counter()

        for report in sentiments:
            for point in report.top_pain_points:
                pain_point_counter[point] += 1

        # 返回频率最高的 10 个
        return [
            point for point, _ in
            pain_point_counter.most_common(10)
        ]

    def _aggregate_emotions(
        self,
        sentiments: Optional[list[SentimentReport]],
    ) -> list[str]:
        """
        聚合所有笔记的用户情绪。

        Args:
            sentiments: 情感分析报告列表

        Returns:
            按强度排序的情绪列表
        """
        if not sentiments:
            return []

        emotion_counter = Counter()

        for report in sentiments:
            for emotion in report.top_emotions:
                emotion_counter[emotion] += 1

        # 返回频率最高的 5 个
        return [
            emotion for emotion, _ in
            emotion_counter.most_common(5)
        ]

    def _detect_seasonal_pattern(
        self,
        notes_with_comments: list[NoteWithComments],
    ) -> dict:
        """
        检测季节性模式。

        基于笔记的发布时间和内容。

        Args:
            notes_with_comments: 笔记列表

        Returns:
            季节性分析结果
        """
        months = {}

        for item in notes_with_comments:
            try:
                from datetime import datetime
                pub_time = item.note.published_at
                if isinstance(pub_time, str):
                    pub_time = datetime.fromisoformat(
                        pub_time.replace("Z", "+00:00")
                    )

                month = pub_time.month
                months[month] = months.get(month, 0) + 1

            except (ValueError, AttributeError, TypeError):
                continue

        return {
            "peak_months": sorted(
                months.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3] if months else [],
            "is_seasonal": len(months) >= 6,  # 至少跨越 6 个月才算季节性
        }

    def _identify_competitor_insights(
        self,
        notes_with_comments: list[NoteWithComments],
    ) -> dict:
        """
        识别竞品学习点。

        从笔记中提取竞品的成功策略。

        Args:
            notes_with_comments: 笔记列表

        Returns:
            竞品学习点
        """
        insights = {
            "successful_angles": [],  # 成功的内容角度
            "common_structures": [],  # 常见的笔记结构
            "successful_ctas": [],  # 有效的 CTA
        }

        # 提取高互动笔记的特征
        high_engagement_notes = sorted(
            notes_with_comments,
            key=lambda x: (
                x.note.likes +
                x.note.comments_count +
                x.note.collects
            ),
            reverse=True,
        )[:5]

        for item in high_engagement_notes:
            note = item.note

            # 分析标题角度
            if "对比" in note.title or "vs" in note.title:
                insights["successful_angles"].append("对比式")
            if "终于" in note.title or "我" in note.title:
                insights["successful_angles"].append("故事式")
            if any(w in note.title for w in ["指南", "教程", "秘诀"]):
                insights["successful_angles"].append("教程式")

            # 分析结构
            content = note.content
            if len(content) > 500:
                insights["common_structures"].append("长文详细")
            if "\n" in content:
                insights["common_structures"].append("分段清晰")

        # 去重和统计
        from collections import Counter
        insights["successful_angles"] = [
            angle for angle, _ in
            Counter(insights["successful_angles"]).most_common(3)
        ]
        insights["common_structures"] = [
            struct for struct, _ in
            Counter(insights["common_structures"]).most_common(3)
        ]

        return insights

    def _tokenize(self, text: str) -> list[str]:
        """
        简单的分词器。

        实际应该用专业的 NLP 分词库（如 jieba）。

        Args:
            text: 输入文本

        Returns:
            词列表
        """
        import re

        # 提取中文、英文和数字
        words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text)
        return words

    def _get_stopwords(self) -> set:
        """获取停用词列表"""
        return {
            "的", "了", "和", "是", "在", "我", "有", "人", "这", "中",
            "大", "为", "上", "个", "国", "以", "要", "他", "时", "来",
            "用", "们", "生", "到", "作", "地", "于", "出", "就", "分",
            "对", "成", "会", "可", "主", "发", "年", "动", "同", "工",
            "也", "能", "下", "过", "民", "前", "面", "方", "现", "系",
            "心", "各", "好", "样", "只", "便", "又", "没", "多", "育",
            "从", "训", "向", "着", "包", "都", "通", "能", "方", "面",
        }


# 便利函数
def analyze_market_trends(
    notes_with_comments: list[NoteWithComments],
) -> dict:
    """
    快速分析市场趋势。

    Args:
        notes_with_comments: 笔记列表

    Returns:
        趋势分析结果

    示例:
        trends = analyze_market_trends(notes)
        print(f"热词: {trends['hot_keywords']}")
    """
    analyzer = TrendAnalyzer()
    return analyzer.analyze_trend(notes_with_comments)
