from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio
import logging
from urllib.parse import urlparse

from app.schemas.article import Article, ArticleCreate, AIAnalysis, MetricPoint, SourceRef, DeepSeekEvaluation
from app.services.fetcher_base import BaseFetcher
from app.services.hn_fetcher import HackerNewsFetcher
from app.services.ph_fetcher import ProductHuntFetcher
from app.services.betalist_fetcher import BetaListFetcher
from app.services.hf_fetcher import HuggingFaceFetcher
from app.services.analyzer import LLMAnalyzer
from app.services.deepseek import DeepSeekEvaluator
from app.services.utils import normalize_url
from app.db.database import get_db, engine, Base
from app.db.models import ArticleModel, ArticleMetricModel, ArticleEvaluationModel

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Registry of all available data sources
FETCHERS: List[BaseFetcher] = [
    HackerNewsFetcher(),
    ProductHuntFetcher(),
    BetaListFetcher(),
    HuggingFaceFetcher()
]

analyzer = LLMAnalyzer()
deepseek_evaluator = DeepSeekEvaluator()

async def ingest_all_sources(limit: int, db: Session) -> List[Article]:
    # 1. Parallel Fetching from all sources
    fetch_tasks = [f.fetch_latest(limit=limit) for f in FETCHERS]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    
    all_raw_articles = []
    for res in results:
        if isinstance(res, list):
            all_raw_articles.extend(res)
        else:
            logger.error(f"Fetcher error during ingestion: {res}")
    
    # Normalize URLs for cross-platform dedupe
    for raw in all_raw_articles:
        raw.url = normalize_url(raw.url)
        raw.sources = [SourceRef(source=raw.source, source_id=raw.source_id)]
    
    incoming_urls = [raw.url for raw in all_raw_articles]
    existing_articles = db.query(ArticleModel).filter(ArticleModel.url.in_(incoming_urls)).all()
    existing_map = {article.url: article for article in existing_articles}
    
    processed_articles: List[Article] = []
    
    for raw in all_raw_articles:
        # Check if exists (by normalized URL)
        db_article = existing_map.get(raw.url)
        source_entry = {"source": raw.source, "source_id": raw.source_id}
        
        if db_article:
            # --- UPDATE EXISTING ---
            db_article.last_seen_at = datetime.utcnow()
            db_article.seen_count += 1
            
            # Merge sources list
            existing_sources = db_article.sources or []
            if source_entry not in existing_sources:
                existing_sources.append(source_entry)
            db_article.sources = existing_sources

            # Add metric point
            metric = ArticleMetricModel(
                article=db_article,
                metric_value=raw.current_metric_value,
                rank=raw.current_rank
            )
            db.add(metric)
            db.commit()
            db.refresh(db_article)
            processed_articles.append(_db_to_schema(db_article))
            
        else:
            # --- CREATE NEW ---
            # Analyze first
            try:
                analysis = await analyzer.analyze(raw)
            except Exception as e:
                logger.error(f"Analysis failed for {raw.url}: {e}")
                continue
            
            db_article = ArticleModel(
                title=raw.title,
                url=raw.url,
                source=raw.source,
                source_id=raw.source_id,
                publish_date=raw.publish_date,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                seen_count=1,
                analyzed_at=datetime.utcnow(),
                analysis_summary=analysis.summary,
                analysis_category=analysis.category,
                analysis_score=analysis.score,
                analysis_reasoning=analysis.reasoning,
                analysis_tags=analysis.tags,
                sources=[source_entry],
            )
            db.add(db_article)
            db.flush() # Get ID
            
            # Update map to handle duplicate URLs within the same batch (e.g. same link on HN and PH)
            existing_map[raw.url] = db_article
            
            # Add first metric point
            metric = ArticleMetricModel(
                article_id=db_article.id,
                metric_value=raw.current_metric_value,
                rank=raw.current_rank
            )
            db.add(metric)
            db.commit()
            db.refresh(db_article)
            processed_articles.append(_db_to_schema(db_article))
        
    return processed_articles

@router.post("/ingest", response_model=List[Article])
async def trigger_ingestion(limit: int = 20, db: Session = Depends(get_db)):
    return await ingest_all_sources(limit=limit, db=db)

@router.get("/feed", response_model=List[Article])
async def get_feed(db: Session = Depends(get_db)):
    # Get all articles, sorted by last_seen desc (freshness) and score
    # For MVP, just simple sort by analysis score
    articles = db.query(ArticleModel).order_by(ArticleModel.analysis_score.desc()).all()
    return [_db_to_schema(a) for a in articles]

@router.post("/articles/{article_id}/evaluate", response_model=DeepSeekEvaluation)
async def evaluate_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(ArticleModel).filter(ArticleModel.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    schema_article = _db_to_schema(article)
    version = len(article.evaluations or []) + 1

    evaluation = await deepseek_evaluator.evaluate(schema_article, version)

    content_json = evaluation.model_dump(mode="json")

    db_eval = ArticleEvaluationModel(
        article_id=article.id,
        version=version,
        model_name=evaluation.model,
        overall_score=evaluation.overall_score,
        content=content_json,
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)

    return _eval_to_schema(db_eval)

def _db_to_schema(db_item: ArticleModel) -> Article:
    """Helper to convert DB model to Pydantic schema"""
    analysis = None
    if db_item.analysis_score is not None:
        analysis = AIAnalysis(
            summary=db_item.analysis_summary or "",
            category=db_item.analysis_category or "Uncategorized",
            score=db_item.analysis_score,
            reasoning=db_item.analysis_reasoning or "",
            tags=db_item.analysis_tags or []
        )
    
    # Sort history by date desc
    history = sorted(db_item.metrics_history, key=lambda x: x.recorded_at, reverse=True)
    sources_list = db_item.sources or [{"source": db_item.source, "source_id": db_item.source_id}]
    
    return Article(
        id=db_item.id,
        title=db_item.title,
        url=db_item.url,
        source=db_item.source,
        source_id=db_item.source_id,
        publish_date=db_item.publish_date,
        first_seen_at=db_item.first_seen_at,
        last_seen_at=db_item.last_seen_at,
        seen_count=db_item.seen_count,
        sources=[SourceRef(**s) for s in sources_list],
        platforms_count=len(sources_list),
        analyzed_at=db_item.analyzed_at,
        analysis=analysis,
        metrics_history=[
            MetricPoint(recorded_at=m.recorded_at, value=m.metric_value, rank=m.rank) 
            for m in history
        ],
        evaluations=[_eval_to_schema(ev) for ev in db_item.evaluations]
    )

def _eval_to_schema(db_item: ArticleEvaluationModel) -> DeepSeekEvaluation:
    content = db_item.content or {}
    return DeepSeekEvaluation(
        version=db_item.version,
        model=db_item.model_name,
        overall_score=content.get("overall_score", db_item.overall_score),
        product_view=content.get("product_view", ""),
        investor_view=content.get("investor_view", ""),
        market_view=content.get("market_view", ""),
        recommendation=content.get("recommendation", ""),
        created_at=db_item.created_at,
    )
