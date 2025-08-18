# backend/app/core/search.py - IMPROVED WITH HYBRID SEARCH
import faiss
import json
import numpy as np
import os
import logging
import threading
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global state for our indices and model - managed carefully
MODEL: Optional[SentenceTransformer] = None
INDEX: Optional[faiss.Index] = None
BM25_INDEX: Optional[BM25Okapi] = None
TOKENIZED_CORPUS: List[List[str]] = []
METADATA: List[Dict[str, Any]] = []

# Threading lock to ensure safe concurrent writes during ingestion
index_lock = threading.Lock()

# RRF Configuration
RRF_K = 60  # Rank constant for Reciprocal Rank Fusion

def load_search_engine():
    """Loads the sentence transformer model, FAISS index, BM25 index, and metadata into memory."""
    global MODEL, INDEX, BM25_INDEX, TOKENIZED_CORPUS, METADATA
    
    logger.info("Loading hybrid search engine...")
    try:
        # Load embedding model
        MODEL = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info(f"SentenceTransformer model '{settings.EMBEDDING_MODEL_NAME}' loaded.")
        
        # Load existing indices and metadata if they exist
        if os.path.exists(settings.FAISS_INDEX_PATH) and os.path.exists(settings.METADATA_PATH):
            # Load FAISS index
            INDEX = faiss.read_index(settings.FAISS_INDEX_PATH)
            logger.info(f"FAISS index loaded from {settings.FAISS_INDEX_PATH}. Total vectors: {INDEX.ntotal}")
            
            # Load metadata
            with open(settings.METADATA_PATH, 'r', encoding='utf-8') as f:
                METADATA = json.load(f)
            logger.info(f"Metadata loaded from {settings.METADATA_PATH}. Total entries: {len(METADATA)}")
            
            # Load BM25 index if it exists
            bm25_path = settings.METADATA_PATH.replace('.json', '_bm25.json')
            if os.path.exists(bm25_path):
                with open(bm25_path, 'r', encoding='utf-8') as f:
                    bm25_data = json.load(f)
                    TOKENIZED_CORPUS = bm25_data['tokenized_corpus']
                    
                if TOKENIZED_CORPUS:
                    BM25_INDEX = BM25Okapi(TOKENIZED_CORPUS)
                    logger.info(f"BM25 index loaded. Total documents: {len(TOKENIZED_CORPUS)}")
                else:
                    logger.warning("BM25 tokenized corpus is empty.")
            else:
                logger.warning("BM25 index file not found. BM25 search will be unavailable.")
                
        else:
            logger.warning("FAISS index or metadata not found. Initializing new indices.")
            # Initialize new indices if they don't exist
            embedding_dim = MODEL.get_sentence_embedding_dimension()
            INDEX = faiss.IndexFlatL2(embedding_dim)
            BM25_INDEX = None
            TOKENIZED_CORPUS = []
            METADATA = []
            
    except Exception as e:
        logger.error(f"Error loading search engine: {e}", exc_info=True)
        raise

def get_model() -> SentenceTransformer:
    """Returns the loaded sentence transformer model."""
    if MODEL is None:
        raise RuntimeError("Model is not loaded. Call load_search_engine() first.")
    return MODEL

def tokenize_text(text: str) -> List[str]:
    """Tokenizes text for BM25 processing."""
    # Simple tokenization - you can enhance this with more sophisticated NLP
    return text.lower().split()

def reciprocal_rank_fusion(dense_results: List[Dict], sparse_results: List[Dict], k: int = RRF_K) -> List[Dict]:
    """
    Implements Reciprocal Rank Fusion (RRF) to combine results from dense and sparse retrieval.
    
    RRF Formula: score = sum(1/(k + rank_i)) for all rankings where document appears
    
    Args:
        dense_results: Results from FAISS (dense retrieval)
        sparse_results: Results from BM25 (sparse retrieval)
        k: RRF rank constant (default: 60)
    
    Returns:
        List of fused and re-ranked results
    """
    # Create a dictionary to store combined scores for each document
    doc_scores = {}
    
    # Process dense results (FAISS)
    for rank, result in enumerate(dense_results):
        doc_key = (result['doc_name'], result['section_title'], result['page'])
        rrf_score = 1.0 / (k + rank + 1)  # rank + 1 because rank is 0-indexed
        
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                'result': result,
                'rrf_score': 0.0,
                'dense_rank': rank + 1,
                'sparse_rank': None
            }
        
        doc_scores[doc_key]['rrf_score'] += rrf_score
    
    # Process sparse results (BM25)
    for rank, result in enumerate(sparse_results):
        doc_key = (result['doc_name'], result['section_title'], result['page'])
        rrf_score = 1.0 / (k + rank + 1)  # rank + 1 because rank is 0-indexed
        
        if doc_key not in doc_scores:
            doc_scores[doc_key] = {
                'result': result,
                'rrf_score': 0.0,
                'dense_rank': None,
                'sparse_rank': rank + 1
            }
        else:
            doc_scores[doc_key]['sparse_rank'] = rank + 1
        
        doc_scores[doc_key]['rrf_score'] += rrf_score
    
    # Sort by RRF score (descending) and return results
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x['rrf_score'], reverse=True)
    
    # Return the original result format with added RRF score
    fused_results = []
    for doc_data in sorted_docs:
        result = doc_data['result'].copy()
        result['rrf_score'] = doc_data['rrf_score']
        result['dense_rank'] = doc_data['dense_rank']
        result['sparse_rank'] = doc_data['sparse_rank']
        fused_results.append(result)
    
    return fused_results

def search_faiss(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """Performs dense retrieval using FAISS."""
    if INDEX is None or INDEX.ntotal == 0:
        logger.warning("FAISS search attempted but index is empty.")
        return []
    
    model = get_model()
    query_embedding = model.encode([query_text], convert_to_numpy=True)
    
    distances, indices = INDEX.search(query_embedding, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # faiss returns -1 for no result
            result = METADATA[idx].copy()
            result['faiss_score'] = float(distances[0][i])
            result['faiss_rank'] = i + 1
            results.append(result)
            
    return results

def search_bm25(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """Performs sparse retrieval using BM25."""
    if BM25_INDEX is None or not TOKENIZED_CORPUS:
        logger.warning("BM25 search attempted but index is not available.")
        return []
    
    # Tokenize the query
    query_tokens = tokenize_text(query_text)
    
    # Get BM25 scores
    scores = BM25_INDEX.get_scores(query_tokens)
    
    # Get top-k results
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for i, idx in enumerate(top_indices):
        if idx < len(METADATA):
            result = METADATA[idx].copy()
            result['bm25_score'] = float(scores[idx])
            result['bm25_rank'] = i + 1
            results.append(result)
    
    return results

def search_similar_chunks(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """
    Performs hybrid search combining FAISS and BM25 using Reciprocal Rank Fusion.
    
    Args:
        query_text: The search query
        top_k: Number of results to retrieve from each method before fusion
    
    Returns:
        List of fused and re-ranked results
    """
    logger.info(f"Performing hybrid search for query: '{query_text[:50]}...'")
    
    # Perform both dense and sparse retrieval
    dense_results = search_faiss(query_text, top_k)
    sparse_results = search_bm25(query_text, top_k)
    
    logger.info(f"FAISS returned {len(dense_results)} results")
    logger.info(f"BM25 returned {len(sparse_results)} results")
    
    # If only one method has results, return those results
    if not dense_results and not sparse_results:
        return []
    elif not dense_results:
        return sparse_results[:top_k]
    elif not sparse_results:
        return dense_results[:top_k]
    
    # Perform Reciprocal Rank Fusion
    fused_results = reciprocal_rank_fusion(dense_results, sparse_results)
    
    logger.info(f"RRF fusion produced {len(fused_results)} combined results")
    
    return fused_results

def add_chunks_to_index(chunks: List[str], metadatas: List[Dict[str, Any]]):
    """
    Encodes chunks and adds them to both FAISS and BM25 indices.
    
    Args:
        chunks: List of text chunks to index
        metadatas: List of metadata dictionaries for each chunk
    """
    global INDEX, BM25_INDEX, TOKENIZED_CORPUS, METADATA
    
    if not chunks:
        return
    
    model = get_model()
    embeddings = model.encode(chunks, convert_to_numpy=True)
    
    # Tokenize chunks for BM25
    new_tokenized = [tokenize_text(chunk) for chunk in chunks]
    
    with index_lock:
        # Add to FAISS index
        INDEX.add(embeddings)
        
        # Update metadata
        METADATA.extend(metadatas)
        
        # Update BM25 index
        TOKENIZED_CORPUS.extend(new_tokenized)
        
        # Rebuild BM25 index with all documents
        if TOKENIZED_CORPUS:
            BM25_INDEX = BM25Okapi(TOKENIZED_CORPUS)
        
        # Persist changes to disk
        faiss.write_index(INDEX, settings.FAISS_INDEX_PATH)
        
        with open(settings.METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(METADATA, f, indent=2)
        
        # Save BM25 data
        bm25_path = settings.METADATA_PATH.replace('.json', '_bm25.json')
        bm25_data = {'tokenized_corpus': TOKENIZED_CORPUS}
        with open(bm25_path, 'w', encoding='utf-8') as f:
            json.dump(bm25_data, f, indent=2)
            
    logger.info(f"Added {len(chunks)} new chunks to hybrid indices. Total vectors: {INDEX.ntotal}")

def get_pdf_path(doc_name: str) -> Optional[str]:
    """
    Returns the file path for a PDF document.
    
    Args:
        doc_name: Name of the PDF document
        
    Returns:
        Full path to the PDF file if it exists, None otherwise
    """
    pdf_path = os.path.join(settings.UPLOAD_DIR, doc_name)
    if os.path.exists(pdf_path):
        return pdf_path
    return None

def search_with_pdf_links(query_text: str, top_k: int) -> List[Dict[str, Any]]:
    """
    Enhanced search function that includes PDF file links in results.
    
    Args:
        query_text: The search query
        top_k: Number of results to return
        
    Returns:
        List of search results with PDF links
    """
    # Perform hybrid search
    results = search_similar_chunks(query_text, top_k * 2)  # Get more results before final filtering
    
    # Add PDF links and enhance results
    enhanced_results = []
    for result in results[:top_k]:  # Limit to requested number
        # Add PDF path information
        pdf_path = get_pdf_path(result['doc_name'])
        result['pdf_available'] = pdf_path is not None
        result['pdf_path'] = pdf_path
        
        # Create a PDF access URL for the frontend
        if pdf_path:
            result['pdf_url'] = f"/api/pdf/{result['doc_name']}"
        else:
            result['pdf_url'] = None
            
        enhanced_results.append(result)
    
    return enhanced_results