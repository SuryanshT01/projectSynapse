# backend/app/api/routes.py - IMPROVED WITH HYBRID SEARCH & PDF LINKS
import os
import shutil
import logging
import asyncio
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
import anyio
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
# Add this line after your imports in routes.py
active_podcast_tasks = {}


# Health check endpoint for Docker
@router.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {
        "status": "healthy",
        "service": "Project Synapse API",
        "version": "1.0.0"
    }

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

# Add this to your existing routes.py file (replace the podcast-related routes)


# Simplified podcast route - add this to your routes.py

@router.post("/podcast")
async def get_podcast(request: InsightsRequest):
    """
    Generate podcast audio - Fixed version with delayed cleanup.
    """
    import uuid
    task_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"Starting podcast generation for task {task_id}")
        
        # Generate podcast audio directly
        audio_file_path = await run_in_threadpool(
            generate_podcast_audio,
            request.query_text,
            request.related_snippets
        )
        
        if not audio_file_path or not os.path.exists(audio_file_path):
            logger.error("Audio file was not created")
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
        
        # Check file size
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"Generated podcast file: {audio_file_path} ({file_size} bytes)")
        
        if file_size < 1000:  # Less than 1KB indicates a problem
            logger.error(f"Generated audio file is too small: {file_size} bytes")
            raise HTTPException(status_code=500, detail="Generated audio file is too small")
        
        # Set up DELAYED background task to clean up the file
        from fastapi import BackgroundTasks
        import asyncio
        background_tasks = BackgroundTasks()
        
        def delayed_cleanup_audio_file():
            """Cleanup audio file after 5 minutes to allow frontend to download/buffer"""
            import time
            import threading
            
            def cleanup_after_delay():
                time.sleep(300)  # Wait 5 minutes (300 seconds)
                try:
                    if os.path.exists(audio_file_path):
                        os.remove(audio_file_path)
                        logger.info(f"Cleaned up audio file after delay: {audio_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup audio file {audio_file_path}: {e}")
            
            # Run cleanup in background thread
            cleanup_thread = threading.Thread(target=cleanup_after_delay, daemon=True)
            cleanup_thread.start()
        
        background_tasks.add_task(delayed_cleanup_audio_file)
        
        # Return the audio file with proper headers
        from fastapi.responses import FileResponse
        return FileResponse(
            path=audio_file_path,
            media_type='audio/mpeg',
            filename=f"podcast_{task_id}.mp3",
            headers={
                "Content-Disposition": f"inline; filename=podcast_{task_id}.mp3",
                "Cache-Control": "no-cache",
                "Accept-Ranges": "bytes"
            },
            background=background_tasks
        )
        
    except Exception as e:
        logger.error(f"Error in /podcast for task {task_id}: {e}", exc_info=True)
        
        # Provide helpful error messages
        error_msg = str(e)
        if "Azure" in error_msg or "TTS" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail=f"Text-to-speech service error: {error_msg}"
            )
        elif "script" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate podcast script. Please try again."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Failed to generate podcast: {error_msg}")
