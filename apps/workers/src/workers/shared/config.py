"""
Configuration management for workers.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ai_vr_tour_guide"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # NATS
    nats_url: str = "nats://localhost:4222"
    
    # Storage
    s3_bucket: str = "ai-vr-tour-guide-assets"
    s3_region: str = "us-east-1"
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    s3_endpoint: Optional[str] = "http://localhost:9000"  # MinIO for development
    
    # AI Services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # TTS
    elevenlabs_api_key: Optional[str] = None
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "eastus"
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
