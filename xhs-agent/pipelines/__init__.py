"""
数据处理管道包。

包含三个核心管道：
1. collection - 数据采集
2. analysis - 数据分析
3. strategy - 策略生成

以及存储、集成等支持层。
"""

from . import collection
from . import analysis

__all__ = [
    "collection",
    "analysis",
]
