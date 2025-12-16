from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.api.routes import ingest_all_sources
from app.db.database import SessionLocal

scheduler = AsyncIOScheduler()


async def _run_ingestion_job():
    db: Session = SessionLocal()
    try:
        await ingest_all_sources(limit=20, db=db)
    finally:
        db.close()


def start_scheduler():
    # 每天 10:00 am 自动抓取/分析
    scheduler.add_job(_run_ingestion_job, CronTrigger(hour=10, minute=0), id="daily_ingest", replace_existing=True)
    scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
