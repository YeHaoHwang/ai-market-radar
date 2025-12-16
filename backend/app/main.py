from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router as api_router
from app.core.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 设置，允许前端域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def on_startup():
    start_scheduler()

@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()

@app.get("/")
async def root():
    return {"message": "Welcome to AI Market Radar API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}
