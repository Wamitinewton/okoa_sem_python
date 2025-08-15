from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Study App"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "postgres")
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
       return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM","HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # YouTube API
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = os.getenv("BACKEND_CORS_ORIGINS", "")
    
    class Config:
        env_file = ".env"

settings = Settings()



