"""
XHS Agent 核心协调器。

将采集、分析、存储、策略生成四个步骤整合成完整的端到端流程。

这是整个 Agent 的"大脑"，协调所有子模块的工作。
"""

from __future__ import annotations

import logging
import asyncio
from typing import Optional, List
from datetime import datetime

from xhs_agent.types import (
    ProductInfo,
    CollectionConfig,
)
from xhs_agent.pipelines.collection import BatchCollector
from xhs_agent.pipelines.analysis import AnalysisOrchestrator
from xhs_agent.storage import StorageContext
from xhs_agent.strategy import StrategyGenerator

logger = logging.getLogger(__name__)


class XHSAgentOrchestrator:
    """
    XHS Agent 核心协调器。

    执行完整的工作流：
    1. 采集 (Collection) — 从小红书采集笔记、达人、评论
    2. 分析 (Analysis) — 分析表现、情感、趋势
    3. 存储 (Storage) — 保存采集和分析结果
    4. 生成 (Generation) — 生成最优种草策略

    使用方式:
        orchestrator = XHSAgentOrchestrator()
        result = await orchestrator.execute_full_pipeline(
            keywords=['护肤', '眼膜'],
            product=product_info,
            celebrities=['user_1', 'user_2']
        )

        # 查看生成的策略
        for strategy in result['strategies']:
            print(f"标题: {strategy.title_options[0]}")
    """

    def __init__(
        self,
        collection_config: Optional[CollectionConfig] = None,
        storage_path: str = "data/",
    ):
        """
        初始化协调器。

        Args:
            collection_config: 采集配置
            storage_path: 存储路径
        """
        self.collection_config = collection_config or CollectionConfig()
        self.storage_path = storage_path

        logger.info("XHS Agent Orchestrator initialized")

    async def execute_full_pipeline(
        self,
        keywords: List[str],
        product: ProductInfo,
        celebrities: Optional[List[str]] = None,
    ) -> dict:
        """
        执行完整的端到端流程。

        Args:
            keywords: 搜索关键词列表
            product: 产品信息
            celebrities: 达人 ID 列表（可选）

        Returns:
            完整的执行结果字典
        """
        logger.info("=" * 80)
        logger.info("XHS Agent - Full Pipeline Execution Started")
        logger.info("=" * 80)

        start_time = datetime.now()

        try:
            # ===== Phase 1: 采集 =====
            logger.info("\n[Phase 1] COLLECTION - 采集小红书数据")
            logger.info("-" * 80)

            collection_result = await self._phase_collection(
                keywords=keywords,
                celebrities=celebrities,
            )

            # ===== Phase 2: 分析 =====
            logger.info("\n[Phase 2] ANALYSIS - 分析采集数据")
            logger.info("-" * 80)

            analysis_result = await self._phase_analysis(
                notes_with_comments=collection_result["notes_with_comments"],
            )

            # ===== Phase 3: 存储 =====
            logger.info("\n[Phase 3] STORAGE - 保存采集和分析结果")
            logger.info("-" * 80)

            storage_result = await self._phase_storage(
                collection_result=collection_result,
                analysis_result=analysis_result,
            )

            # ===== Phase 4: 策略生成 =====
            logger.info("\n[Phase 4] STRATEGY GENERATION - 生成种草策略")
            logger.info("-" * 80)

            strategy_result = await self._phase_strategy_generation(
                product=product,
                collection_result=collection_result,
                analysis_result=analysis_result,
                storage_path=self.storage_path,
            )

            # ===== 汇总结果 =====
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            final_result = {
                "success": True,
                "timestamp": datetime.now(),
                "duration_seconds": duration,

                "collection": collection_result,
                "analysis": analysis_result,
                "storage": storage_result,
                "strategies": strategy_result["strategies"],

                "summary": {
                    "notes_collected": len(collection_result.get("notes", [])),
                    "notes_with_comments": len(
                        collection_result.get("notes_with_comments", [])
                    ),
                    "celebrities_collected": len(
                        collection_result.get("celebrities", [])
                    ),
                    "strategies_generated": len(strategy_result["strategies"]),
                    "total_duration": f"{duration:.1f}s",
                },
            }

            logger.info("\n" + "=" * 80)
            logger.info("✅ XHS Agent - Full Pipeline Execution Completed!")
            logger.info("=" * 80)
            logger.info(
                f"总用时: {duration:.1f}s | "
                f"笔记: {final_result['summary']['notes_collected']} | "
                f"达人: {final_result['summary']['celebrities_collected']} | "
                f"策略: {final_result['summary']['strategies_generated']}"
            )

            return final_result

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def _phase_collection(
        self,
        keywords: List[str],
        celebrities: Optional[List[str]] = None,
    ) -> dict:
        """Phase 1: 采集"""
        logger.info(f"搜索关键词: {', '.join(keywords)}")

        collector = BatchCollector(self.collection_config)

        try:
            result = await collector.collect_all(
                keywords=keywords,
                celebrity_ids=celebrities,
            )

            logger.info(
                f"✅ 采集完成: {result['summary']['total_notes']} 笔记, "
                f"{result['summary']['total_celebrities']} 达人"
            )

            return result

        finally:
            collector.print_summary()

    async def _phase_analysis(self, notes_with_comments: List) -> dict:
        """Phase 2: 分析"""
        logger.info(f"分析 {len(notes_with_comments)} 条笔记...")

        orchestrator = AnalysisOrchestrator()

        try:
            signals = await orchestrator.analyze_for_strategy(
                notes_with_comments=notes_with_comments
            )

            logger.info(f"✅ 分析完成: 生成 {len(signals)} 个策略信号")

            return {
                "signals": signals,
                "total_notes_analyzed": len(notes_with_comments),
            }

        except Exception as e:
            logger.error(f"Analysis phase failed: {e}")
            raise

    async def _phase_storage(
        self,
        collection_result: dict,
        analysis_result: dict,
    ) -> dict:
        """Phase 3: 存储"""
        from xhs_agent.storage import StorageContext

        logger.info(f"保存数据到 {self.storage_path}...")

        try:
            with StorageContext("json", {"path": self.storage_path}) as storage:
                # 保存采集数据
                notes_saved = storage.save_notes(
                    [item.note for item in collection_result.get("notes_with_comments", [])]
                )

                celebs_saved = storage.save_celebrities(
                    collection_result.get("celebrities", [])
                )

                # 保存分析结果
                signals_saved = sum(
                    1 for signal in analysis_result.get("signals", [])
                    if storage.save_strategy_signals(signal)
                )

                logger.info(
                    f"✅ 存储完成: {notes_saved} 笔记, "
                    f"{celebs_saved} 达人, {signals_saved} 信号"
                )

                stats = storage.get_stats()

                return {
                    "notes_saved": notes_saved,
                    "celebrities_saved": celebs_saved,
                    "signals_saved": signals_saved,
                    "storage_path": self.storage_path,
                    "storage_stats": stats,
                }

        except Exception as e:
            logger.error(f"Storage phase failed: {e}")
            raise

    async def _phase_strategy_generation(
        self,
        product: ProductInfo,
        collection_result: dict,
        analysis_result: dict,
        storage_path: str,
    ) -> dict:
        """Phase 4: 策略生成"""
        logger.info(f"为产品 '{product.product_name}' 生成策略...")

        generator = StrategyGenerator()
        strategies = []

        try:
            # 为每个采集到的达人生成策略
            celebs = collection_result.get("celebrities", [])

            if not celebs:
                logger.warning("No celebrities found, skipping strategy generation")
                return {"strategies": []}

            # 为每个达人和对应的信号生成策略
            signals_list = analysis_result.get("signals", [])

            for i, celeb in enumerate(celebs[:5]):  # 限制最多生成 5 个
                try:
                    # 获取对应的信号（如果有）
                    signal = signals_list[i] if i < len(signals_list) else None

                    strategy = await generator.generate_strategy(
                        product=product,
                        celebrity=celeb,
                        signals=signal,
                        reference_note_id=signal.note_id if signal else None,
                    )

                    strategies.append(strategy)

                    logger.info(
                        f"  ✅ 为达人 '{celeb.name}' 生成了策略"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to generate strategy for {celeb.name}: {e}"
                    )
                    continue

            logger.info(f"✅ 策略生成完成: {len(strategies)} 条策略")

            # 保存策略到存储
            await self._save_strategies(strategies, storage_path)

            return {"strategies": strategies}

        except Exception as e:
            logger.error(f"Strategy generation phase failed: {e}")
            raise

    async def _save_strategies(
        self,
        strategies: list,
        storage_path: str,
    ) -> int:
        """保存生成的策略"""
        from xhs_agent.storage import StorageContext

        try:
            with StorageContext("json", {"path": storage_path}) as storage:
                saved_count = 0

                for strategy in strategies:
                    if storage.save_strategy_plan(strategy):
                        saved_count += 1

                logger.info(f"保存了 {saved_count} 条策略")
                return saved_count

        except Exception as e:
            logger.error(f"Failed to save strategies: {e}")
            return 0

    def print_final_report(self, result: dict):
        """打印最终报告"""
        if not result.get("success"):
            print(f"\n❌ 执行失败: {result.get('error')}")
            return

        print("\n" + "=" * 80)
        print("📊 XHS Agent 执行报告")
        print("=" * 80)

        summary = result.get("summary", {})
        print(f"\n采集统计:")
        print(f"  📝 笔记: {summary.get('notes_collected', 0)}")
        print(f"  👥 达人: {summary.get('celebrities_collected', 0)}")
        print(f"  📊 策略: {summary.get('strategies_generated', 0)}")
        print(f"  ⏱️  耗时: {summary.get('total_duration', '?')}")

        strategies = result.get("strategies", [])
        if strategies:
            print(f"\n生成的种草策略:")
            for i, strategy in enumerate(strategies[:3], 1):
                print(f"\n  {i}. 产品: {strategy.product_name}")
                print(f"     达人: {strategy.target_celebrity}")
                print(f"     标题1: {strategy.title_options[0][:60]}...")
                print(f"     信心度: {strategy.confidence_score:.1%}")

        print("\n" + "=" * 80)


# 便利函数
async def run_xhs_agent(
    keywords: List[str],
    product: ProductInfo,
    celebrities: Optional[List[str]] = None,
    storage_path: str = "data/",
) -> dict:
    """
    快速运行 XHS Agent 完整流程。

    Args:
        keywords: 搜索关键词
        product: 产品信息
        celebrities: 达人 ID 列表
        storage_path: 数据存储路径

    Returns:
        完整的执行结果

    示例:
        result = await run_xhs_agent(
            keywords=['护肤', '眼膜'],
            product=product_info,
            celebrities=['user_1', 'user_2']
        )
    """
    orchestrator = XHSAgentOrchestrator(storage_path=storage_path)
    result = await orchestrator.execute_full_pipeline(
        keywords=keywords,
        product=product,
        celebrities=celebrities,
    )

    orchestrator.print_final_report(result)

    return result
