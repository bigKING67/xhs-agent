"""
分析管道协调器。

将表现分析、情感分析、趋势分析的结果组合成策略信号。
"""

from __future__ import annotations

import logging
from typing import Optional

from xhs_agent.types import (
    NoteWithComments,
    PerformanceMetrics,
    SentimentReport,
    StrategySignals,
)
from .performance import NotePerformanceAnalyzer
from .sentiment import CommentSentimentAnalyzer
from .trends import TrendAnalyzer

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    分析管道协调器。

    协调多个分析器，将结果组合成策略信号。

    使用方式:
        orchestrator = AnalysisOrchestrator()
        signals = await orchestrator.analyze_for_strategy(
            notes_with_comments=notes,
            reference_notes=reference_notes
        )
    """

    def __init__(self):
        """初始化协调器"""
        self.performance_analyzer = NotePerformanceAnalyzer()
        self.sentiment_analyzer = CommentSentimentAnalyzer()
        self.trend_analyzer = TrendAnalyzer()

    async def analyze_for_strategy(
        self,
        notes_with_comments: list[NoteWithComments],
        reference_notes: Optional[list[NoteWithComments]] = None,
    ) -> list[StrategySignals]:
        """
        为策略生成阶段准备分析信号。

        Args:
            notes_with_comments: 笔记列表（用于最终方案的笔记）
            reference_notes: 参考笔记列表（用于趋势分析，可选）

        Returns:
            策略信号列表，每个笔记对应一个
        """
        logger.info(
            "Analyzing %d notes for strategy generation",
            len(notes_with_comments),
        )

        # Step 1: 表现分析
        logger.info("Step 1: Analyzing note performance...")
        performance_metrics = self.performance_analyzer.batch_analyze(
            notes_with_comments
        )

        # Step 2: 情感分析
        logger.info("Step 2: Analyzing comment sentiment...")
        sentiment_reports = self.sentiment_analyzer.batch_analyze(
            notes_with_comments
        )

        # Step 3: 趋势分析（使用参考笔记）
        logger.info("Step 3: Analyzing market trends...")
        trend_data = self.trend_analyzer.analyze_trend(
            notes_with_comments=reference_notes or notes_with_comments,
            metrics=performance_metrics,
            sentiments=sentiment_reports,
        )

        # Step 4: 组合成策略信号
        logger.info("Step 4: Generating strategy signals...")
        signals = []

        for i, note in enumerate(notes_with_comments):
            metrics = performance_metrics[i]
            sentiment = sentiment_reports[i]

            signal = self._create_strategy_signal(
                note=note,
                metrics=metrics,
                sentiment=sentiment,
                trends=trend_data,
            )

            signals.append(signal)

        logger.info("Generated %d strategy signals", len(signals))
        return signals

    def _create_strategy_signal(
        self,
        note: NoteWithComments,
        metrics: PerformanceMetrics,
        sentiment: SentimentReport,
        trends: dict,
    ) -> StrategySignals:
        """
        为单个笔记创建策略信号。

        Args:
            note: 笔记
            metrics: 表现指标
            sentiment: 情感分析
            trends: 趋势数据

        Returns:
            策略信号
        """
        # 1. 确定核心切入点
        top_pain_point = (
            sentiment.top_pain_points[0]
            if sentiment.top_pain_points
            else "产品体验"
        )

        # 2. 识别有效框架
        top_performing_frames = self._infer_effective_frames(
            metrics=metrics,
            sentiment=sentiment,
        )

        # 3. 确定目标情绪
        user_emotions = (
            sentiment.top_emotions[:3]
            if sentiment.top_emotions
            else ["获得感", "安心感"]
        )

        # 4. 识别竞品学习点
        competitor_insights = self._format_competitor_insights(
            trends=trends,
            sentiment=sentiment,
        )

        # 5. 生成内容角度建议
        content_angle = self._recommend_content_angle(
            metrics=metrics,
            sentiment=sentiment,
            pain_point=top_pain_point,
        )

        # 6. 计算信号置信度
        confidence = self._calculate_confidence(metrics, sentiment)

        return StrategySignals(
            note_id=note.note.note_id,
            top_pain_point=top_pain_point,
            top_performing_frames=top_performing_frames,
            user_emotions=user_emotions,
            competitor_insights=competitor_insights,
            content_angle_recommendation=content_angle,
            signal_confidence=confidence,
            source_metrics=metrics,
            source_sentiment=sentiment,
        )

    def _infer_effective_frames(
        self,
        metrics: PerformanceMetrics,
        sentiment: SentimentReport,
    ) -> list[str]:
        """
        推断最有效的叙述框架。

        基于表现和情感数据。

        Args:
            metrics: 表现指标
            sentiment: 情感分析

        Returns:
            有效框架列表
        """
        frames = []

        # 如果热度高，问题-分析-解决方案框架有效
        if metrics.heat_score > 70:
            frames.append("问题-分析-解决方案")

        # 如果有明确痛点，对比框架有效
        if sentiment.top_pain_points:
            frames.append("对比式转变")

        # 如果正面比例高，故事分享框架有效
        if sentiment.positive_ratio > 0.7:
            frames.append("真实体验分享")

        # 如果转化潜力高，功效展示框架有效
        if metrics.conversion_potential > 70:
            frames.append("功效展示证明")

        # 如果评论多，社群共鸣框架有效
        if sentiment.total_comments > 100:
            frames.append("社群共鸣讨论")

        return frames or ["问题-分析-解决方案"]  # 默认框架

    def _recommend_content_angle(
        self,
        metrics: PerformanceMetrics,
        sentiment: SentimentReport,
        pain_point: str,
    ) -> str:
        """
        推荐内容角度。

        Args:
            metrics: 表现指标
            sentiment: 情感分析
            pain_point: 核心痛点

        Returns:
            推荐角度
        """
        # 根据痛点和情感推荐角度
        if "黑眼圈" in pain_point:
            angle = f"{pain_point}自救指南"
        elif "细纹" in pain_point:
            angle = f"{pain_point}克星"
        elif "暗沉" in pain_point:
            angle = f"{pain_point}改善方案"
        else:
            angle = f"{pain_point}解决方案"

        # 如果有明确的购买驱动力，融合到角度中
        if sentiment.purchase_drivers:
            driver = sentiment.purchase_drivers[0]
            if "快速" in driver or "见效" in driver:
                angle += "（快速见效）"
            elif "性价比" in driver or "划算" in driver:
                angle += "（性价比高）"

        return angle

    def _format_competitor_insights(
        self,
        trends: dict,
        sentiment: SentimentReport,
    ) -> str:
        """
        格式化竞品学习点。

        Args:
            trends: 趋势数据
            sentiment: 情感分析

        Returns:
            学习点文本
        """
        insights = []

        # 从趋势中提取学习点
        if "competitor_insights" in trends:
            angles = trends["competitor_insights"].get(
                "successful_angles", []
            )
            if angles:
                insights.append(f"成功角度: {', '.join(angles)}")

            structures = trends["competitor_insights"].get(
                "common_structures", []
            )
            if structures:
                insights.append(f"内容结构: {', '.join(structures)}")

        # 从情感中提取学习点
        if sentiment.top_emotions:
            insights.append(
                f"情绪触发: {', '.join(sentiment.top_emotions)}"
            )

        return " | ".join(insights) if insights else "竞品内容风格参考"

    def _calculate_confidence(
        self,
        metrics: PerformanceMetrics,
        sentiment: SentimentReport,
    ) -> float:
        """
        计算策略信号的置信度。

        Args:
            metrics: 表现指标
            sentiment: 情感分析

        Returns:
            置信度（0-1）
        """
        confidence_score = 0.0

        # 热度高加分
        confidence_score += metrics.heat_score / 100 * 0.3

        # 评论多加分
        if sentiment.total_comments > 50:
            confidence_score += 0.2
        elif sentiment.total_comments > 20:
            confidence_score += 0.1

        # 正面比例高加分
        confidence_score += sentiment.positive_ratio * 0.25

        # 痛点和情绪明确加分
        if sentiment.top_pain_points and sentiment.top_emotions:
            confidence_score += 0.15

        return min(confidence_score, 1.0)


# 便利函数
async def generate_strategy_signals(
    notes_with_comments: list[NoteWithComments],
) -> list[StrategySignals]:
    """
    快速生成策略信号。

    Args:
        notes_with_comments: 笔记列表

    Returns:
        策略信号列表

    示例:
        signals = await generate_strategy_signals(notes)
        for signal in signals:
            print(f"切入点: {signal.top_pain_point}")
    """
    orchestrator = AnalysisOrchestrator()
    return await orchestrator.analyze_for_strategy(notes_with_comments)
