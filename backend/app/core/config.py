from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow",  # 允许未声明的环境变量（如 DEEPSEEK_API_KEY / OPENAI_API_KEY）
    )

    PROJECT_NAME: str = "AI Market Radar"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS (Cross-Origin Resource Sharing)
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

settings = Settings()
