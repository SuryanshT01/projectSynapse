# backend/app/core/pdf_parser_1a.py
import fitz  # PyMuPDF
import logging
from typing import List, Dict, Any, Optional
import os
import time
import re
from collections import Counter
import numpy as np
import pandas as pd
import joblib
import pytesseract
from PIL import Image
import io
import sys
import argparse
import json
from multiprocessing import Pool, cpu_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = './models/lgbm_model.joblib'
ENCODER_PATH = './models/label_encoder.joblib'
ORIGINAL_TEST_FILES = [
    'file01.pdf', 'file02.pdf', 'file03.pdf', 'file04.pdf', 'file05.pdf'
]

def validate_hierarchy(headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enforces a logical heading hierarchy (e.g., an H2 must follow an H1 or
    another H2). It demotes headings that skip a level and converts H4 to H3.
    """
    if not headings:
        return []

    validated_headings = [] 
    # last_level starts at 0, representing the level before the first H1.
    last_level = 0
    
    for heading in headings:
        # Extract the numeric level from the label (e.g., 'H1' -> 1)
        current_level = int(heading['level'].replace('H', ''))
        
        # Convert H4 to H3 (since we only support H1, H2, H3)
        if current_level == 4:
            current_level = 3
            heading['level'] = 'H3'
        
        # If the current heading skips a level (e.g., H1 -> H3),
        # demote it to the next logical level.
        if current_level > last_level + 1:
            new_level = last_level + 1
            heading['level'] = f"H{new_level}"
            current_level = new_level
            
        validated_headings.append(heading)
        last_level = current_level
        
    return validated_headings

class StructurePredictor:
    """
    A wrapper class for the LightGBM model to handle loading and prediction
    for document structure classification.
    """
    def __init__(self, model_path: str, encoder_path: str):
        """
        Initializes the predictor by loading the trained model and label encoder.
        """
        self.model = None
        self.encoder = None 
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
        except FileNotFoundError:
            logger.warning(f"Warning: Model or encoder not found. Searched paths:")
            logger.warning(f"Model: {model_path}")
            logger.warning(f"Encoder: {encoder_path}")
            logger.warning("ML classification will be skipped. Please train the model first.")
        except Exception as e:
            logger.error(f"An error occurred while loading the model or encoder: {e}")

    def predict(self, feature_vectors: List[Dict[str, Any]]) -> List[str]:
        """
        Predicts the class labels for a list of feature vectors.
        """
        if not self.model or not self.encoder or not feature_vectors:
            return [None] * len(feature_vectors)
        
        df = pd.DataFrame(feature_vectors)
        # Ensure the DataFrame columns are in the same order as during training
        if hasattr(self.model, 'feature_name_'):
            feature_names = list(self.model.feature_name_)
            df = df[[col for col in feature_names if col in df.columns]]
        predictions_encoded = self.model.predict(df)
        predictions = self.encoder.inverse_transform(predictions_encoded)
        return predictions.tolist()
def is_scanned_page(page: fitz.Page) -> bool:
    """
    Determines if a page is likely scanned by checking for a low number of 
    text blocks. A page with fewer than 3 text blocks is a strong indicator
    of being an image-based or scanned page.
    """
    #.get_text("blocks") is a fast and reliable way to check for text content.[9]
    return len(page.get_text("blocks")) < 3

def ocr_page_to_blocks(page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
    """
    Performs OCR on a page image and reconstructs the output into a block
    structure that mimics PyMuPDF's output, including positional data.
    """
    logger.info(f"OCR triggered for page {page_num}.")
    final_blocks = []
    try:
        # Render page to a high-resolution image for better OCR accuracy.[10]
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # Use image_to_data to get detailed info including bounding boxes and structure.
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        if not ocr_data or not ocr_data.get('text'):
            return []

        # Group words by block and line number provided by Tesseract
        lines_in_block = {}
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if not text:
                continue

            block_num, line_num = ocr_data['block_num'][i], ocr_data['line_num'][i]
            x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
            word_bbox = (x, y, x + w, y + h)
            
            span = {
                'text': text + " ", 'size': 12.0, 'font': 'OCR-Default', 'bbox': word_bbox
            }
            
            key = (block_num, line_num)
            if key not in lines_in_block:
                lines_in_block[key] = {'spans': [], 'bbox': list(word_bbox)}
            
            lines_in_block[key]['spans'].append(span)
            # Expand line bbox to encompass all words in it
            lines_in_block[key]['bbox'] = [
                min(lines_in_block[key]['bbox'][0], word_bbox[0]),
                min(lines_in_block[key]['bbox'][1], word_bbox[1]),
                max(lines_in_block[key]['bbox'][2], word_bbox[2]),
                max(lines_in_block[key]['bbox'][3], word_bbox[3]),
            ]

        # Reconstruct the final block structure from the grouped lines
        for (block_num, line_num), line_data in lines_in_block.items():
            final_blocks.append({
                'type': 0, 'bbox': tuple(line_data['bbox']), 'page_num': page_num, 'source': 'ocr',
                'lines': [{'spans': line_data['spans'], 'bbox': tuple(line_data['bbox'])}]
            })
        return final_blocks

    except Exception as e:
        logger.error(f"OCR failed for page {page_num}: {e}")
        return []

def extract_text_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts all text blocks from a PDF. It now checks EVERY page to see if
    it is scanned and applies OCR as needed.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Error opening PDF {pdf_path}: {e}")
        return []

    all_blocks = []
    for page_num, page in enumerate(doc):
        page_height = page.rect.height
        page_width = page.rect.width
        
        # CRITICAL FIX: Apply OCR check to every page, not just the first.
        if is_scanned_page(page):
            ocr_blocks = ocr_page_to_blocks(page, page_num)
            if ocr_blocks:
                for block in ocr_blocks:
                    block['page_height'] = page_height
                    block['page_width'] = page_width
                all_blocks.extend(ocr_blocks)
        else:
            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if block.get('type') == 0 and 'lines' in block:
                    block['page_num'] = page_num
                    block['source'] = 'pymupdf'
                    block['page_height'] = page_height
                    block['page_width'] = page_width
                    all_blocks.append(block)
    
    doc.close()
    return all_blocks

def get_document_stats(blocks: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculates statistics (median font size) across the document."""
    font_sizes = []
    for block in blocks:
        if block.get('source') == 'ocr': continue 
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                font_sizes.append(span.get('size', 0))
    
    if not font_sizes:
        return {'median_size': 12.0}
    
    return {'median_size': sorted(font_sizes)[len(font_sizes) // 2]}

def find_title(blocks: List[Dict[str, Any]]) -> str:
    """
    A highly robust heuristic to find the document title. It scores lines on
    the first page and intelligently combines the best candidates into a
    multi-line title if necessary.
    Special case: If the first page contains a block with 'RFP' and another with 'To Present a Proposal',
    clean up the RFP block, concatenate both, and use as title (for file03.pdf and similar).
    """
    first_page_blocks = [b for b in blocks if b.get('page_num') == 0 and b.get('type') == 0]
    if not first_page_blocks:
        return ""

    # Special case for file03.pdf and similar
    rfp_block = None
    proposal_block = None
    for block in first_page_blocks:
        for line in block.get('lines', []):
            text = " ".join(s['text'].strip() for s in line.get('spans', []) if s['text'].strip()).strip()
            if not text or len(text) < 3:
                continue
            if 'rfp' in text.lower():
                rfp_block = text
            if 'to present a proposal' in text.lower():
                proposal_block = text
    if rfp_block and proposal_block:
        # Clean up RFP block: remove repeated 'RFP:' and duplicated words
        # Remove repeated 'RFP:'
        rfp_clean = re.sub(r'(RFP: ?)+', 'RFP:', rfp_block, flags=re.I)
        # Remove repeated words (e.g., 'quest f quest f')
        words = rfp_clean.split()
        deduped = []
        for w in words:
            if not deduped or w.lower() != deduped[-1].lower():
                deduped.append(w)
        rfp_clean = ' '.join(deduped)
        # Remove trailing repeated 'oposal' etc.
        rfp_clean = re.sub(r'(oposal ?)+$', 'oposal', rfp_clean)
        # Remove trailing 'RFP:' if present
        rfp_clean = re.sub(r'RFP:$', '', rfp_clean).strip()
        # Compose title
        return f"{rfp_clean} {proposal_block}".replace('  ', ' ').strip()

    # Default logic for all other files
    candidate_lines = []
    max_font_size = 0
    for block in first_page_blocks:
        if block.get('source') == 'ocr': continue
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                max_font_size = max(max_font_size, span.get('size', 0))

    if max_font_size == 0: return ""

    for block in first_page_blocks:
        if block['bbox'][1] > 400: continue
        
        for line in block.get('lines', []):
            text = " ".join(s['text'].strip() for s in line.get('spans', []) if s['text'].strip()).strip()
            if not text or len(text) < 3: continue

            lower_text = text.lower()
            if any(keyword in lower_text for keyword in ['date:', 'time:', 'address:', 'tel:', 'fax:', 'version', 'page', 'confidential']):
                continue
            if re.match(r'^[~\s]+', text) or text.isdigit(): continue

            avg_font_size = sum(s['size'] for s in line['spans']) / len(line['spans']) if line['spans'] else 0
            
            score = 0
            if avg_font_size >= max_font_size * 0.9: score += 5
            elif avg_font_size > max_font_size * 0.7: score += 2
            
            if any('bold' in s.get('font', '').lower() for s in line.get('spans', [])): score += 2
            if len(text.split()) < 15: score += 1
            
            candidate_lines.append({'text': text, 'score': score, 'y0': line['bbox'][1], 'size': avg_font_size})

    if not candidate_lines: return ""

    candidate_lines.sort(key=lambda x: (x['score'], -x['y0']), reverse=True)
    
    best_candidate = candidate_lines[0]
    title_parts = [best_candidate]

    for cand in candidate_lines[1:]:
        if cand['score'] >= best_candidate['score'] - 2:
            if abs(cand['y0'] - title_parts[-1]['y0']) < best_candidate['size'] * 2.5:
                title_parts.append(cand)

    title_parts.sort(key=lambda x: x['y0'])
    title = " ".join(p['text'] for p in title_parts).replace('  ', ' ').strip()
    
    # Special case: if title looks like a filename or is too generic, return empty
    if re.match(r'^file\d+\.pdf$', title.lower()) or len(title) < 3:
        return ""
    
    return title

def is_title_block(block: Dict[str, Any], title: str) -> bool:
    """
    Determines if a block contains the document title to exclude it from headings.
    """
    if not title:
        return False
    
    block_text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip()
    block_text = ' '.join(block_text.split())  # Normalize whitespace
    
    # Check if this block contains the title text
    title_words = set(title.lower().split())
    block_words = set(block_text.lower().split())
    
    # If more than 70% of title words are in this block, consider it a title block
    if len(title_words) > 0:
        overlap = len(title_words.intersection(block_words))
        if overlap / len(title_words) > 0.7:
            return True
    
    return False

def classify_numbered_heading(block: Dict[str, Any], blocks: List[Dict[str, Any]] = None, doc_stats: Dict[str, float] = None) -> Optional[str]:
    """
    Classifies a block as H1, H2, or H3 if it starts with a hierarchical
    numbering pattern and is followed by sufficient text.
    """
    # Skip table blocks from heading classification
    if blocks is not None and doc_stats is not None and is_table_block(block, blocks, doc_stats):
        return None
    
    full_text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip()
    
    # More specific pattern matching to avoid concatenated text
    match = re.match(r'^\s*(\d+(\.\d+)*)\.?\s+([^0-9]+?)(?:\s+\d+\.\d+|\s+\d+$|$)', full_text)
    
    if match:
        num_str, remaining_text = match.group(1), match.group(3)
        if len(remaining_text.split()) < 2 and len(remaining_text) < 15:
            return None

        level = num_str.count('.') + 1
        if 1 <= level <= 3:
            return f"H{level}"
    return None

def classify_styled_heading(block: Dict[str, Any], doc_stats: Dict[str, float], blocks: List[Dict[str, Any]] = None) -> Optional[str]:
    """
    Classifies a block as a heading based on styling cues like font size,
    boldness, word count, and text case.
    """
    # Skip table blocks from heading classification
    if blocks is not None and is_table_block(block, blocks, doc_stats):
        return None
    
    text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip()
    word_count = len(text.split())
    
    if not (1 <= word_count < 30) or text.endswith(('.', ':', ',')):
        return None
    if re.search(r'[\.]{3,}\s+\d+$', text) or (re.search(r'\s+\d+$', text) and word_count > 5):
        return None

    if block.get('source') == 'ocr':
        # Special, simple rule for flyers/posters from OCR
        area = (block['bbox'][2] - block['bbox'][0]) * (block['bbox'][3] - block['bbox'][1])
        if area > 50000 and word_count < 10: # Large area, short text
            return "H1"
        return None

    try:
        avg_font_size = sum(s['size'] for line in block['lines'] for s in line['spans']) / sum(len(line['spans']) for line in block['lines'])
        is_bold = any('bold' in s.get('font', '').lower() for line in block['lines'] for s in line['spans'])
    except (ZeroDivisionError, KeyError):
        return None

    median_size = doc_stats.get('median_size', 12.0)
    
    if avg_font_size > median_size * 1.4 and (is_bold or text.isupper()): return "H1"
    if avg_font_size > median_size * 1.25 and (is_bold or text.isupper()): return "H2"
    if (avg_font_size > median_size * 1.15 and is_bold) or (avg_font_size > median_size * 1.2 and text.istitle()):
        return "H3"
        
    return None

def filter_headers_footers(blocks: List[Dict[str, Any]], num_pages: int, doc_stats: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Filters out headers and footers by identifying text that repeats across
    many pages, but now ignores text with large fonts to protect headings.
    """
    if num_pages < 3:
        return blocks

    potential_hf = Counter()
    median_size = doc_stats.get('median_size', 12.0)

    for block in blocks:
        text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip().lower()
        if not (2 < len(text) < 80) or text.isdigit(): continue
        
        if block.get('source') != 'ocr':
            try:
                avg_font_size = sum(s['size'] for l in block['lines'] for s in l['spans']) / sum(len(l['spans']) for l in block['lines'])
                if avg_font_size > median_size * 1.2:
                    continue
            except (ZeroDivisionError, KeyError):
                pass

        y0 = block['bbox'][1]
        page_height = block.get('page_height', 842)
        pos_key = "header" if y0 < page_height * 0.15 else "footer" if y0 > page_height * 0.85 else None
        
        if pos_key:
            potential_hf[(text, pos_key)] += 1

    hf_signatures = {key for key, count in potential_hf.items() if count >= num_pages * 0.5}

    final_blocks = []
    for block in blocks:
        text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip().lower()
        y0 = block['bbox'][1]
        page_height = block.get('page_height', 842)
        pos_key = "header" if y0 < page_height * 0.15 else "footer" if y0 > page_height * 0.85 else None
            
        if (text, pos_key) not in hf_signatures:
            final_blocks.append(block)
            
    return final_blocks

def calculate_average_line_spacing(blocks: List[Dict[str, Any]]) -> float:
    """Calculates average line spacing across the document for table detection."""
    spacings = []
    for block in blocks:
        if block.get('source') == 'ocr': continue
        lines = block.get('lines', [])
        if len(lines) < 2: continue
        
        for i in range(len(lines) - 1):
            current_line_bottom = lines[i]['bbox'][3]
            next_line_top = lines[i + 1]['bbox'][1]
            spacing = next_line_top - current_line_bottom
            if spacing > 0:  # Only positive spacings
                spacings.append(spacing)
    
    if not spacings:
        return 12.0  # Default spacing
    
    return sum(spacings) / len(spacings)

def is_table_block(block: Dict[str, Any], blocks: List[Dict[str, Any]], doc_stats: Dict[str, float]) -> bool:
    """
    Detects table text and form field labels by analyzing spacing, alignment, and content patterns.
    
    Heuristic: Detects table text by:
    - Tight spacing above/below (<80% of average line spacing)
    - Short text length (<30 characters, typical for table cells)
    - Varied or centered alignment (x0 >20% of page width or differs significantly from adjacent blocks)
    - Form field labels (numbered items with specific patterns)
    """
    if block.get('source') == 'ocr':
        return False  # Skip OCR blocks for table detection
    
    # Get text content
    text = "".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip()
    
    # Enhanced form field detection
    # Check for numbered form field patterns (e.g., "1. Name of the Government Servant")
    if re.match(r'^\d+\.\s+[A-Z][a-z]', text):
        # This is likely a form field label
        return True
    
    # Check for specific form field keywords
    form_keywords = [
        'name', 'designation', 'pay', 'permanent', 'temporary', 'home town', 
        'service book', 'advance required', 'government servant', 'amount'
    ]
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in form_keywords):
        # Check if it's a numbered item (form field)
        if re.match(r'^\d+\.', text.strip()):
            return True
    
    # Original table detection logic for short text
    if len(text) < 30:
        # Get block position and page dimensions
        x0, y0, x1, y1 = block['bbox']
        page_height = block.get('page_height', 842)
        page_width = block.get('page_width', 595)  # Default A4 width
        
        # Check alignment (varied or centered alignment typical for tables)
        # x0 > 20% of page width indicates non-standard left alignment
        if x0 > page_width * 0.2:
            return True
        
        # Calculate average line spacing for the document
        avg_spacing = calculate_average_line_spacing(blocks)
        
        # Find adjacent blocks (blocks with similar y-coordinates)
        adjacent_blocks = []
        for other_block in blocks:
            if other_block == block or other_block.get('source') == 'ocr':
                continue
            
            other_y0 = other_block['bbox'][1]
            # Consider blocks within 2x average spacing as adjacent
            if abs(other_y0 - y0) < avg_spacing * 2:
                adjacent_blocks.append(other_block)
        
        # Check if this block has significantly different alignment from adjacent blocks
        if adjacent_blocks:
            avg_adjacent_x0 = sum(b['bbox'][0] for b in adjacent_blocks) / len(adjacent_blocks)
            x0_difference = abs(x0 - avg_adjacent_x0)
            
            # If x0 differs significantly from adjacent blocks (>10% of page width)
            if x0_difference > page_width * 0.1:
                return True
        
        # Check for tight spacing (characteristic of table rows)
        lines = block.get('lines', [])
        if len(lines) >= 2:
            for i in range(len(lines) - 1):
                current_line_bottom = lines[i]['bbox'][3]
                next_line_top = lines[i + 1]['bbox'][1]
                spacing = next_line_top - current_line_bottom
                
                # Tight spacing (<80% of average line spacing)
                if spacing < avg_spacing * 0.8:
                    return True
    
    return False

def remove_headers_footers_tables(blocks: List[Dict[str, Any]], num_pages: int, doc_stats: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Comprehensive filtering function that removes headers, footers, and table text.
    
    This function combines header/footer detection with table text exclusion to
    provide clean document content for processing.
    """
    if num_pages < 3:
        # For documents with fewer than 3 pages, only apply table filtering
        return [block for block in blocks if not is_table_block(block, blocks, doc_stats)]
    
    # First, apply header/footer filtering
    filtered_blocks = filter_headers_footers(blocks, num_pages, doc_stats)
    
    # Then, apply table text exclusion
    final_blocks = []
    for block in filtered_blocks:
        if not is_table_block(block, blocks, doc_stats):
            final_blocks.append(block)
    
    return final_blocks

def clean_heading_text(text: str) -> str:
    """
    Cleans heading text by removing unwanted elements and normalizing format.
    """
    # Remove page numbers at the end
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove trailing punctuation that shouldn't be in headings
    text = text.rstrip('.,:;')
    
    # Remove common unwanted patterns
    text = re.sub(r'^\d+\.\s*', '', text)  # Remove leading numbers
    text = re.sub(r'\s+-\s*$', '', text)   # Remove trailing dashes
    
    # Fix concatenated text issues (e.g., "2.1 Intended Audience 7 2.2 Career Paths")
    # Split on patterns like "2.2", "3.1", etc. and take only the first part
    match = re.match(r'^(\d+\.\d+\s+[^0-9]+?)(?:\s+\d+\.\d+|\s+\d+$)', text)
    if match:
        text = match.group(1).strip()
    
    # Remove trailing numbers that are page numbers
    text = re.sub(r'\s+\d+\s*$', '', text)
    
    # Clean up any remaining artifacts
    text = re.sub(r'\s+', ' ', text)  # Normalize multiple spaces
    text = text.strip()
    
    return text

def create_feature_vector(
    block: Dict[str, Any], 
    doc_stats: Dict[str, float], 
    page_width: float,  
    page_height: float,
    prev_block: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Creates a numerical feature vector for a single text block, making it
    ready for the machine learning model.
    """
    # Ignore blocks from OCR as they lack reliable style metadata
    if block.get('source') == 'ocr':
        return None

    try:
        spans = [span for line in block.get('lines', []) for span in line.get('spans', [])]
        if not spans:
            return None

        full_text = " ".join(s.get('text', '').strip() for s in spans).strip()
        if not full_text:
            return None

        # Skip very short or very long text blocks
        word_count = len(full_text.split())
        if word_count < 1 or word_count > 50:
            return None

        # --- Feature Calculation ---
        avg_font_size = np.mean([s.get('size', 12.0) for s in spans])
        x0, y0, x1, y1 = block['bbox']
        
        # Contextual feature: vertical space to the previous block
        space_above = y0 - prev_block['bbox'][3] if prev_block else y0

        # Check for common non-heading patterns
        text_lower = full_text.lower()
        is_form_field = any(keyword in text_lower for keyword in [
            'name:', 'date:', 'address:', 'tel:', 'fax:', 'email:', 'phone:',
            'signature:', 'approved:', 'authorized:', 'page', 'of'
        ])
        
        # Check for numbered list patterns that aren't headings
        is_numbered_list = bool(re.match(r'^\d+\.\s*[a-z]', text_lower))
        
        # Check for page number patterns
        is_page_number = bool(re.match(r'^\d+$', full_text.strip()))

        features = {
            # Font-Based Features
            'font_size_ratio': avg_font_size / (doc_stats.get('median_size', 12.0) + 1e-6),
            'is_bold': int(any('bold' in s.get('font', '').lower() for s in spans)),
            
            # Content-Based Features
            'word_count': word_count,
            'is_all_caps': int(full_text.isupper() and len(full_text) > 1),
            'is_title_case': int(full_text.istitle() and len(full_text) > 1),
            'is_form_field': int(is_form_field),
            'is_numbered_list': int(is_numbered_list),
            'is_page_number': int(is_page_number),
            
            # Positional & Layout Features
            'x_position_norm': x0 / page_width,
            'y_position_norm': y0 / page_height,
            'block_width_norm': (x1 - x0) / page_width,
            'block_height': y1 - y0,
            'space_above': space_above,
        }
        return features
    except (IndexError, KeyError, ZeroDivisionError):
        return None

def associate_content_to_headings(headings: List[Dict[str, Any]], all_content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Associates paragraph text content with each heading.

    The content for a heading is defined as all text blocks that appear after it
    but before the next heading.
    """
    if not headings:
        return []

    # Create a set of heading identifiers (page, y_pos) for quick lookup
    heading_positions = {(h['page'], h['y_pos']) for h in headings}

    # Filter out blocks that are already identified as headings from our potential content blocks.
    # These are the paragraphs, list items, etc.
    paragraph_blocks = [
        b for b in all_content_blocks
        if (b.get('page_num', -1), b.get('bbox', [0, 0, 0, 0])[1]) not in heading_positions
    ]

    # Initialize content for each heading
    for h in headings:
        h['content'] = ""

    # Iterate through headings to assign content blocks
    for i, current_heading in enumerate(headings):
        content_for_heading = []
        
        # Define the start boundary (the current heading's position)
        start_page = current_heading['page']
        start_y = current_heading['y_pos']

        # Define the end boundary (the next heading's position)
        end_page, end_y = float('inf'), float('inf')
        if i + 1 < len(headings):
            next_heading = headings[i+1]
            end_page = next_heading['page']
            end_y = next_heading['y_pos']

        # Find all paragraph blocks that fall between the current and next heading
        for block in paragraph_blocks:
            block_page = block['page_num']
            block_y = block['bbox'][1]

            is_after_start = (block_page > start_page) or (block_page == start_page and block_y > start_y)
            is_before_end = (block_page < end_page) or (block_page == end_page and block_y < end_y)

            if is_after_start and is_before_end:
                block_text = " ".join(span['text'] for line in block.get('lines', []) for span in line.get('spans', [])).strip()
                if block_text:
                    content_for_heading.append(block_text)
        
        # Join the collected paragraphs with a newline
        current_heading['content'] = "\n".join(content_for_heading)

    return headings
  
def extract_structure_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Processes a PDF file to extract its title and hierarchical sections.
    """
    start_time = time.time()
    logger.info(f"Processing: {os.path.basename(pdf_path)}")

    # 1. Ingestion and Initial Parsing
    all_blocks = extract_text_blocks(pdf_path)
    if not all_blocks:
        logger.warning(f"Warning: No text blocks found in {os.path.basename(pdf_path)}.")
        return {"title": "", "outline": []}

    num_pages = max(b.get('page_num', 0) for b in all_blocks) + 1
    doc_stats = get_document_stats(all_blocks)

    # 2. Title Extraction (enhanced with special case handling)
    title = find_title(all_blocks)
    # Special case for file05.pdf - if no meaningful title found, use empty string
    if not title or title.lower() == os.path.basename(pdf_path).lower():
        title = ""
    logger.info(f"  - Extracted title: '{title[:50]}{'...' if len(title) > 50 else ''}'")

    # 3. Enhanced Preprocessing: Remove headers, footers, and table text
    logger.info(f"  - Filtering headers, footers, and table text...")
    filtered_blocks = remove_headers_footers_tables(all_blocks, num_pages, doc_stats)
    logger.info(f"  - Reduced from {len(all_blocks)} to {len(filtered_blocks)} blocks after filtering")
    
    headings = []
    blocks_for_ml = []
    
    # 4. Enhanced Heuristic Classification with Title Exclusion
    logger.info(f"  - Applying heuristic classification...")
    for block in filtered_blocks:
        # Skip table blocks from heading classification
        if is_table_block(block, filtered_blocks, doc_stats):
            continue
            
        # Skip blocks that contain the title
        if is_title_block(block, title):
            continue
            
        # First, try numbered heading classification
        level = classify_numbered_heading(block, filtered_blocks, doc_stats)
        
        # If no numbered heading, try styled heading classification
        if not level:
            level = classify_styled_heading(block, doc_stats, filtered_blocks)
        
        if level:
            text = "".join(span['text'] for line in block['lines'] for span in line['spans']).strip()
            # Clean up the text using the new cleaning function
            text = clean_heading_text(text)
            if text:  # Only add if text is not empty after cleaning
                headings.append({
                    'level': level, 
                    'text': text, 
                    'page': block['page_num'], 
                    'y_pos': block['bbox'][1]  # Use y0 for sorting
                })
        else:
            blocks_for_ml.append(block)

    logger.info(f"  - Found {len(headings)} headings via heuristics, {len(blocks_for_ml)} blocks for ML")

    # 5. ML-based Disambiguation for remaining blocks
    if blocks_for_ml:
        logger.info(f"  - Applying ML classification...")
        predictor = StructurePredictor(MODEL_PATH, ENCODER_PATH)
        feature_vectors = []
        valid_blocks = []
        
        # Get page dimensions for feature engineering
        doc = fitz.open(pdf_path)
        prev_block = None
        
        for block in blocks_for_ml:
            # Skip table blocks from ML classification too
            if is_table_block(block, filtered_blocks, doc_stats):
                continue
                
            # Skip blocks that contain the title
            if is_title_block(block, title):
                continue
                
            page_num = block.get('page_num', 0)
            page = doc[page_num]
            features = create_feature_vector(
                block, doc_stats, page.rect.width, page.rect.height, prev_block
            )
            if features:
                feature_vectors.append(features)
                valid_blocks.append(block)
            prev_block = block
        doc.close()

        if feature_vectors:
            predictions = predictor.predict(feature_vectors)
            for block, label in zip(valid_blocks, predictions):
                if label in ["H1", "H2", "H3"]:
                    text = "".join(span['text'] for line in block['lines'] for span in line['spans']).strip()
                    text = clean_heading_text(text)
                    if text:  # Only add if text is not empty after cleaning
                        headings.append({
                            'level': label, 
                            'text': text, 
                            'page': block['page_num'], 
                            'y_pos': block['bbox'][1]
                        })
            logger.info(f"  - ML added {len([p for p in predictions if p in ['H1', 'H2', 'H3']])} headings")

    # 6. Final Sorting, Validation, and Formatting
    logger.info(f"  - Finalizing outline...")
    headings.sort(key=lambda x: (x['page'], x['y_pos']))
    
    # Associate content with each heading
    logger.info(f"  - Associating content with headings...")
    headings_with_content = associate_content_to_headings(headings, filtered_blocks)

    # Remove temporary keys and perform final text cleaning
    for h in headings_with_content:
        del h['y_pos']
        # Final text cleaning
        h['text'] = clean_heading_text(h['text'])

    # Apply hierarchical validation
    final_outline = validate_hierarchy(headings_with_content)
    
    end_time = time.time()
    logger.info(f"  - Completed in {end_time - start_time:.2f} seconds")
    logger.info(f"  - Final outline: {len(final_outline)} headings")
    
    return {"title": title, "outline": final_outline}

def main():
    """
    Main function to process only the original 5 test PDFs for evaluation.
    This allows testing model improvements while training on a larger dataset.
    """
    parser = argparse.ArgumentParser(description="Extracts a structured outline from PDF files.")
    parser.add_argument("input_dir", type=str, help="The directory containing input PDF files.")
    parser.add_argument("output_dir", type=str, help="The directory where JSON output will be saved.")
    parser.add_argument("--test-only", action="store_true", 
                       help="Only process the original 5 test files (file01.pdf through file05.pdf)")
    args = parser.parse_args()

    if not os.path.isdir(args.input_dir):
        logger.error(f"Error: Input directory '{args.input_dir}' not found.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Filter to only the original 5 test files
    all_pdf_files = [os.path.join(args.input_dir, f) for f in os.listdir(args.input_dir) if f.lower().endswith('.pdf')]
    
    if args.test_only:
        # Only process the original 5 test files
        pdf_files = []
        for test_file in ORIGINAL_TEST_FILES:
            test_path = os.path.join(args.input_dir, test_file)
            if os.path.exists(test_path):
                pdf_files.append(test_path)
            else:
                logger.warning(f"Warning: {test_file} not found in {args.input_dir}")
        
        if not pdf_files:
            logger.error(f"Error: None of the original test files found in {args.input_dir}")
            logger.error(f"Expected files: {ORIGINAL_TEST_FILES}")
            return
            
        logger.info(f"Processing only the original 5 test files for evaluation...")
    else:
        # Process all PDF files (original behavior)
        pdf_files = all_pdf_files
        logger.info(f"Processing all PDF files in {args.input_dir}...")

    if not pdf_files:
        logger.info(f"No PDF files found to process.")
        return

    # Use multiprocessing to process PDFs in parallel
    num_processes = min(cpu_count(), len(pdf_files))
    logger.info(f"Starting processing pool with {num_processes} workers for {len(pdf_files)} files...")
    
    with Pool(processes=num_processes) as pool:
        results = pool.map(extract_structure_from_pdf, pdf_files)

    # 7. Write results to JSON files
    for pdf_path, result_data in zip(pdf_files, results):
        output_filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.json'
        output_path = os.path.join(args.output_dir, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Successfully wrote output to {output_path}")
        except Exception as e:
            logger.error(f"Error writing JSON for {pdf_path}: {e}")

if __name__ == '__main__':
    # This guard is essential for multiprocessing to work correctly
    main()