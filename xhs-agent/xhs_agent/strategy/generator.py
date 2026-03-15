"""
策略生成模块。

基于采集和分析的结果，调用 ohmyxhs SKILL 生成最优种草策略。
"""

from __future__ import annotations

import logging
from typing import Optional

from xhs_agent.types import (
    ProductInfo,
    CelebData,
    StrategySignals,
    XhsStrategyPlan,
)

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """
    策略生成器。

    基于产品信息、达人数据和分析信号，生成最优的种草策略。

    使用方式:
        generator = StrategyGenerator()
        strategy = await generator.generate_strategy(
            product=product_info,
            celebrity=celeb_data,
            signals=strategy_signals
        )
    """

    def __init__(self, ohmyxhs_skill_enabled: bool = True):
        """
        初始化策略生成器。

        Args:
            ohmyxhs_skill_enabled: 是否启用 ohmyxhs SKILL（如果禁用会使用模板）
        """
        self.ohmyxhs_skill_enabled = ohmyxhs_skill_enabled
        self._ohmyxhs_client = None

    async def generate_strategy(
        self,
        product: ProductInfo,
        celebrity: CelebData,
        signals: StrategySignals,
        reference_note_id: Optional[str] = None,
    ) -> XhsStrategyPlan:
        """
        生成策略。

        Args:
            product: 产品信息
            celebrity: 达人数据
            signals: 分析信号
            reference_note_id: 参考笔记 ID（可选）

        Returns:
            完整的策略方案
        """
        try:
            logger.info(
                f"Generating strategy for {product.product_name} "
                f"by {celebrity.name}"
            )

            # Step 1: 验证合规性
            compliance_status = self._check_compliance(product, signals)

            # Step 2: 准备输入
            context = self._prepare_context(
                product=product,
                celebrity=celebrity,
                signals=signals,
            )

            # Step 3: 调用生成（优先用 ohmyxhs，降级用模板）
            if self.ohmyxhs_skill_enabled:
                try:
                    plan = await self._generate_with_ohmyxhs(
                        context=context,
                        product=product,
                        celebrity=celebrity,
                    )
                except Exception as e:
                    logger.warning(
                        f"ohmyxhs SKILL failed, falling back to template: {e}"
                    )
                    plan = self._generate_with_template(
                        context=context,
                        product=product,
                        celebrity=celebrity,
                        signals=signals,
                    )
            else:
                plan = self._generate_with_template(
                    context=context,
                    product=product,
                    celebrity=celebrity,
                    signals=signals,
                )

            # Step 4: 添加合规信息
            plan.compliance_status = compliance_status["status"]
            plan.compliance_notes = compliance_status["notes"]

            # Step 5: 添加来源信息
            plan.data_sources = [reference_note_id] if reference_note_id else []
            plan.confidence_score = signals.signal_confidence

            logger.info(
                f"Strategy generated successfully "
                f"(confidence: {plan.confidence_score:.1%})"
            )

            return plan

        except Exception as e:
            logger.error(f"Failed to generate strategy: {e}")
            raise

    async def _generate_with_ohmyxhs(
        self,
        context: dict,
        product: ProductInfo,
        celebrity: CelebData,
    ) -> XhsStrategyPlan:
        """
        使用 ohmyxhs SKILL 生成策略。

        这是一个模拟实现，实际需要调用真实的 ohmyxhs。

        Args:
            context: 生成上下文
            product: 产品信息
            celebrity: 达人数据

        Returns:
            策略方案
        """
        logger.info("Generating strategy with ohmyxhs SKILL...")

        # 这里应该调用真实的 ohmyxhs SKILL
        # 目前使用模板作为降级方案
        return self._generate_with_template(
            context=context,
            product=product,
            celebrity=celebrity,
            signals=StrategySignals(note_id=""),
        )

    def _generate_with_template(
        self,
        context: dict,
        product: ProductInfo,
        celebrity: CelebData,
        signals: StrategySignals,
    ) -> XhsStrategyPlan:
        """
        使用模板生成策略。

        当 ohmyxhs 不可用时使用。

        Args:
            context: 生成上下文
            product: 产品信息
            celebrity: 达人数据
            signals: 分析信号

        Returns:
            策略方案
        """
        logger.info("Generating strategy with template...")

        # 提取关键信息
        pain_point = context.get("top_pain_point", "产品体验")
        emotions = context.get("user_emotions", ["获得感", "安心感"])
        frames = context.get("top_performing_frames", ["问题-分析-解决"])
        angle = context.get("content_angle_recommendation", "产品解决方案")

        # 生成标题（3个版本）
        titles = self._generate_titles(
            product=product,
            pain_point=pain_point,
            angle=angle,
        )

        # 生成内容脚本
        script = self._generate_script(
            product=product,
            celebrity=celebrity,
            pain_point=pain_point,
            emotions=emotions,
            angle=angle,
        )

        # 生成话题标签
        hashtags = self._generate_hashtags(
            product=product,
            pain_point=pain_point,
        )

        # 生成发布建议
        posting_time = self._recommend_posting_time()
        posting_days = ["Monday", "Wednesday", "Friday"]  # 工作日
        ctas = self._generate_ctas(product=product)

        return XhsStrategyPlan(
            product_name=product.product_name,
            target_celebrity=celebrity.name,
            title_options=titles,
            content_script=script,
            hashtags=hashtags,
            posting_time_recommendation=posting_time,
            posting_days_of_week=posting_days,
            cta_recommendations=ctas,
            expected_engagement_rate=0.08,  # 预期互动率 8%
            compliance_status="pending",
            generation_model="template",
            confidence_score=signals.signal_confidence if signals else 0.7,
        )

    def _generate_titles(
        self,
        product: ProductInfo,
        pain_point: str,
        angle: str,
    ) -> list[str]:
        """生成 3 个标题"""
        titles = [
            # 方案 A: 精准搜索式
            f'{pain_point} | 从"{product.product_name}"开始改善，坚持3周有奇效',

            # 方案 B: 解决方案式
            f"保姆级{angle} | {product.product_name}"
            f"让我重获自信",

            # 方案 C: 悬念故事式
            f"我再也不为{pain_point}烦恼了，"
            f"{product.product_name}的秘密在这里",
        ]

        return titles

    def _generate_script(
        self,
        product: ProductInfo,
        celebrity: CelebData,
        pain_point: str,
        emotions: list[str],
        angle: str,
    ) -> str:
        """生成内容脚本"""
        emotion_desc = "、".join(emotions)

        script = f"""【引入段】
你是否也被"{pain_point}"困扰着？
就像我一样，每次照镜子都很烦恼...

【主体段 - PAS 逻辑】

😢 第一部分：痛点分析
   {pain_point}的根本原因是...
   这不仅是产品问题，更是生活方式问题

🧴 第二部分：产品介绍
   {product.product_name} 的核心卖点：
   {chr(10).join([f"   ✨ {point}" for point in product.core_selling_points])}

📊 第三部分：真实体验
   使用 {product.product_name} 的 3 周变化：
   - 第 1 周：初步改善，肌肤感受到变化
   - 第 2 周：明显效果，周围人都有所察觉
   - 第 3 周：稳定维持，建立护肤新习惯

💡 第四部分：专业建议
   ✓ 坚持最重要（不要期望一夜见效）
   ✓ 配合正确手法（按摩很关键）
   ✓ 日常防护同步（防晒很必要）

【总结段】
{product.product_name} 不仅解决了我的"{pain_point}"困扰，
更重要的是让我找回了（{emotion_desc}）的感觉。

👇 评论区分享你的亲身经历吧！
"""

        return script

    def _generate_hashtags(
        self,
        product: ProductInfo,
        pain_point: str,
    ) -> list[str]:
        """生成推荐话题"""
        hashtags = [
            product.category.value,  # 品类
            pain_point,  # 痛点
            "真实测评",
            "护肤笔记",
            "变美之旅",
            "坚持的力量",
        ]

        return hashtags

    def _recommend_posting_time(self) -> str:
        """建议发布时间"""
        return "工作日 12:00 或 20:00（用户高活跃时段）"

    def _generate_ctas(self, product: ProductInfo) -> list[str]:
        """生成 CTA（行动号召）"""
        ctas = [
            f"评论区分享你对{product.product_name}的期待！",
            f"如果你也有{product.category.value}的困扰，不妨试试？",
            "转发给身边有同样困扰的朋友呀～",
            "收藏本篇，坚持 3 周后回来看看效果变化～",
        ]

        return ctas

    def _prepare_context(
        self,
        product: ProductInfo,
        celebrity: CelebData,
        signals: StrategySignals,
    ) -> dict:
        """
        准备生成上下文。

        将产品信息、达人数据、分析信号组合成生成器可用的格式。
        """
        return {
            "product_name": product.product_name,
            "product_category": product.category.value,
            "core_selling_points": product.core_selling_points,
            "price": product.price,
            "price_tier": product.price_tier.value,
            "target_audience": product.target_audience,

            "celebrity_name": celebrity.name,
            "celebrity_followers": celebrity.followers,
            "celebrity_style": ",".join(s.value for s in celebrity.content_styles),

            "top_pain_point": signals.top_pain_point,
            "top_performing_frames": signals.top_performing_frames,
            "user_emotions": signals.user_emotions,
            "content_angle_recommendation": signals.content_angle_recommendation,
            "competitor_insights": signals.competitor_insights,
        }

    def _check_compliance(
        self,
        product: ProductInfo,
        signals: StrategySignals,
    ) -> dict:
        """
        检查合规性。

        验证内容是否违反平台规则。
        """
        notes = []
        status = "passed"

        # 检查禁用词汇
        forbidden_words = [
            "绝对", "最好", "唯一", "顶级",  # 绝对词
            "治疗", "修复", "激活", "再生",  # 医疗词
            "一夜见效", "立竿见影", "100%有效",  # 夸大词
        ]

        script_text = signals.competitor_insights or ""

        for word in forbidden_words:
            if word in script_text:
                notes.append(f"警告: 包含禁用词'{word}'")
                status = "warning"

        # 检查产品类别风险
        if product.category.value in ["medical_beauty", "finance", "real_estate"]:
            notes.append(
                f"⚠️ 产品品类'{product.category.value}'属于高风险，"
                f"需要特别谨慎表述"
            )
            status = "warning"

        return {
            "status": status,
            "notes": notes,
        }


# 便利函数
async def generate_strategy_plan(
    product: ProductInfo,
    celebrity: CelebData,
    signals: StrategySignals,
) -> XhsStrategyPlan:
    """
    快速生成策略方案。

    Args:
        product: 产品信息
        celebrity: 达人数据
        signals: 分析信号

    Returns:
        完整的策略方案

    示例:
        strategy = await generate_strategy_plan(product, celeb, signals)
        print(f"标题: {strategy.title_options[0]}")
    """
    generator = StrategyGenerator()
    return await generator.generate_strategy(product, celebrity, signals)
