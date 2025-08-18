# backend/app/core/config.py
import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define the base directory for the app once.
# This makes all paths robust and independent of the current working directory.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    """
    Manages all application settings, loading from environment variables and a .env file.
    """
    # --- Paths for PDF Parser Models ---
    MODEL_PATH: str = Field(default=os.path.join(APP_DIR, 'models', 'lgbm_model.joblib'))
    ENCODER_PATH: str = Field(default=os.path.join(APP_DIR, 'models', 'label_encoder.joblib'))
    
    # --- Paths for Vector Search & Data ---
    EMBEDDING_MODEL_NAME: str = Field("all-MiniLM-L6-v2", description="embedding model name")
    FAISS_INDEX_PATH: str = Field("backend/data/index.faiss", description="path to faiss index")
    METADATA_PATH: str = Field("backend/data/metadata.json", description="path to metadata json")
    UPLOAD_DIR: str = Field("backend/data/uploads", description="where uploaded PDFs are saved")

    # --- Text Processing Strategy ---
    CHUNK_SIZE: int = Field(5, description="Number of sentences per chunk")
    CHUNK_OVERLAP: int = Field(1, description="Number of sentences overlap")

    # --- Search Parameters ---
    TOP_K_SEARCH: int = Field(10, description="initial nearest neighbors to retrieve")
    MAX_RESULTS: int = Field(5, description="final number of sections to return")

    # --- Optional External Service Keys ---
    GEMINI_MODEL: Optional[str] = None
    LLM_PROVIDER: Optional[str] = None
    TTS_PROVIDER: Optional[str] = None
    AZURE_TTS_KEY: Optional[str] = None
    AZURE_TTS_ENDPOINT: Optional[str] = None
    ADOBE_EMBED_API_KEY: Optional[str] = None

    # pydantic-settings config: read backend/.env relative to project root
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    """
    return Settings()