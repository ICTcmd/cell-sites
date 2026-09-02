"""Configuration management using Pydantic Settings"""
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/cellsite_db"
    
    # Application
    APP_NAME: str = "Cell Site Mapping System"
    API_VERSION: str = "v1"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # City Bounding Box
    CITY_NAME: str = "Manila"
    COUNTRY: str = "Philippines"
    BBOX_MIN_LAT: float = 14.40
    BBOX_MAX_LAT: float = 14.80
    BBOX_MIN_LON: float = 120.90
    BBOX_MAX_LON: float = 121.15
    
    # Triangulation Parameters
    MIN_SAMPLES_FOR_TRIANGULATION: int = 5
    MAX_DISTANCE_FROM_TOWER_METERS: int = 5000
    RSRP_WEIGHT_EXPONENT: float = 2.5
    
    # External APIs
    OPENCELLID_API_KEY: str = ""
    CELLMAPPER_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
