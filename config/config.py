from typing import List, Optional, Union
import os
from pydantic import AnyHttpUrl, PostgresDsn, field_validator, validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Urban Lens"
    DEBUG: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"  # Default to localhost for development
    POSTGRES_USER: str = "urban_lens"
    POSTGRES_PASSWORD: str = "urban_lens"
    POSTGRES_DB: str = "urban_lens"
    POSTGRES_PORT: str = "5432"
    
    # Database operations
    RUN_MIGRATIONS: bool = False  # Temporarily disabled for testing

    @property
    def DATABASE_URL(self) -> str:
        """Return the async database URL"""
        # Check for environment variable - Render uses DATABASE_URL
        render_db_url = os.environ.get("DATABASE_URL")
        if render_db_url:
            # If using Render, convert standard postgres:// URL to asyncpg format
            return render_db_url.replace("postgres://", "postgresql+asyncpg://")
        # Otherwise use the individual components for local development
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Return a synchronous database URL for Alembic"""
        # Check for environment variable - Render uses DATABASE_URL
        render_db_url = os.environ.get("DATABASE_URL")
        if render_db_url:
            return render_db_url
        # Otherwise use the individual components for local development
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"  # Default to localhost

    # Security
    SECRET_KEY: str = ""  # Default value for development
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    
    # Google Cloud Storage
    GCP_PROJECT_ID: Optional[str] = None
    GCP_BUCKET_NAME: Optional[str] = None
    GCP_CREDENTIALS_FILE: Optional[str] = None
    USE_GCS: bool = False  # Toggle for using Google Cloud Storage or local storage
    
 
    MAIL_FROM: Optional[str] = None
    FRONTEND_URL: Optional[str] = "http://localhost:3000"  # Default for development
    


    # Pydantic v2 configuration
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


# Create a global settings instance
settings = Settings()
