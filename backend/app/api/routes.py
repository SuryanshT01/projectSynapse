# backend/app/api/routes.py - IMPROVED WITH HYBRID SEARCH & PDF LINKS
import os
import shutil
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ..core.config import get_settings
from ..core.processing import process_and_index_pdf
from ..core.search import search_with_pdf_links
from ..core.generation import generate_insights, generate_podcast_audio

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query_text: str

class InsightsRequest(BaseModel):
    query_text: str
    related_snippets: List[str]

class RelatedSection(BaseModel):
    doc_name: str
    section_title: str
    page: int
    snippet: str  # The matched chunk text
    # Hybrid search scores
    rrf_score: Optional[float] = None
    faiss_score: Optional[float] = None
    bm25_score: Optional[float] = None
    # Rankings from each method
    dense_rank: Optional[int] = None
    sparse_rank: Optional[int] = None
    # PDF access information
    pdf_available: bool = False
    pdf_url: Optional[str] = None

@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Handles bulk upload of PDFs. Responds immediately and processes in the background.
    Now supports hybrid search indexing with both FAISS and BM25.
    """
    saved_files = []
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add the processing task to the background
        background_tasks.add_task(process_and_index_pdf, pdf_path=file_path, doc_name=file.filename)
        saved_files.append(file.filename)
    
    return {
        "message": f"Processing started in background for {len(saved_files)} documents.", 
        "filenames": saved_files,
        "note": "Documents will be indexed for both semantic (FAISS) and keyword (BM25) search"
    }

@router.post("/related-sections", response_model=List[RelatedSection])
async def get_related_sections(request: QueryRequest):
    """
    IMPROVED: The core 'Connecting the Dots' feature using hybrid search.
    
    Now combines:
    - FAISS for semantic similarity
    - BM25 for keyword matching  
    - Reciprocal Rank Fusion (RRF) for optimal result combination
    - PDF links for direct document access
    """
    try:
        logger.info(f"Processing hybrid search query: '{request.query_text[:50]}...'")
        
        # Perform hybrid search with PDF links
        raw_results = search_with_pdf_links(request.query_text, top_k=settings.TOP_K_SEARCH)
        
        if not raw_results:
            logger.warning(f"No results found for query: '{request.query_text}'")
            return []
        
        # De-duplicate results by section (keeping the highest RRF score)
        unique_sections = {}
        for result in raw_results:
            key = (result['doc_name'], result['section_title'])
            if key not in unique_sections or result.get('rrf_score', 0) > unique_sections[key].get('rrf_score', 0):
                unique_sections[key] = result
        
        # Limit to the top N results and sort by RRF score
        top_sections = sorted(unique_sections.values(), 
                            key=lambda x: x.get('rrf_score', 0), 
                            reverse=True)[:settings.MAX_RESULTS]
        
        # Format results for response
        final_results = []
        for section in top_sections:
            final_results.append(
                RelatedSection(
                    doc_name=section['doc_name'],
                    section_title=section['section_title'],
                    page=section['page'],
                    snippet=section['chunk_text'],
                    # Hybrid search scores
                    rrf_score=section.get('rrf_score'),
                    faiss_score=section.get('faiss_score'),
                    bm25_score=section.get('bm25_score'),
                    # Rankings
                    dense_rank=section.get('dense_rank'),
                    sparse_rank=section.get('sparse_rank'),
                    # PDF access
                    pdf_available=section.get('pdf_available', False),
                    pdf_url=section.get('pdf_url')
                )
            )
        
        logger.info(f"Returning {len(final_results)} results with hybrid search scores")
        return final_results
        
    except Exception as e:
        logger.error(f"Error in /related-sections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/pdf/{filename}")
async def get_pdf(filename: str):
    """
    NEW ENDPOINT: Serves PDF files directly to the frontend.
    Enables users to open and view the original PDF documents.
    """
    try:
        # Validate filename to prevent path traversal attacks
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
            
        # Verify it's a PDF file
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File is not a PDF")
            
        return FileResponse(
            path=file_path,
            media_type='application/pdf',
            filename=filename,
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving PDF {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error serving PDF file")

@router.post("/insights")
async def get_insights(request: InsightsRequest):
    """Powers the 'Insights Bulb' feature with enhanced context from hybrid search."""
    try:
        insights = generate_insights(request.query_text, request.related_snippets)
        return insights
    except Exception as e:
        logger.error(f"Error in /insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/podcast")
async def get_podcast(request: InsightsRequest):
    """Powers 'Podcast Mode' with enhanced context from hybrid search."""
    try:
        audio_file_path = generate_podcast_audio(request.query_text, request.related_snippets)
        
        # Return the file as a streaming response and clean up after
        def cleanup():
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
                
        background_tasks = BackgroundTasks()
        background_tasks.add_task(cleanup)
        
        return FileResponse(
            path=audio_file_path,
            media_type='audio/mpeg',
            filename=os.path.basename(audio_file_path),
            background=background_tasks
        )
    except Exception as e:
        logger.error(f"Error in /podcast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate podcast")

@router.get("/search-stats")
async def get_search_stats():
    """
    NEW ENDPOINT: Provides statistics about the search indices.
    Useful for monitoring and debugging the hybrid search system.
    """
    try:
        from ..core.search import INDEX, BM25_INDEX, METADATA, TOKENIZED_CORPUS
        
        stats = {
            "total_documents": len(METADATA),
            "faiss_index_size": INDEX.ntotal if INDEX else 0,
            "bm25_index_size": len(TOKENIZED_CORPUS) if TOKENIZED_CORPUS else 0,
            "search_methods": []
        }
        
        if INDEX and INDEX.ntotal > 0:
            stats["search_methods"].append("FAISS (Dense/Semantic)")
            
        if BM25_INDEX and TOKENIZED_CORPUS:
            stats["search_methods"].append("BM25 (Sparse/Keyword)")
            
        if len(stats["search_methods"]) >= 2:
            stats["search_methods"].append("RRF (Reciprocal Rank Fusion)")
            stats["hybrid_search_available"] = True
        else:
            stats["hybrid_search_available"] = False
            
        return stats
        
    except Exception as e:
        logger.error(f"Error in /search-stats: {e}", exc_info=True)
        return {
            "error": "Unable to retrieve search statistics",
            "total_documents": 0,
            "hybrid_search_available": False
        }