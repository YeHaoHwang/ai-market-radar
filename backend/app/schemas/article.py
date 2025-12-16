from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SourceRef(BaseModel):
    source: str
    source_id: str

class ArticleBase(BaseModel):
    title: str
    url: str
    source: str
    source_id: str
    publish_date: Optional[datetime] = None
    sources: List[SourceRef] = []

class ArticleCreate(ArticleBase):
    raw_content: Optional[str] = None
    # Current snapshot metrics
    current_metric_value: int = 0 # e.g. votes, score, likes
    current_rank: Optional[int] = None

class MetricPoint(BaseModel):
    recorded_at: datetime
    value: int
    rank: Optional[int]

class AIAnalysis(BaseModel):
    summary: str
    category: str
    score: int
    reasoning: str
    tags: List[str]

class DeepSeekEvaluation(BaseModel):
    version: int
    model: str
    overall_score: int
    product_view: str
    investor_view: str
    market_view: str
    recommendation: str
    created_at: datetime
    full_evaluation: str | None = None

class Article(ArticleBase):
    id: int
    first_seen_at: datetime
    last_seen_at: datetime
    seen_count: int
    platforms_count: int = 1
    
    analyzed_at: Optional[datetime] = None
    analysis: Optional[AIAnalysis] = None
    
    # Include history in response? Maybe just latest or summary
    metrics_history: List[MetricPoint] = []
    evaluations: List[DeepSeekEvaluation] = []

    class Config:
        from_attributes = True
