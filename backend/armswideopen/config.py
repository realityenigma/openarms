"""Configuration management for OpenArms"""
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "OpenArms"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./armswideopen.db"
    
    # Storage
    storage_path: str = "./storage"
    git_lfs_enabled: bool = True
    
    # API
    api_title: str = "OpenArms API"
    api_version: str = "0.1.0"
    api_description: str = "Open-source implementation of Hugging Face Hub"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
