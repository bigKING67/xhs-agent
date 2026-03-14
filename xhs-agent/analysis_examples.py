"""
分析管道使用示例。

演示如何使用各个分析器分析采集到的数据。
"""

import asyncio
import logging
from typing import List

from xhs_agent.types import NoteWithComments
from xhs_agent.pipelines.analysis import (
    NotePerformanceAnalyzer,
    CommentSentimentAnalyzer,
    TrendAnalyzer,
    AnalysisOrchestrator,
    analyze_note_performance,
    analyze_comment_sentiment,
    analyze_market_trends,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# 示例 1: 笔记表现分析（单个）
# =============================================================================

def example_1_analyze_single_note_performance(note_with_comments: NoteWithComments):
    """
    分析单个笔记的表现。

    包括互动率、热度、传播力、转化潜力等指标。
    """
    logger.info("Example 1: Analyzing single note performance")

    analyzer = NotePerformanceAnalyzer()
    metrics = analyzer.analyze(note_with_comments)

    print(f"笔记: {note_with_comments.note.title}")
    print(f"  热度评分: {metrics.heat_score:.1f}/100")
    print(f"  传播力评分: {metrics.virality_score:.1f}/100")
    print(f"  转化潜力: {metrics.conversion_potential:.1f}/100")
    print(f"  互动率: {metrics.engagement_rate:.2%}")
    print(f"  发布至今: {metrics.days_since_publish} 天")


# =============================================================================
# 示例 2: 笔记表现批量分析
# =============================================================================

def example_2_analyze_batch_performance(notes_with_comments: List[NoteWithComments]):
    """
    批量分析多个笔记的表现。
    """
    logger.info("Example 2: Analyzing batch note performance")

    analyzer = NotePerformanceAnalyzer()
    metrics_list = analyzer.batch_analyze(notes_with_comments)

    print(f"分析了 {len(metrics_list)} 条笔记\n")

    # 按热度排序
    sorted_metrics = sorted(
        metrics_list,
        key=lambda m: m.heat_score,
        reverse=True
    )

    print("按热度排序的笔记:")
    for i, metrics in enumerate(sorted_metrics[:5], 1):
        print(
            f"{i}. 热度: {metrics.heat_score:.1f}, "
            f"互动: {metrics.engagement_count}"
        )


# =============================================================================
# 示例 3: 评论情感分析（单个）
# =============================================================================

def example_3_analyze_single_sentiment(note_with_comments: NoteWithComments):
    """
    分析单个笔记的评论情感。

    包括情感分布、痛点、关键情绪、购买驱动力等。
    """
    logger.info("Example 3: Analyzing comment sentiment")

    analyzer = CommentSentimentAnalyzer()
    report = analyzer.analyze(note_with_comments)

    print(f"笔记: {note_with_comments.note.title}")
    print(f"  总评论数: {report.total_comments}")
    print(f"  正面比例: {report.positive_ratio:.1%}")
    print(f"  负面比例: {report.negative_ratio:.1%}")
    print(f"  中立比例: {report.neutral_ratio:.1%}")

    if report.top_pain_points:
        print(f"  核心痛点: {', '.join(report.top_pain_points[:3])}")

    if report.top_emotions:
        print(f"  关键情绪: {', '.join(report.top_emotions)}")

    if report.purchase_drivers:
        print(f"  购买驱动: {', '.join(report.purchase_drivers[:3])}")

    if report.key_topics:
        print(f"  热点话题:")
        for topic, count in list(report.key_topics.items())[:5]:
            print(f"    - {topic}: {count}次")


# =============================================================================
# 示例 4: 评论情感批量分析
# =============================================================================

def example_4_analyze_batch_sentiment(notes_with_comments: List[NoteWithComments]):
    """
    批量分析多个笔记的评论情感。
    """
    logger.info("Example 4: Analyzing batch sentiment")

    analyzer = CommentSentimentAnalyzer()
    reports = analyzer.batch_analyze(notes_with_comments)

    print(f"分析了 {len(reports)} 条笔记的评论\n")

    # 计算平均情感
    avg_positive = sum(r.positive_ratio for r in reports) / len(reports)
    avg_negative = sum(r.negative_ratio for r in reports) / len(reports)

    print(f"平均正面比例: {avg_positive:.1%}")
    print(f"平均负面比例: {avg_negative:.1%}")

    # 聚合所有的痛点
    all_pain_points = []
    for report in reports:
        all_pain_points.extend(report.top_pain_points[:2])

    from collections import Counter
    pain_point_counts = Counter(all_pain_points)
    print(f"\n聚合的核心痛点:")
    for pain, count in pain_point_counts.most_common(5):
        print(f"  - {pain}: {count}次")


# =============================================================================
# 示例 5: 市场趋势分析
# =============================================================================

def example_5_analyze_trends(notes_with_comments: List[NoteWithComments]):
    """
    分析市场趋势。

    包括热词、内容风格、竞品学习点等。
    """
    logger.info("Example 5: Analyzing market trends")

    analyzer = TrendAnalyzer()
    trends = analyzer.analyze_trend(notes_with_comments)

    print(f"分析了 {len(notes_with_comments)} 条笔记的市场趋势\n")

    # 热词
    if trends['hot_keywords']:
        print("热词 Top 10:")
        for i, (keyword, count) in enumerate(trends['hot_keywords'][:10], 1):
            print(f"  {i}. {keyword}: {count}次")

    # 内容风格
    print(f"\n内容风格分布:")
    for style, count in trends['content_styles'].items():
        print(f"  {style}: {count}条")

    # 竞品学习点
    if trends['competitor_insights']:
        insights = trends['competitor_insights']
        if insights.get('successful_angles'):
            print(f"\n成功的内容角度: {', '.join(insights['successful_angles'])}")

    # 聚合痛点
    if trends.get('common_pain_points'):
        print(f"\n聚合的用户痛点: {', '.join(trends['common_pain_points'][:5])}")


# =============================================================================
# 示例 6: 端到端分析（采集→分析→信号）
# =============================================================================

async def example_6_end_to_end_analysis(notes_with_comments: List[NoteWithComments]):
    """
    执行完整的分析流程。

    从采集的数据生成策略信号。
    """
    logger.info("Example 6: End-to-end analysis pipeline")

    orchestrator = AnalysisOrchestrator()
    signals = await orchestrator.analyze_for_strategy(notes_with_comments)

    print(f"为 {len(signals)} 条笔记生成了策略信号\n")

    for i, signal in enumerate(signals[:3], 1):
        print(f"{i}. 笔记 {signal.note_id}")
        print(f"   核心切入点: {signal.top_pain_point}")
        print(f"   有效框架: {', '.join(signal.top_performing_frames)}")
        print(f"   关键情绪: {', '.join(signal.user_emotions)}")
        print(f"   推荐角度: {signal.content_angle_recommendation}")
        print(f"   信心度: {signal.signal_confidence:.1%}\n")


# =============================================================================
# 示例 7: 快速便利函数
# =============================================================================

def example_7_quick_functions(note_with_comments: NoteWithComments):
    """
    使用快速便利函数进行分析。
    """
    logger.info("Example 7: Using quick convenience functions")

    # 一行代码分析表现
    metrics = analyze_note_performance(note_with_comments)
    print(f"热度评分: {metrics.heat_score:.1f}")

    # 一行代码分析情感
    sentiment = analyze_comment_sentiment(note_with_comments)
    print(f"正面比例: {sentiment.positive_ratio:.1%}")


# =============================================================================
# 示例 8: 自定义分析权重
# =============================================================================

def example_8_custom_weights(note_with_comments: NoteWithComments):
    """
    使用自定义权重进行分析。

    可以调整热度、传播力等指标的计算方式。
    """
    logger.info("Example 8: Custom analysis weights")

    # 自定义热度权重（强调评论）
    custom_weights = {
        "likes": 0.3,      # 赞数权重降低
        "comments": 0.5,   # 评论数权重提高
        "shares": 0.2,
    }

    analyzer = NotePerformanceAnalyzer(heat_weights=custom_weights)
    metrics = analyzer.analyze(note_with_comments)

    print(f"自定义权重下的热度: {metrics.heat_score:.1f}")
    print("（强调评论互动）")


# =============================================================================
# 主函数
# =============================================================================

async def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("XHS Agent 分析管道示例")
    print("=" * 80 + "\n")

    print("注意: 这些示例需要实际的采集数据")
    print("建议先运行 examples.py 中的采集示例来生成数据\n")

    # 模拟数据（实际应该从采集管道获取）
    # notes_with_comments = await collect_notes_with_comments(['护肤'])

    print("✅ 分析管道框架已就绪")
    print("\n可用的分析器:")
    print("1. NotePerformanceAnalyzer - 笔记表现分析（互动、热度、传播力）")
    print("2. CommentSentimentAnalyzer - 评论情感分析（痛点、情绪、购买信号）")
    print("3. TrendAnalyzer - 市场趋势分析（热词、风格、竞品）")
    print("4. AnalysisOrchestrator - 分析协调（整合生成策略信号）")

    print("\n快速使用:")
    print("""
    from xhs_agent.pipelines.analysis import (
        analyze_note_performance,
        analyze_comment_sentiment,
        analyze_market_trends,
        generate_strategy_signals
    )

    # 分析单个笔记
    metrics = analyze_note_performance(note_with_comments)
    sentiment = analyze_comment_sentiment(note_with_comments)

    # 分析市场趋势
    trends = analyze_market_trends(notes)

    # 生成策略信号
    signals = await generate_strategy_signals(notes)
    """)


if __name__ == "__main__":
    asyncio.run(main())
