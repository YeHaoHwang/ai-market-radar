from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class ArticleModel(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    source = Column(String)
    source_id = Column(String)
    publish_date = Column(DateTime, default=datetime.utcnow)
    
    # Tracking
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    seen_count = Column(Integer, default=1)

    # List of sources where this item appeared (to aggregate duplicates across platforms)
    sources = Column(JSON, default=list)
    
    # AI Analysis (Static snapshot, or could be updated)
    analyzed_at = Column(DateTime, nullable=True)
    analysis_summary = Column(Text, nullable=True)
    analysis_category = Column(String, nullable=True)
    analysis_score = Column(Integer, nullable=True)
    analysis_reasoning = Column(Text, nullable=True)
    analysis_tags = Column(JSON, nullable=True)

    # Relationship to metrics history
    metrics_history = relationship("ArticleMetricModel", back_populates="article", cascade="all, delete-orphan")
    # Relationship to DeepSeek evaluations (multiple versions)
    evaluations = relationship("ArticleEvaluationModel", back_populates="article", cascade="all, delete-orphan")

class ArticleMetricModel(Base):
    __tablename__ = "article_metrics"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # Raw metrics from the source (normalized)
    # e.g., HN score, PH votes, HF likes. 
    # We store the primary "heat" metric here.
    metric_value = Column(Integer, default=0) 
    
    # Rank in the feed (optional, good for trend analysis)
    rank = Column(Integer, nullable=True)
    
    article = relationship("ArticleModel", back_populates="metrics_history")

class ArticleEvaluationModel(Base):
    __tablename__ = "article_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    version = Column(Integer, default=1)
    model_name = Column(String, default="deepseek-chat")
    overall_score = Column(Integer, default=0)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Long-form evaluation (full prompt/answer) stored separately
    full_evaluation = Column(Text, nullable=True)

    article = relationship("ArticleModel", back_populates="evaluations")
