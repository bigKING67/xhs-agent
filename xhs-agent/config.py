"""
XHS Agent 全局配置。

管理采集、分析、存储、策略生成等各个模块的配置。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from xhs_agent.types import CollectionConfig

# ============================================================================
# 路径配置
# ============================================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据存储目录
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 采集数据目录
COLLECTION_DATA_DIR = DATA_DIR / "collection"
COLLECTION_DATA_DIR.mkdir(exist_ok=True)

# 分析结果目录
ANALYSIS_DATA_DIR = DATA_DIR / "analysis"
ANALYSIS_DATA_DIR.mkdir(exist_ok=True)

# 生成的策略目录
STRATEGY_DATA_DIR = DATA_DIR / "strategies"
STRATEGY_DATA_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ============================================================================
# 采集配置
# ============================================================================

DEFAULT_COLLECTION_CONFIG = CollectionConfig(
    # 并发设置
    concurrent_requests=5,
    request_timeout=30,
    retry_attempts=3,
    rate_limit_delay=1.0,

    # 采集限制
    max_notes_per_search=100,
    max_comments_per_note=200,

    # 存储设置
    storage_backend="json",
    storage_path=str(COLLECTION_DATA_DIR),
)

# ============================================================================
# 日志配置
# ============================================================================

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        },
        "detailed": {
            "format": (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(filename)s:%(lineno)d] - %(message)s"
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOG_DIR / "xhs_agent.log"),
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}

# ============================================================================
# 分析配置
# ============================================================================

# 热度评分权重
HEAT_SCORE_WEIGHTS = {
    "likes": 0.4,
    "comments": 0.35,
    "shares": 0.25,
}

# 传播力评分权重
VIRALITY_SCORE_WEIGHTS = {
    "shares": 0.5,
    "reposts": 0.3,
    "comments": 0.2,
}

# 转化潜力评分权重
CONVERSION_POTENTIAL_WEIGHTS = {
    "comments_with_purchase_signals": 0.4,
    "comments_with_positive_sentiment": 0.3,
    "engagement_rate": 0.3,
}

# ============================================================================
# 情感分析配置
# ============================================================================

# 正面词汇列表
POSITIVE_KEYWORDS = [
    "好用", "效果好", "真的有效", "推荐", "已回购",
    "爱上", "必买", "安利", "绝绝子", "太棒了",
    "改善", "满意", "值得", "正品", "品质好",
]

# 负面词汇列表
NEGATIVE_KEYWORDS = [
    "不好用", "没效果", "浪费钱", "坑", "差评",
    "不推荐", "退货", "假货", "骗人", "垃圾",
    "烂", "太差", "失望", "后悔", "不值得",
]

# 购买信号词汇
PURCHASE_SIGNAL_KEYWORDS = [
    "回购", "已下单", "已拍", "囤货", "收藏",
    "分享给朋友", "推荐给", "安利", "转发",
    "预购", "等快递", "已到货",
]

# ============================================================================
# 策略生成配置
# ============================================================================

# ohmyxhs SKILL 路径
OHMYXHS_SKILL_PATH = PROJECT_ROOT / "ohmyxhs" / "SKILL.md"

# 默认的生成模式
DEFAULT_GENERATION_MODE = "complete"  # "complete", "concise", "quick"

# ============================================================================
# 数据库配置
# ============================================================================

# SQLite 数据库路径（如果使用）
SQLITE_DB_PATH = DATA_DIR / "xhs_agent.db"

# ============================================================================
# API 配置
# ============================================================================

# xiaohongshu-cli 相关
XHS_CLI_PATH = PROJECT_ROOT.parent / "xiaohongshu-cli"
XHS_API_TIMEOUT = 30
XHS_REQUEST_DELAY = 1.0

# ============================================================================
# 辅助函数
# ============================================================================


def get_collection_config() -> CollectionConfig:
    """获取采集配置"""
    return DEFAULT_COLLECTION_CONFIG


def ensure_data_directories():
    """确保所有数据目录都存在"""
    for directory in [
        DATA_DIR,
        COLLECTION_DATA_DIR,
        ANALYSIS_DATA_DIR,
        STRATEGY_DATA_DIR,
        LOG_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
