import json
import os
import logging
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.schemas.article import Article, DeepSeekEvaluation

# Ensure .env is loaded so DEEPSEEK_* variables are available when not exported
load_dotenv()
logger = logging.getLogger(__name__)


class DeepSeekEvaluator:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        self.client: Optional[AsyncOpenAI] = None
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            logger.warning("DEEPSEEK_API_KEY not set, DeepSeekEvaluator will use mock responses.")

    async def evaluate(self, article: Article, version: int) -> DeepSeekEvaluation:
        if not self.client:
            logger.info("DeepSeek mock: client not initialized, skip real call (article_id=%s, version=%s)", getattr(article, "id", None), version)
            return self._mock(article, version)

        prompt = (
            "You are a senior product manager + investor + market analyst. "
            "Given a product, produce a structured JSON with fields: "
            "overall_score (0-100), product_view, investor_view, market_view, recommendation. "
            "Be concise but specific."
        )

        sources_text = ", ".join({f'{s.source}:{s.source_id}' for s in (article.sources or [])})
        analysis_summary = article.analysis.summary if article.analysis else ""

        try:
            logger.info("DeepSeek request: article_id=%s version=%s model=%s", getattr(article, "id", None), version, self.model)
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Title: {article.title}\n"
                            f"URL: {article.url}\n"
                            f"Sources: {sources_text}\n"
                            f"AI Summary: {analysis_summary}\n"
                            "Return only the JSON."
                        ),
                    },
                ],
                response_format={"type": "json_object"},
            )
            logger.info("DeepSeek success: article_id=%s version=%s", getattr(article, "id", None), version)
            content = completion.choices[0].message.content or "{}"
            data = json.loads(content)
            return DeepSeekEvaluation(
                version=version,
                model=self.model,
                overall_score=int(data.get("overall_score", 0)),
                product_view=data.get("product_view", ""),
                investor_view=data.get("investor_view", ""),
                market_view=data.get("market_view", ""),
                recommendation=data.get("recommendation", ""),
                created_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error("DeepSeek evaluation failed, falling back to mock (article_id=%s version=%s): %r", getattr(article, "id", None), version, e)
            # 回退到 mock，避免请求失败阻断流程
            return self._mock(article, version)

    async def evaluate_full(self, article: Article, version: int) -> DeepSeekEvaluation:
        """Produce a long-form, multi-perspective evaluation; returns same schema with full_evaluation populated."""
        if not self.client:
            logger.info("DeepSeek mock (full): client not initialized (article_id=%s, version=%s)", getattr(article, "id", None), version)
            base = self._mock(article, version)
            base.full_evaluation = self._mock_full_text(article)
            return base

        detailed_prompt = (
            "You are a senior product leader, investor, and market strategist. "
            "Provide a comprehensive assessment covering:\n"
            "- Product view: vision, differentiation, UX/tech moat, execution risks.\n"
            "- Investor view: market size, traction signals, monetization, defendability, funding posture.\n"
            "- Market view: competitive landscape, timing, regulatory/logistics hurdles, go-to-market angles.\n"
            "- Recommendation: clear next steps and level of conviction.\n"
            "Return ONLY a well-structured narrative (not JSON), 4-6 short paragraphs, crisp and actionable."
        )

        sources_text = ", ".join({f'{s.source}:{s.source_id}' for s in (article.sources or [])})
        analysis_summary = article.analysis.summary if article.analysis else ""

        try:
            logger.info("DeepSeek full request: article_id=%s version=%s model=%s", getattr(article, "id", None), version, self.model)
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": detailed_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Title: {article.title}\n"
                            f"URL: {article.url}\n"
                            f"Sources: {sources_text}\n"
                            f"AI Summary: {analysis_summary}\n"
                            "Return only the narrative."
                        ),
                    },
                ],
            )
            logger.info("DeepSeek full success: article_id=%s version=%s", getattr(article, "id", None), version)
            full_text = completion.choices[0].message.content or ""
            # Reuse base eval for score/short fields; mock short fields if needed
            base = await self.evaluate(article, version)
            base.full_evaluation = full_text
            return base
        except Exception as e:
            logger.error("DeepSeek full evaluation failed, falling back to mock (article_id=%s version=%s): %r", getattr(article, "id", None), version, e)
            base = self._mock(article, version)
            base.full_evaluation = self._mock_full_text(article)
            return base

    def _mock(self, article: Article, version: int) -> DeepSeekEvaluation:
        logger.debug("DeepSeek mock used for article_id=%s version=%s", getattr(article, "id", None), version)
        return DeepSeekEvaluation(
            version=version,
            model=self.model,
            overall_score=70,
            product_view=f"{article.title} has mid-level product potential; core experience needs refinement.",
            investor_view="Medium risk; observe traction before capital deployment.",
            market_view="Crowded niche; differentiation and distribution are key.",
            recommendation="Track metrics; consider investment/push after stronger signals.",
            created_at=datetime.utcnow(),
        )

    def _mock_full_text(self, article: Article) -> str:
        return (
            f"Product: {article.title} shows promise but needs clearer differentiation and tighter UX.\n"
            "Investor: Market is competitive; watch for early traction and defendability before funding.\n"
            "Market: Timing is fair, but incumbents exist; leverage GTM niches and partnerships.\n"
            "Recommendation: Pilot with a focused segment, measure conversion, then decide on scale/invest."
        )
