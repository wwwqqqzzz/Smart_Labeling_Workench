from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 数据库
    DATABASE_URL: str = "sqlite:///./data/conversations.db"

    # API Keys
    GLM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # 应用配置
    APP_NAME: str = "智能打标便捷器"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://frontend-wqz.vercel.app",
        "https://smart-labeling-workbench.vercel.app"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
