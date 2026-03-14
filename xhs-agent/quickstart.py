"""
XHS Agent 快速开始指南。

演示如何使用完整的采集→分析→存储→生成流程。
"""

import asyncio
import logging

from xhs_agent.types import ProductInfo, ProductCategory, PriceLevel
from xhs_agent.core import run_xhs_agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# 示例：完整的端到端流程
# =============================================================================

async def main():
    """
    运行 XHS Agent 完整流程。

    这是最简单的使用方式——一行代码执行采集→分析→存储→生成的完整工作流。
    """

    # 第一步：定义产品信息
    # =========================================================================
    product = ProductInfo(
        product_name="蓝光眼膜",
        category=ProductCategory.SKINCARE,
        description="深层补水、淡化黑眼圈、改善细纹的蓝光眼膜",

        core_selling_points=[
            "深层补水，8小时持续保湿",
            "淡化黑眼圈，一周见效",
            "改善细纹，提亮眼周肌肤",
        ],
        key_ingredients=["玻尿酸", "蓝光精油", "胶原蛋白"],

        price=79.0,
        price_tier=PriceLevel.MID_RANGE,
        target_audience="25-35岁职场女性，常对着屏幕，有黑眼圈和细纹困扰",

        brand_name="某品牌",
        brand_style="科学护肤，温和有效",

        compliance_level="low",
        forbidden_keywords=[],
        required_disclaimers=[],
    )

    # 第二步：定义搜索关键词和达人
    # =========================================================================
    keywords = ["护肤", "眼膜", "黑眼圈"]
    celebrities = ["user_123", "user_456"]  # 达人 ID（实际从小红书获取）

    # 第三步：运行完整流程
    # =========================================================================
    logger.info(f"\n开始执行 XHS Agent，产品：{product.product_name}\n")

    result = await run_xhs_agent(
        keywords=keywords,
        product=product,
        celebrities=celebrities,
        storage_path="data/",  # 数据存储路径
    )

    # 第四步：查看结果
    # =========================================================================
    if result.get("success"):
        strategies = result.get("strategies", [])

        logger.info("\n\n" + "=" * 80)
        logger.info("📋 生成的种草策略详情")
        logger.info("=" * 80)

        for i, strategy in enumerate(strategies, 1):
            logger.info(f"\n第 {i} 个策略:")
            logger.info(f"  产品：{strategy.product_name}")
            logger.info(f"  达人：{strategy.target_celebrity}")
            logger.info(f"\n  标题选项：")
            for j, title in enumerate(strategy.title_options, 1):
                logger.info(f"    {j}. {title}")

            logger.info(f"\n  内容脚本（前 500 字）：")
            script_preview = strategy.content_script[:500] + "..."
            logger.info(f"    {script_preview}")

            logger.info(f"\n  推荐话题：{', '.join(strategy.hashtags)}")
            logger.info(f"  发布时机：{strategy.posting_time_recommendation}")
            logger.info(f"  CTA 建议：{strategy.cta_recommendations[0]}")
            logger.info(f"  信心度：{strategy.confidence_score:.1%}")
            logger.info(f"  合规状态：{strategy.compliance_status}")

    else:
        logger.error(f"执行失败：{result.get('error')}")


# =============================================================================
# 使用说明
# =============================================================================

USAGE_GUIDE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                  XHS Agent 快速开始指南                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

【核心流程】
┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│  采集 (Phase 1) │ ──→  │ 分析 (Phase 2)  │ ──→  │ 生成 (Phase 3)  │
├────────────────┤      ├────────────────┤      ├────────────────┤
│ 笔记、达人      │      │ 表现、情感      │      │ 策略、脚本      │
│ 评论数据        │      │ 趋势分析        │      │ 标题、话题      │
└────────────────┘      └────────────────┘      └────────────────┘
         │
         ↓
    ┌─────────────┐
    │存储 (Storage)│
    └─────────────┘


【最简单的使用方式】

import asyncio
from xhs_agent.types import ProductInfo, ProductCategory, PriceLevel
from xhs_agent.core import run_xhs_agent

# 定义产品
product = ProductInfo(
    product_name="眼膜",
    category=ProductCategory.SKINCARE,
    description="深层补水眼膜",
    core_selling_points=["补水", "淡化黑眼圈"],
    price=79.0,
    price_tier=PriceLevel.MID_RANGE,
    target_audience="女性用户",
    brand_name="品牌名",
)

# 一行代码执行完整流程
result = await run_xhs_agent(
    keywords=['护肤', '眼膜'],
    product=product,
    celebrities=['user_1', 'user_2']
)

# 查看生成的策略
for strategy in result['strategies']:
    print(strategy.title_options[0])


【详细的分步使用方式】

# 仅采集
from xhs_agent.pipelines.collection import BatchCollector

collector = BatchCollector()
notes = await collector.collect_notes_with_comments(keywords=['护肤'])

# 仅分析
from xhs_agent.pipelines.analysis import AnalysisOrchestrator

orchestrator = AnalysisOrchestrator()
signals = await orchestrator.analyze_for_strategy(notes)

# 仅生成策略
from xhs_agent.strategy import StrategyGenerator
from xhs_agent.types import ProductInfo, CelebData

generator = StrategyGenerator()
strategy = await generator.generate_strategy(product, celebrity, signals[0])


【数据存储】

生成的数据自动保存到：
  data/
  ├── notes/              # 采集的笔记
  ├── celebrities/        # 采集的达人
  ├── analysis/           # 分析结果
  │   ├── performance/    # 表现指标
  │   ├── sentiment/      # 情感报告
  │   └── signals/        # 策略信号
  └── strategies/         # 生成的策略


【关键 API】

产品定义：
  ProductInfo(product_name, category, description, core_selling_points, ...)

采集模块：
  BatchCollector.collect_all(keywords, celebrity_ids)
  BatchCollector.collect_notes_with_comments(keywords)

分析模块：
  AnalysisOrchestrator.analyze_for_strategy(notes_with_comments)

存储模块：
  StorageContext("json", {"path": "data/"})

策略生成：
  StrategyGenerator.generate_strategy(product, celebrity, signals)

完整协调：
  run_xhs_agent(keywords, product, celebrities, storage_path)


【返回结果】

result = {
    "success": True,
    "timestamp": datetime,
    "duration_seconds": 125.3,

    # 四个阶段的结果
    "collection": {
        "notes": [...],
        "notes_with_comments": [...],
        "celebrities": [...],
    },

    "analysis": {
        "signals": [...],
    },

    "storage": {
        "notes_saved": 95,
        "celebrities_saved": 2,
        "signals_saved": 95,
    },

    "strategies": [XhsStrategyPlan, ...],

    # 统计摘要
    "summary": {
        "notes_collected": 95,
        "celebrities_collected": 2,
        "strategies_generated": 2,
        "total_duration": "125.3s",
    }
}


【使用示例】

# 示例 1: 快速开始（推荐）
result = await run_xhs_agent(keywords=['护肤'], product=product)

# 示例 2: 分步执行
collector = BatchCollector()
notes = await collector.collect_notes_with_comments(['护肤'])

analyzer = AnalysisOrchestrator()
signals = await analyzer.analyze_for_strategy(notes)

generator = StrategyGenerator()
for i, note in enumerate(notes[:2]):
    strategy = await generator.generate_strategy(
        product=product,
        celebrity=celebrities[i],
        signals=signals[i]
    )

# 示例 3: 仅采集
notes = await collector.collect_notes_with_comments(['护肤'])

# 示例 4: 仅存储
from xhs_agent.storage import StorageContext

with StorageContext("json", {"path": "data/"}) as storage:
    storage.save_notes(notes)


【下一步】

✅ 现在可以：
   - 采集小红书数据（笔记、达人、评论）
   - 分析数据（表现、情感、趋势）
   - 生成种草策略（标题、脚本、话题）
   - 保存所有结果

⏳ 待实现：
   - SQLite 数据库支持
   - Web API 接口
   - CLI 命令行工具
   - 数据可视化仪表板
"""

if __name__ == "__main__":
    print(USAGE_GUIDE)
    print("\n运行完整流程...")
    print("="*80 + "\n")

    # 取消注释下面的代码来运行完整流程
    # asyncio.run(main())
