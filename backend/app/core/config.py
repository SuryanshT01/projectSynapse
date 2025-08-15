# backend/app/core/config.py
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Model and Data paths
    EMBEDDING_MODEL_NAME: str = Field("all-MiniLM-L6-v2", description="embedding model name")
    FAISS_INDEX_PATH: str = Field("backend/data/index.faiss", description="path to faiss index")
    METADATA_PATH: str = Field("backend/data/metadata.json", description="path to metadata json")
    UPLOAD_DIR: str = Field("backend/data/uploads", description="where uploaded PDFs are saved")

    # Chunking Strategy
    CHUNK_SIZE: int = Field(5, description="Number of sentences per chunk")
    CHUNK_OVERLAP: int = Field(1, description="Number of sentences overlap")

    # Search parameters
    TOP_K_SEARCH: int = Field(10, description="initial nearest neighbors to retrieve")
    MAX_RESULTS: int = Field(5, description="final number of sections to return")

    # Optional external keys (set via env vars or backend/.env)
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
    return Settings()
