# backend/app/core/processing.py
import logging
import uuid
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize

from .config import get_settings
from .pdf_parser_1a import extract_structure_from_pdf
from .search import add_chunks_to_index

# Download the sentence tokenizer model if not already present
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)
settings = get_settings()

def chunk_text(text: str) -> List[str]:
    """Splits a text into chunks of sentences with overlap."""
    sentences = sent_tokenize(text)
    chunks = []
    
    start = 0
    while start < len(sentences):
        end = start + settings.CHUNK_SIZE
        chunk_sentences = sentences[start:end]
        chunks.append(" ".join(chunk_sentences))
        
        # Move the start pointer for the next chunk
        if end >= len(sentences):
            break
        
        # The step is chunk_size minus overlap
        step = settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
        start += step if step > 0 else 1 # Ensure we always move forward

    return chunks

def process_and_index_pdf(pdf_path: str, doc_name: str):
    """
    Main pipeline function to process a single PDF and add it to the search index.
    1. Extracts structure using Round 1A logic.
    2. Chunks the content of each section.
    3. Creates metadata for each chunk.
    4. Adds the chunks to the FAISS index.
    """
    try:
        logger.info(f"Processing document: {doc_name}")
        doc_structure = extract_structure_from_pdf(pdf_path)
        
        doc_id = str(uuid.uuid4())
        all_chunks = []
        all_metadatas = []

        for section in doc_structure.get("outline", []):
            section_content = section.get("content")
            if not section_content or not isinstance(section_content, str):
                continue
            
            text_chunks = chunk_text(section_content)
            
            for i, chunk in enumerate(text_chunks):
                metadata = {
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "section_title": section.get("text", "Untitled Section"),
                    "page": section.get("page", 0),
                    "chunk_text": chunk,
                }
                all_chunks.append(chunk)
                all_metadatas.append(metadata)
        
        if all_chunks:
            add_chunks_to_index(all_chunks, all_metadatas)
            logger.info(f"Successfully processed and indexed {len(all_chunks)} chunks from {doc_name}.")
        else:
            logger.warning(f"No text chunks were extracted from {doc_name}.")

    except Exception as e:
        logger.error(f"Failed to process {doc_name}: {e}", exc_info=True)