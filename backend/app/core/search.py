# backend/app/core/search.py
import faiss
import json
import numpy as np
import os
import logging
import threading
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global state for our index and model - managed carefully
MODEL: Optional[SentenceTransformer] = None
INDEX: Optional[faiss.Index] = None
METADATA: List[Dict[str, Any]] = []

# Threading lock to ensure safe concurrent writes during ingestion
index_lock = threading.Lock()

def load_search_engine():
    """Loads the sentence transformer model, FAISS index, and metadata into memory."""
    global MODEL, INDEX, METADATA
    
    logger.info("Loading search engine...")
    try:
        MODEL = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info(f"SentenceTransformer model '{settings.EMBEDDING_MODEL_NAME}' loaded.")
        
        if os.path.exists(settings.FAISS_INDEX_PATH) and os.path.exists(settings.METADATA_PATH):
            INDEX = faiss.read_index(settings.FAISS_INDEX_PATH)
            logger.info(f"FAISS index loaded from {settings.FAISS_INDEX_PATH}. Total vectors: {INDEX.ntotal}")
            
            with open(settings.METADATA_PATH, 'r', encoding='utf-8') as f:
                METADATA = json.load(f)
            logger.info(f"Metadata loaded from {settings.METADATA_PATH}. Total entries: {len(METADATA)}")
        else:
            logger.warning("FAISS index or metadata not found. Initializing a new one.")
            # Initialize a new index if one doesn't exist
            embedding_dim = MODEL.get_sentence_embedding_dimension()
            INDEX = faiss.IndexFlatL2(embedding_dim)
            METADATA = []
            
    except Exception as e:
        logger.error(f"Error loading search engine: {e}", exc_info=True)
        raise

def get_model() -> SentenceTransformer:
    if MODEL is None:
        raise RuntimeError("Model is not loaded. Call load_search_engine() first.")
    return MODEL

def search_similar_chunks(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """Searches for chunks semantically similar to the query text."""
    if INDEX is None or INDEX.ntotal == 0:
        logger.warning("Search attempted but index is empty.")
        return []

    model = get_model()
    query_embedding = model.encode([query_text], convert_to_numpy=True)
    
    distances, indices = INDEX.search(query_embedding, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1: # faiss returns -1 for no result
            result = METADATA[idx]
            result['score'] = float(distances[0][i])
            results.append(result)
            
    return results

def add_chunks_to_index(chunks: List[str], metadatas: List[Dict[str, Any]]):
    """Encodes chunks and adds them to the FAISS index and metadata list."""
    global INDEX, METADATA
    if not chunks:
        return

    model = get_model()
    embeddings = model.encode(chunks, convert_to_numpy=True)
    
    with index_lock:
        INDEX.add(embeddings)
        METADATA.extend(metadatas)
        
        # Persist changes to disk
        faiss.write_index(INDEX, settings.FAISS_INDEX_PATH)
        with open(settings.METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(METADATA, f, indent=2)
            
    logger.info(f"Added {len(chunks)} new chunks to the index. Total vectors: {INDEX.ntotal}")