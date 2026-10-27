import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PRAMAAN-X"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database: SQLite by default for zero-config hackathon demo; override with postgres:// in Docker
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pramaan_x.db")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "pramaan-x-hackathon-super-secret-key-2025-aicte")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    RULES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules")
    
    # Mock External Issuer latency in seconds (0 for instantaneous, >0 for realistic async demo)
    MOCK_ISSUER_SIMULATE_DELAY: bool = False
    
    class Config:
        case_sensitive = True

settings = Settings()

# Ensure uploads dir exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
