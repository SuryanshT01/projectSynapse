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

# Store active podcast generation tasks for cancellation
active_podcast_tasks = {}

async def _check_client_disconnected(request: Request) -> bool:
    """
    Check if the client has disconnected by trying to receive a message.
    Returns True if client is disconnected, False otherwise.
    """
    try:
        message = await request.receive()
        return message.get("type") == "http.disconnect"
    except:
        return False

async def _generate_podcast_with_cancellation(
    request: Request, 
    query_text: str, 
    related_snippets: List[str],
    task_id: str
) -> str:
    """
    Generate podcast audio with client disconnection detection.
    
    Args:
        request: FastAPI request object
        query_text: The query text
        related_snippets: List of related content snippets
        task_id: Unique task identifier
        
    Returns:
        str: Path to the generated audio file
        
    Raises:
        asyncio.CancelledError: If the task is cancelled
        Exception: If generation fails
    """
    logger.info(f"Starting podcast generation task {task_id}")
    
    try:
        # Use asyncio.create_task for better control
        import asyncio
        
        # Task 1: Monitor client connection
        async def monitor_client():
            while True:
                if await _check_client_disconnected(request):
                    logger.info(f"Client disconnected for task {task_id}, cancelling")
                    return "cancelled"
                await asyncio.sleep(0.5)  # Check every 500ms
        
        # Task 2: Generate the actual podcast
        async def generate_podcast():
            try:
                # Run the CPU-intensive podcast generation in a thread pool
                audio_path = await run_in_threadpool(
                    generate_podcast_audio,
                    query_text,
                    related_snippets
                )
                return audio_path
            except Exception as e:
                logger.error(f"Podcast generation failed for task {task_id}: {e}")
                raise
        
        # Create tasks
        monitor_task = asyncio.create_task(monitor_client())
        generation_task = asyncio.create_task(generate_podcast())
        
        try:
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [monitor_task, generation_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Check results
            for task in done:
                if task == generation_task:
                    audio_path = task.result()
                    logger.info(f"Podcast generation completed successfully for task {task_id}")
                    return audio_path
                elif task == monitor_task:
                    result = task.result()
                    if result == "cancelled":
                        logger.info(f"Client disconnected for task {task_id}")
                        raise asyncio.CancelledError(f"Task {task_id} was cancelled due to client disconnect")
            
            # If we get here, something unexpected happened
            raise Exception("Unexpected task completion state")
            
        except asyncio.CancelledError:
            logger.info(f"Podcast generation was cancelled for task {task_id}")
            raise
                
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Podcast generation error for task {task_id}: {e}")
        raise
    finally:
        # Clean up the task from active tasks
        active_podcast_tasks.pop(task_id, None)

@router.post("/podcast")
async def get_podcast(request: InsightsRequest, fastapi_request: Request):
    """
    Generate podcast audio with enhanced context from hybrid search.
    Supports client disconnection detection and request cancellation.
    """
    import uuid
    task_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"Starting podcast generation for task {task_id}")
        
        # Store the task for potential cancellation
        active_podcast_tasks[task_id] = {"status": "running", "query": request.query_text[:50]}
        
        # Generate podcast with cancellation support
        audio_file_path = await _generate_podcast_with_cancellation(
            fastapi_request,
            request.query_text,
            request.related_snippets,
            task_id
        )
        
        if not audio_file_path or not os.path.exists(audio_file_path):
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
        
        # Set up background task to clean up the file after sending
        background_tasks = BackgroundTasks()
        
        def cleanup_audio_file():
            try:
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                    logger.info(f"Cleaned up audio file: {audio_file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup audio file {audio_file_path}: {e}")
        
        background_tasks.add_task(cleanup_audio_file)
        
        # Return the audio file
        return FileResponse(
            path=audio_file_path,
            media_type='audio/mpeg',
            filename=f"podcast_{task_id}.mp3",
            background=background_tasks
        )
        
    except asyncio.CancelledError:
        logger.info(f"Podcast generation cancelled for task {task_id}")
        raise HTTPException(status_code=499, detail="Request cancelled by client")
        
    except Exception as e:
        logger.error(f"Error in /podcast for task {task_id}: {e}", exc_info=True)
        active_podcast_tasks.pop(task_id, None)
        
        # Provide more specific error messages
        if "TTS" in str(e):
            raise HTTPException(
                status_code=503, 
                detail="Text-to-speech service is currently unavailable. Please check TTS configuration."
            )
        elif "script" in str(e).lower():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate podcast script. Please try again."
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate podcast")

@router.get("/podcast/status/{task_id}")
async def get_podcast_status(task_id: str):
    """
    Get the status of a podcast generation task.
    
    Args:
        task_id: The task identifier
        
    Returns:
        dict: Task status information
    """
    if task_id in active_podcast_tasks:
        return {
            "task_id": task_id,
            "status": active_podcast_tasks[task_id]["status"],
            "query": active_podcast_tasks[task_id]["query"]
        }
    else:
        return {
            "task_id": task_id,
            "status": "completed_or_not_found"
        }

@router.delete("/podcast/{task_id}")
async def cancel_podcast(task_id: str):
    """
    Cancel a running podcast generation task.
    
    Args:
        task_id: The task identifier to cancel
        
    Returns:
        dict: Cancellation status
    """
    if task_id in active_podcast_tasks:
        active_podcast_tasks[task_id]["status"] = "cancelled"
        logger.info(f"Marked task {task_id} for cancellation")
        return {"message": f"Task {task_id} marked for cancellation", "status": "success"}
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@router.get("/podcast/health")
async def podcast_health_check():
    """
    Health check endpoint for podcast generation service.
    
    Returns:
        dict: Health status and configuration info
    """
    from app.core.generation import test_tts_setup, get_tts_provider_info
    
    try:
        # Test TTS setup
        tts_working = await run_in_threadpool(test_tts_setup)
        tts_info = get_tts_provider_info()
        
        active_tasks_count = len(active_podcast_tasks)
        
        return {
            "status": "healthy" if tts_working else "degraded",
            "tts_working": tts_working,
            "tts_provider": tts_info,
            "active_tasks": active_tasks_count,
            "message": "Podcast service is operational" if tts_working else "TTS configuration issues detected"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Podcast service is experiencing issues"
        }

# Additional utility endpoints

@router.get("/podcast/active-tasks")
async def get_active_podcast_tasks():
    """
    Get information about currently active podcast generation tasks.
    Useful for monitoring and debugging.
    
    Returns:
        dict: Information about active tasks
    """
    return {
        "active_tasks": active_podcast_tasks,
        "total_count": len(active_podcast_tasks)
    }

@router.post("/podcast/cleanup")
async def cleanup_old_audio_files():
    """
    Manually trigger cleanup of old audio files.
    
    Returns:
        dict: Cleanup results
    """
    try:
        from app.core.generation import cleanup_old_audio_files
        
        await run_in_threadpool(cleanup_old_audio_files, max_age_hours=1)
        
        return {
            "status": "success",
            "message": "Audio file cleanup completed"
        }
        
    except Exception as e:
        logger.error(f"Manual cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")

# Startup event to initialize cleanup worker
from contextlib import asynccontextmanager

@asynccontextmanager
async def podcast_lifespan(app):
    """
    Lifespan context manager for podcast-related services.
    """
    logger.info("Starting podcast services...")
    
    # Start background cleanup worker
    from app.core.generation import schedule_audio_cleanup
    try:
        await run_in_threadpool(schedule_audio_cleanup)
        logger.info("Audio cleanup worker started")
    except Exception as e:
        logger.warning(f"Failed to start cleanup worker: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down podcast services...")
    
    # Cancel any active tasks
    for task_id in list(active_podcast_tasks.keys()):
        active_podcast_tasks[task_id]["status"] = "cancelled"
    
    active_podcast_tasks.clear()
    logger.info("Podcast services shutdown complete")

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