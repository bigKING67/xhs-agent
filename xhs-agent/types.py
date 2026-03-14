"""
XHS Agent 核心数据类型定义。

此模块定义了整个采集→分析→生成管道中的所有数据模型。
使用 Pydantic 确保类型安全和序列化/反序列化。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# 枚举类型
# =============================================================================

class ContentStyle(str, Enum):
    """达人内容风格"""
    DAILY_LIFE = "daily_life"  # 日常分享
    TUTORIAL = "tutorial"  # 教程干货
    STORY = "story"  # 故事叙述
    ARTISTIC = "artistic"  # 文艺分享
    EXPERT = "expert"  # 专家/学者
    HUMOR = "humor"  # 幽默搞笑


class SentimentType(str, Enum):
    """情感极性"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class PriceLevel(str, Enum):
    """价格档位"""
    BUDGET = "budget"  # 平价 (<50)
    MID_RANGE = "mid_range"  # 中档 (50-200)
    PREMIUM = "premium"  # 高档 (>200)


class ProductCategory(str, Enum):
    """产品品类"""
    BEAUTY = "beauty"  # 美妆
    SKINCARE = "skincare"  # 护肤
    FOOD = "food"  # 食品/饮品
    FASHION = "fashion"  # 服饰
    HOME = "home"  # 家居
    ELECTRONICS = "electronics"  # 3C/电子
    HEALTH = "health"  # 健康保健
    MOTHER_BABY = "mother_baby"  # 母婴
    MEDICAL_BEAUTY = "medical_beauty"  # 医美（高风险）
    FINANCE = "finance"  # 金融（高风险）
    REAL_ESTATE = "real_estate"  # 房产（高风险）
    PET = "pet"  # 宠物
    SECONDHAND = "secondhand"  # 二手交易
    EDUCATION = "education"  # 教育/课程
    FITNESS = "fitness"  # 健身/运动


class EmotionType(str, Enum):
    """情感触发类型"""
    GAIN = "gain"  # 获得感
    SAFETY = "safety"  # 安心感
    CONFIDENCE = "confidence"  # 自信感
    RESONANCE = "resonance"  # 共鸣感
    CONTROL = "control"  # 掌控感


class NoteType(str, Enum):
    """笔记类型"""
    IMAGE = "image"  # 图文
    VIDEO = "video"  # 视频
    CAROUSEL = "carousel"  # 轮播


# =============================================================================
# 基础实体数据模型
# =============================================================================

class CelebData(BaseModel):
    """达人信息"""

    model_config = ConfigDict(str_strip_whitespace=True)

    celeb_id: str = Field(..., description="小红书用户 ID")
    name: str = Field(..., description="达人昵称")
    avatar_url: Optional[str] = Field(None, description="头像 URL")

    # 粉丝和互动数据
    followers: int = Field(default=0, description="粉丝数")
    interaction_rate: float = Field(
        default=0.0, description="平均互动率 (赞+评+收/曝光)"
    )
    avg_likes_per_note: float = Field(default=0.0, description="平均赞数")
    avg_comments_per_note: float = Field(default=0.0, description="平均评论数")
    avg_shares_per_note: float = Field(default=0.0, description="平均分享数")

    # 内容特征
    content_styles: List[ContentStyle] = Field(
        default_factory=list, description="主要内容风格"
    )
    avg_notes_per_week: int = Field(default=0, description="周均发布数")
    target_audience: str = Field(default="", description="目标受众描述")
    bio: str = Field(default="", description="达人简介")

    # 价格和商业化
    price_tier: PriceLevel = Field(
        default=PriceLevel.MID_RANGE, description="价格档位"
    )
    collaboration_history: List[str] = Field(
        default_factory=list, description="合作过的品牌列表"
    )

    # 元数据
    data_collected_at: datetime = Field(
        default_factory=datetime.now, description="数据采集时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "celeb_id": "user_123",
                "name": "小红书达人",
                "followers": 100000,
                "interaction_rate": 0.05,
                "content_styles": ["daily_life", "tutorial"],
            }
        }


class NoteData(BaseModel):
    """笔记基础数据"""

    model_config = ConfigDict(str_strip_whitespace=True)

    note_id: str = Field(..., description="笔记 ID")
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记正文")
    author_id: str = Field(..., description="发布者 ID")
    author_name: str = Field(..., description="发布者昵称")

    # 内容特征
    note_type: NoteType = Field(default=NoteType.IMAGE, description="笔记类型")
    images: List[str] = Field(
        default_factory=list, description="图片 URL 列表"
    )
    topics: List[str] = Field(default_factory=list, description="话题标签")
    mentioned_products: List[str] = Field(
        default_factory=list, description="提及的产品名称"
    )

    # 互动数据
    likes: int = Field(default=0, description="赞数")
    comments_count: int = Field(default=0, description="评论数")
    shares: int = Field(default=0, description="分享数")
    collects: int = Field(default=0, description="收藏数")
    reposts: int = Field(default=0, description="转发数")

    # 时间信息
    published_at: datetime = Field(..., description="发布时间")
    fetched_at: datetime = Field(
        default_factory=datetime.now, description="采集时间"
    )

    # 关联数据
    source_search_keyword: Optional[str] = Field(
        None, description="通过搜索什么关键词找到的"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "note_id": "note_456",
                "title": "护肤新手必看",
                "content": "今天分享一下我的护肤心得...",
                "author_id": "user_123",
                "author_name": "小红书达人",
                "likes": 1000,
                "comments_count": 100,
                "published_at": "2026-03-14T10:00:00",
            }
        }


class Comment(BaseModel):
    """评论数据"""

    model_config = ConfigDict(str_strip_whitespace=True)

    comment_id: str = Field(..., description="评论 ID")
    note_id: str = Field(..., description="所属笔记 ID")
    author_id: str = Field(..., description="评论者 ID")
    author_name: str = Field(..., description="评论者昵称")
    content: str = Field(..., description="评论内容")

    # 互动数据
    likes: int = Field(default=0, description="点赞数")
    replies_count: int = Field(default=0, description="回复数")

    # 回复关系
    is_reply: bool = Field(default=False, description="是否是回复")
    parent_comment_id: Optional[str] = Field(None, description="父评论 ID")

    # 时间信息
    published_at: datetime = Field(..., description="发布时间")
    fetched_at: datetime = Field(
        default_factory=datetime.now, description="采集时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "comment_id": "cmt_789",
                "note_id": "note_456",
                "author_id": "user_999",
                "author_name": "用户评论",
                "content": "真的好用！已经回购三次了",
                "likes": 50,
                "published_at": "2026-03-14T12:00:00",
            }
        }


# =============================================================================
# 富化数据模型（包含关联数据）
# =============================================================================


class NoteWithComments(BaseModel):
    """包含评论的完整笔记数据"""

    note: NoteData = Field(..., description="笔记基础数据")
    comments: List[Comment] = Field(default_factory=list, description="评论列表")
    author_data: Optional[CelebData] = Field(None, description="发布者详细信息")

    def get_top_comments(self, n: int = 10) -> List[Comment]:
        """获取赞数最多的 N 条评论"""
        sorted_comments = sorted(
            self.comments, key=lambda c: c.likes, reverse=True
        )
        return sorted_comments[:n]

    def get_reply_threads(self) -> Dict[str, List[Comment]]:
        """获取回复线程（顶级评论 → 回复）"""
        threads = {}
        for comment in self.comments:
            if not comment.is_reply:
                threads[comment.comment_id] = [
                    c for c in self.comments
                    if c.parent_comment_id == comment.comment_id
                ]
        return threads


# =============================================================================
# 分析结果数据模型
# =============================================================================


class PerformanceMetrics(BaseModel):
    """笔记表现指标"""

    note_id: str = Field(..., description="笔记 ID")

    # 基础指标
    engagement_rate: float = Field(
        default=0.0,
        description="互动率 = (赞+评+收) / 预估曝光"
    )
    engagement_count: int = Field(
        default=0,
        description="总互动数 (赞+评+收)"
    )

    # 评分指标
    heat_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="热度评分 (0-100)"
    )
    virality_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="传播力评分 (0-100)"
    )
    conversion_potential: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="转化潜力评分 (0-100)"
    )

    # 时间相关
    peak_engagement_hour: Optional[int] = Field(
        None, description="最高互动小时 (0-23)"
    )
    days_since_publish: int = Field(
        default=0, description="发布至今天数"
    )

    # 计算细节
    calculation_timestamp: datetime = Field(
        default_factory=datetime.now, description="计算时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "note_id": "note_456",
                "engagement_rate": 0.08,
                "heat_score": 75.5,
                "virality_score": 65.0,
                "conversion_potential": 72.0,
            }
        }


class SentimentReport(BaseModel):
    """评论情感分析报告"""

    note_id: str = Field(..., description="笔记 ID")
    total_comments: int = Field(default=0, description="总评论数")

    # 情感分布
    positive_ratio: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="正面评论比例"
    )
    neutral_ratio: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="中立评论比例"
    )
    negative_ratio: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="负面评论比例"
    )

    # 核心洞察
    top_pain_points: List[str] = Field(
        default_factory=list,
        description="用户最关心的痛点"
    )
    top_emotions: List[str] = Field(
        default_factory=list,
        description="最能打动用户的情绪"
    )
    purchase_drivers: List[str] = Field(
        default_factory=list,
        description="购买驱动力排序"
    )

    # 话题提取
    key_topics: Dict[str, int] = Field(
        default_factory=dict,
        description="热点话题及提及次数"
    )

    # 质量指标
    overall_sentiment_score: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="总体情感评分 (0=全负, 1=全正)"
    )

    analysis_timestamp: datetime = Field(
        default_factory=datetime.now, description="分析时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "note_id": "note_456",
                "total_comments": 100,
                "positive_ratio": 0.75,
                "neutral_ratio": 0.15,
                "negative_ratio": 0.10,
                "top_pain_points": ["黑眼圈", "细纹"],
                "top_emotions": ["获得感", "安心感"],
                "purchase_drivers": ["真实有效", "快速见效"],
                "key_topics": {"补水": 45, "保湿": 38, "提亮": 32},
            }
        }


class StrategySignals(BaseModel):
    """策略信号（分析阶段输出，用于策略生成）"""

    note_id: str = Field(..., description="参考笔记 ID")

    # 核心信号
    top_pain_point: str = Field(
        default="",
        description="最有效的切入点"
    )
    top_performing_frames: List[str] = Field(
        default_factory=list,
        description="最有效的叙述框架"
    )
    user_emotions: List[str] = Field(
        default_factory=list,
        description="最能打动用户的情绪"
    )

    # 竞品和趋势
    competitor_insights: str = Field(
        default="",
        description="竞品学习点"
    )
    content_angle_recommendation: str = Field(
        default="",
        description="推荐的内容角度"
    )

    # 质量指标
    signal_confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="信号置信度"
    )

    # 源数据引用
    source_metrics: Optional[PerformanceMetrics] = Field(
        None, description="来自哪个表现指标"
    )
    source_sentiment: Optional[SentimentReport] = Field(
        None, description="来自哪个情感分析"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "note_id": "note_456",
                "top_pain_point": "黑眼圈困扰",
                "top_performing_frames": [
                    "问题-分析-解决方案",
                    "对比式转变",
                ],
                "user_emotions": ["获得感", "安心感"],
                "content_angle_recommendation": "黑眼圈自救指南",
                "signal_confidence": 0.85,
            }
        }


# =============================================================================
# 产品信息模型
# =============================================================================


class ProductInfo(BaseModel):
    """产品信息"""

    product_name: str = Field(..., description="产品名称")
    category: ProductCategory = Field(..., description="产品品类")
    description: str = Field(..., description="产品描述")

    # 卖点
    core_selling_points: List[str] = Field(
        ..., description="核心卖点 (2-3个)"
    )
    key_ingredients: List[str] = Field(
        default_factory=list, description="关键成分"
    )

    # 市场信息
    price: float = Field(..., description="产品价格")
    price_tier: PriceLevel = Field(..., description="价格档位")
    target_audience: str = Field(..., description="目标用户描述")

    # 品牌信息
    brand_name: str = Field(..., description="品牌名")
    brand_style: str = Field(default="", description="品牌风格")

    # 风险等级（用于内容审核）
    compliance_level: str = Field(
        default="low",
        description="合规风险等级 (low/medium/high/super_high)"
    )

    # 其他约束
    forbidden_keywords: List[str] = Field(
        default_factory=list, description="禁用词汇列表"
    )
    required_disclaimers: List[str] = Field(
        default_factory=list, description="需要的免责声明"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "某品牌蓝光眼膜",
                "category": "skincare",
                "core_selling_points": ["深层补水", "淡化细纹", "改善黑眼圈"],
                "price": 79.0,
                "price_tier": "mid_range",
                "target_audience": "25-35岁职场女性",
                "brand_name": "某品牌",
                "compliance_level": "low",
            }
        }


# =============================================================================
# 最终输出模型
# =============================================================================


class XhsStrategyPlan(BaseModel):
    """完整的种草策略"""

    # 基本信息
    product_name: str = Field(..., description="产品名称")
    target_celebrity: str = Field(..., description="目标达人")
    generated_at: datetime = Field(
        default_factory=datetime.now, description="生成时间"
    )

    # 核心输出
    title_options: List[str] = Field(
        default_factory=list,
        description="3个标题选项（按有效性排序）"
    )
    content_script: str = Field(
        default="",
        description="内容脚本（PAS 逻辑）"
    )
    hashtags: List[str] = Field(
        default_factory=list, description="推荐话题"
    )

    # 发布建议
    posting_time_recommendation: str = Field(
        default="",
        description="发布时机建议"
    )
    posting_days_of_week: List[str] = Field(
        default_factory=list,
        description="推荐发布的星期"
    )

    # 互动管理
    expected_engagement_rate: float = Field(
        default=0.0,
        description="预期互动率"
    )
    cta_recommendations: List[str] = Field(
        default_factory=list,
        description="CTA (行动号召) 建议"
    )

    # 合规检查
    compliance_status: str = Field(
        default="passed",
        description="合规状态 (passed/warning/failed)"
    )
    compliance_notes: List[str] = Field(
        default_factory=list,
        description="合规备注"
    )

    # 追踪信息
    data_sources: List[str] = Field(
        default_factory=list,
        description="使用的参考笔记"
    )
    generation_model: str = Field(
        default="ohmyxhs",
        description="使用的生成模型"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="策略信心度"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "某品牌蓝光眼膜",
                "target_celebrity": "小红书达人",
                "title_options": [
                    "眼膜 | 25岁黑眼圈困扰3周逆袭记，终于不用遮瑕了",
                    "保姆级黑眼圈护理指南 | 这款眼膜让我重获自信",
                    "我从不用遮瑕了，黑眼圈眼膜的秘密在这里",
                ],
                "content_script": "引入段...\n主体段...\n总结段...",
                "hashtags": ["护肤", "黑眼圈", "眼膜"],
                "compliance_status": "passed",
                "confidence_score": 0.85,
            }
        }


# =============================================================================
# 采集配置模型
# =============================================================================


class CollectionConfig(BaseModel):
    """采集配置"""

    # 通用设置
    concurrent_requests: int = Field(default=5, ge=1, le=20, description="并发请求数")
    request_timeout: int = Field(default=30, ge=10, le=120, description="请求超时(秒)")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="重试次数")
    rate_limit_delay: float = Field(
        default=1.0, ge=0.1, le=10, description="请求间隔延迟(秒)"
    )

    # 采集限制
    max_notes_per_search: int = Field(
        default=100, ge=10, le=1000, description="每个搜索最多采集笔记数"
    )
    max_comments_per_note: int = Field(
        default=200, ge=10, le=1000, description="每个笔记最多采集评论数"
    )

    # 存储设置
    storage_backend: str = Field(
        default="json",
        description="存储后端 (json/sqlite)"
    )
    storage_path: str = Field(
        default="data/",
        description="数据存储路径"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "concurrent_requests": 5,
                "request_timeout": 30,
                "retry_attempts": 3,
                "rate_limit_delay": 1.0,
                "max_notes_per_search": 100,
                "max_comments_per_note": 200,
                "storage_backend": "json",
                "storage_path": "data/",
            }
        }


# =============================================================================
# 采集结果模型
# =============================================================================


class CollectionResult(BaseModel):
    """采集操作的结果"""

    success: bool = Field(..., description="是否成功")
    items_collected: int = Field(default=0, description="采集的项目数")
    items_failed: int = Field(default=0, description="失败的项目数")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_seconds: float = Field(default=0.0, description="耗时(秒)")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="操作时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "items_collected": 95,
                "items_failed": 5,
                "error_message": None,
                "duration_seconds": 45.3,
            }
        }
