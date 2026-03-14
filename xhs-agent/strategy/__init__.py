"""
策略生成层 (Strategy Layer)。

负责生成最优的种草策略：
- 调用 ohmyxhs SKILL
- 基于分析结果优化策略
- 输出完整的内容方案
"""

from .generator import StrategyGenerator, generate_strategy_plan

__all__ = [
    "StrategyGenerator",
    "generate_strategy_plan",
]
