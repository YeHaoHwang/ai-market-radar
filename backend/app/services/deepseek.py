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
            "你是资深产品经理 + 投资人 + 市场分析师的组合，需对产品未来发展做评估。\n"
            "请基于以下信息（标题、链接、来源、AI分析摘要等）给出 JSON 结构化结论，字段：\n"
            "overall_score (0-100), product_view, investor_view, market_view, recommendation。\n"
            "输出必须是 JSON。"
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
                            "请返回指定 JSON。"
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

    def _mock(self, article: Article, version: int) -> DeepSeekEvaluation:
        logger.debug("DeepSeek mock used for article_id=%s version=%s", getattr(article, "id", None), version)
        return DeepSeekEvaluation(
            version=version,
            model=self.model,
            overall_score=70,
            product_view=f"{article.title} 产品潜力中等，需继续打磨核心体验。",
            investor_view="风险偏中，建议观察后跟进。",
            market_view="细分赛道竞争激烈，需强化差异化。",
            recommendation="短期保持跟踪，关键指标提升后再考虑投资/推广。",
            created_at=datetime.utcnow(),
        )
