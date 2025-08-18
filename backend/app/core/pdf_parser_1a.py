# backend/app/core/pdf_parser_1a.py

# --- 1. UNIFIED IMPORTS ---
import io
import json
import logging
import os
import re
import time
from collections import Counter
from functools import partial
from multiprocessing import Pool, cpu_count
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF
import joblib
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- 2. HELPER FUNCTIONS ---

def normalize_text(text: str) -> str:
    """Cleans text by handling ligatures and normalizing whitespace."""
    text = text.replace('\ufb00', 'ff').replace('\ufb01', 'fi').replace('\ufb02', 'fl')
    return ' '.join(text.split())

def validate_hierarchy(headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # This function is now more important to assign H1/H2/H3 levels
    if not headings: return []
    
    # Simple logic: Assume first heading is H1, subsequent ones are H2.
    # This can be made more sophisticated later if needed.
    headings[0]['level'] = "H1"
    for i in range(1, len(headings)):
        headings[i]['level'] = "H2" # Default to H2 for sub-headings

    return headings

def clean_heading_text(text: str) -> str:
    """Cleans text specifically for headings."""
    normalized = normalize_text(text)
    normalized = re.sub(r'\s+\d+\s*$', '', normalized)
    normalized = re.sub(r'^\d+(\.\d+)*\s*\.?\s*', '', normalized)
    return normalized.rstrip('.,:')


# --- 3. CORE LOGIC CLASSES (Unchanged) ---
class StructurePredictor:
    def __init__(self, model_path: str, encoder_path: str):
        self.model, self.encoder = None, None
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
        except FileNotFoundError:
            logger.error(f"FATAL: Model or encoder not found at {os.path.abspath(model_path)} / {os.path.abspath(encoder_path)}")
            raise
        except Exception as e:
            logger.error(f"Error loading model/encoder: {e}")
            raise
    def predict(self, feature_vectors: List[Dict[str, Any]]) -> List[str]:
        # This part of the logic is not being used by the new heuristic
        return ['Body_Text'] * len(feature_vectors)


# --- 4. PDF PARSING AND BLOCK EXTRACTION (Unchanged) ---
def extract_text_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Error opening PDF {pdf_path}: {e}")
        return []
    all_blocks = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict").get("blocks", [])
        for block in blocks:
            if block.get('type') == 0 and 'lines' in block:
                raw_text = "".join(span['text'] for line in block['lines'] for span in line['spans']).strip()
                if raw_text:
                    block.update({'page_num': page_num, 'source': 'pymupdf'})
                    all_blocks.append(block)
    doc.close()
    return all_blocks


# --- 5. HEURISTICS AND CLASSIFICATION (NEW & DEFINITIVE) ---

def is_heading(block: Dict[str, Any]) -> bool:
    """
    Determines if a block is a heading based on boldness and text properties.
    This logic is tailored to the evidence from the debug logs.
    """
    spans = [s for l in block.get('lines', []) for s in l.get('spans', [])]
    if not spans:
        return False

    # A heading must be bold.
    is_bold = any('bold' in s.get('font', '').lower() for s in spans)
    if not is_bold:
        return False
        
    text = "".join(s['text'] for s in spans)

    # A heading must not be a bullet point.
    if '•' in text:
        return False
        
    normalized_text = normalize_text(text)
    word_count = len(normalized_text.split())

    # A heading should have a reasonable length.
    if not (1 <= word_count < 30):
        return False
    
    # A heading should not end like a sentence.
    if normalized_text.endswith(('.', '?', '!', ',')):
        return False
        
    return True

def associate_content_to_headings(headings: List[Dict[str, Any]], content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Accurately associates content blocks with the correct headings."""
    if not headings: 
        return []

    for i, current_h in enumerate(headings):
        start_page, start_y = current_h['page'], current_h['bbox'][1]
        
        next_h = headings[i + 1] if i + 1 < len(headings) else None
        end_page = next_h['page'] if next_h else float('inf')
        end_y = next_h['bbox'][1] if next_h else float('inf')
        
        content_for_heading = []
        for block in content_blocks:
            b_page, b_y = block['page_num'], block['bbox'][1]
            is_after_start = (b_page > start_page) or (b_page == start_page and b_y > start_y)
            is_before_end = (b_page < end_page) or (b_page == end_page and b_y < end_y)

            if is_after_start and is_before_end:
                block_text = "".join(span['text'] for line in block['lines'] for span in line.get('spans', []))
                if block_text.strip():
                    content_for_heading.append(normalize_text(block_text))
        
        current_h['content'] = "\n".join(content_for_heading)
    return headings


# --- 7. MAIN PUBLIC FUNCTION (REBUILT) ---

def extract_structure_from_pdf(pdf_path: str, model_path: str, encoder_path: str) -> Dict[str, Any]:
    start_time = time.time()
    logger.info(f"Extracting blocks from: {os.path.basename(pdf_path)}")
    all_blocks = extract_text_blocks(pdf_path)
    if not all_blocks:
        return {"title": "", "outline": []}

    # Separate blocks into headings and content based on our new, reliable rule.
    identified_headings, content_blocks = [], []
    for block in all_blocks:
        if is_heading(block):
            block_text = "".join(span['text'] for line in block['lines'] for span in line['spans'])
            identified_headings.append({
                "level": "H0", # Temporary level
                "text": clean_heading_text(block_text),
                "page": block['page_num'], 
                "bbox": block['bbox']
            })
        else:
            content_blocks.append(block)

    # Assign a title
    title = identified_headings[0]['text'] if identified_headings else "Untitled Document"
    
    # Associate content correctly
    headings_with_content = associate_content_to_headings(identified_headings, content_blocks)
    
    # Assign final H1/H2 levels and prepare output
    final_outline = [
        {"level": h['level'], "text": h['text'], "page": h['page'], "content": h['content']} 
        for h in headings_with_content
    ]
    final_outline = validate_hierarchy(final_outline)
    
    logger.info(f"Completed in {time.time() - start_time:.2f}s. Found {len(final_outline)} headings.")
    return {"title": title, "outline": final_outline}

# --- 8. STANDALONE EXECUTION (Unchanged) ---
if __name__ == '__main__':
    pass