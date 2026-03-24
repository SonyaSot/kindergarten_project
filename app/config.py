from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Optional: отдельные поля для Docker (если нужно)
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # ← ИГНОРИРОВАТЬ лишние поля из .env!

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()