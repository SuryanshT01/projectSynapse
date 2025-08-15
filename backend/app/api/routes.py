# backend/app/api/routes.py
import os
import shutil
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.processing import process_and_index_pdf
from ..core.search import search_similar_chunks
from ..core.generation import generate_insights, generate_podcast_audio

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

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
    snippet: str # The LLM-generated, high-relevance snippet

@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Handles bulk upload of 'past' PDFs. Responds immediately and processes in the background.
    """
    saved_files = []
    for file in files:
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add the processing task to the background
        background_tasks.add_task(process_and_index_pdf, pdf_path=file_path, doc_name=file.filename)
        saved_files.append(file.filename)

    return {"message": f"Processing started in background for {len(saved_files)} documents.", "filenames": saved_files}

@router.post("/related-sections", response_model=List[RelatedSection])
async def get_related_sections(request: QueryRequest):
    """
    The core 'Connecting the Dots' feature.
    Finds relevant sections and generates high-quality snippets.
    """
    try:
        # 1. Perform initial semantic search
        raw_results = search_similar_chunks(request.query_text, top_k=settings.TOP_K_SEARCH)
        
        # 2. De-duplicate results by section
        unique_sections = {}
        for result in raw_results:
            key = (result['doc_name'], result['section_title'])
            if key not in unique_sections:
                unique_sections[key] = result
        
        # 3. Limit to the top N results
        top_sections = list(unique_sections.values())[:settings.MAX_RESULTS]

        # 4. Generate high-relevance snippets for the top results (placeholder for LLM call)
        # For a hackathon, returning the matched chunk is fast and reliable.
        # The blueprint suggests an LLM call here, which would be a great enhancement.
        # For now, we use the matched chunk as the "snippet".
        
        final_results = []
        for section in top_sections:
            final_results.append(
                RelatedSection(
                    doc_name=section['doc_name'],
                    section_title=section['section_title'],
                    page=section['page'],
                    snippet=section['chunk_text'] # Using matched chunk as snippet
                )
            )

        return final_results
    except Exception as e:
        logger.error(f"Error in /related-sections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/insights")
async def get_insights(request: InsightsRequest):
    """Powers the 'Insights Bulb' feature."""
    try:
        insights = generate_insights(request.query_text, request.related_snippets)
        return insights
    except Exception as e:
        logger.error(f"Error in /insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/podcast")
async def get_podcast(request: InsightsRequest):
    """Powers 'Podcast Mode' and returns an MP3 file."""
    try:
        audio_file_path = generate_podcast_audio(request.query_text, request.related_snippets)
        
        # Return the file as a streaming response and clean up after
        def cleanup():
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