# backend/app/core/processing.py

# --- FIX: ADD THESE IMPORTS AND DEFINITIONS ---
import logging
import uuid
from typing import List

import nltk
from nltk.tokenize import sent_tokenize

# This imports the settings function
from .config import get_settings
# These imports were already here
from .pdf_parser_1a import extract_structure_from_pdf
from .search import add_chunks_to_index

# This creates the logger instance
logger = logging.getLogger(__name__)
# --- END OF FIX ---


# Download the sentence tokenizer model if not already present
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Splits a text into chunks of sentences with overlap."""
    text = " ".join(text.strip().split())
    sentences = sent_tokenize(text)
    chunks = []
    
    start = 0
    while start < len(sentences):
        end = start + chunk_size
        chunks.append(" ".join(sentences[start:end]))
        
        if end >= len(sentences):
            break
        
        step = chunk_size - chunk_overlap
        start += step if step > 0 else 1

    return chunks

def process_and_index_pdf(pdf_path: str, doc_name: str):
    """
    Main pipeline function to process a single PDF and add it to the search index.
    """
    try:
        settings = get_settings()
        logger.info(f"Processing document: {doc_name}")

        doc_structure = extract_structure_from_pdf(
            pdf_path=pdf_path,
            model_path=settings.MODEL_PATH,
            encoder_path=settings.ENCODER_PATH
        )
        
        doc_id = str(uuid.uuid4())
        all_chunks = []
        all_metadatas = []

        document_title = doc_structure.get("title") or doc_name.replace(".pdf", "")

        for section in doc_structure.get("outline", []):
            section_content = section.get("content")
            
            if not section_content or len(section_content.split()) < 5:
                continue
            
            text_chunks = chunk_text(
                section_content, 
                settings.CHUNK_SIZE, 
                settings.CHUNK_OVERLAP
            )
            
            for chunk in text_chunks:
                metadata = {
                    "doc_id": doc_id,
                    "doc_name": doc_name,
                    "document_title": document_title,
                    "section_title": section.get("text", "Untitled Section"),
                    "page": section.get("page", 0),
                    "chunk_text": chunk,
                }
                all_chunks.append(chunk)
                all_metadatas.append(metadata)
        
        if all_chunks:
            add_chunks_to_index(all_chunks, all_metadatas)
            logger.info(f"Successfully indexed {len(all_chunks)} chunks from {doc_name}.")
        else:
            logger.warning(f"No meaningful text chunks were extracted from {doc_name}.")

    except Exception as e:
        logger.error(f"Failed to process {doc_name}: {e}", exc_info=True)