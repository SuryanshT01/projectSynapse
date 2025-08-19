# backend/app/core/generation.py

import logging
import os
import uuid
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from pydub import AudioSegment

# Corrected import path assuming 'scripts' is a sibling to 'core' under 'app'
from ..scripts.chat_with_llm import chat_with_llm
from ..scripts.generate_audio import generate_audio
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Define paths for temporary audio files
TEMP_AUDIO_DIR = "backend/data/temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


def generate_insights(query_text: str, related_snippets: List[str]) -> Dict[str, Any]:
    """Generates various insights using an LLM based on a query and related text."""
    
    # Safety check: If there are no related snippets, we can't generate good insights.
    if not related_snippets:
        logger.warning("generate_insights called with no related snippets.")
        return {"insights_text": "Not enough related content was found to generate insights."}

    snippets_text = "\n\n".join(f"Snippet {i+1}:\n{s}" for i, s in enumerate(related_snippets))
    
    prompt = f"""
You are an expert document analyst with expertise across all domains. Generate actionable insights from the user's selected text and related content from different documents along with their context. Focus on what's most valuable for someone working with this specific information.

**SELECTED TEXT:** {query_text}

**RELATED CONTENT:**
{snippets_text}

---

Provide insights in this exact format:

## 🎯 **QUICK INSIGHTS**
• [Key Insights Short, crisp and consize answer to the selected text, using all the information along with your own knowledge.]

### ⚡ **Key Points**
• [Most important finding from the content]
• [Critical detail that stands out from the selected text and the content from different documents]
• [Unexpected or noteworthy information]

### ⚠️ **Critical Notes**
• [Any contradictions, gaps, or limitations in the information from the selected text and the information in the related content.]
• [What questions remain unanswered]
• [Potential risks or considerations]

### 💡 **Actionable Takeaways**
• [Specific action someone could take based on this information]
• [What to research further or investigate]
• [How to apply or use this knowledge]

### � **Connections**
• [How this relates to other parts of the document]
• [Cross-references or related concepts mentioned]
• [Broader implications or applications]

---
**Analysis based on:** {len(related_snippets)} related sections from the document"""
    
    logger.info(f"Generating insights for query: '{query_text[:50]}...'")
    response_text = chat_with_llm(prompt)
    
    # Add a safety check to handle cases where the LLM might return an empty response
    if not response_text or not response_text.strip():
        logger.error("LLM returned an empty or null response for insights.")
        raise RuntimeError("Failed to get a valid response from the language model.")

    logger.info("Successfully generated insights from LLM.")
    return {"insights_text": response_text}


def generate_podcast_audio(query_text: str, related_snippets: List[str]) -> str:
    """
    Generate a single-narrator podcast audio file.
    Simplified version for reliable hackathon demo.
    
    Args:
        query_text (str): The original query text
        related_snippets (List[str]): List of related content snippets
        
    Returns:
        str: Path to the generated audio file
        
    Raises:
        Exception: If podcast generation fails
    """
    logger.info(f"Starting podcast generation for query: '{query_text[:50]}...'")
    
    try:
        # Step 1: Generate a conversational script
        script = _generate_podcast_script(query_text, related_snippets)
        
        if not script:
            raise Exception("Failed to generate podcast script from LLM.")
        
        logger.info(f"Generated script ({len(script)} chars)")
        
        # Step 2: Create output directory
        temp_dir = _ensure_temp_audio_dir()
        final_filename = os.path.join(temp_dir, f"podcast_{uuid.uuid4()}.mp3")
        
        # Step 3: Generate audio with a pleasant voice
        voice = "nova"  # Female voice, good for narration
        
        logger.info(f"Generating audio with voice: {voice}")
        
        # Generate the audio file
        generated_file = generate_audio(script, final_filename, voice=voice)
        
        if not generated_file or not os.path.exists(generated_file):
            raise Exception("Failed to generate audio file")
        
        # Check file size
        file_size = os.path.getsize(generated_file)
        if file_size < 1000:  # Less than 1KB indicates a problem
            raise Exception(f"Generated audio file is too small ({file_size} bytes)")
        
        logger.info(f"Podcast generated successfully: {generated_file} ({file_size} bytes)")
        return generated_file
        
    except Exception as e:
        logger.error(f"Podcast generation failed: {e}", exc_info=True)
        raise Exception(f"Podcast generation failed: {str(e)}")

def _generate_podcast_script(query_text: str, related_snippets: List[str]) -> str:
    """Generate a conversational podcast script using LLM."""
    logger.info("Generating podcast script using LLM...")
    
    # Prepare context from related snippets
    context_text = ""
    if related_snippets:
        context_text = "\n\n".join([f"Source {i+1}: {snippet}" for i, snippet in enumerate(related_snippets[:5])])
    
    # Create podcast generation prompt
    prompt = f"""Create an engaging, conversational podcast script about "{query_text}".

CONTEXT FROM DOCUMENTS:
{context_text}

INSTRUCTIONS:
Write a natural, friendly podcast script as if you're explaining this topic to a friend. The script should:

1. Start with a warm greeting and introduce the topic
2. Explain the main concept in simple, engaging terms  
3. Include interesting details and examples from the context
4. Make connections between different ideas
5. End with key takeaways and a friendly closing

STYLE GUIDELINES:
- Write in first person ("I want to talk to you about...")
- Use conversational language, not formal academic tone
- Include natural transitions ("So here's what's interesting...")
- Keep it engaging and easy to follow
- Target length: 2-3 minutes when spoken (about 300-500 words)
- No special formatting, just natural flowing text

Script:"""

    try:
        script = chat_with_llm(prompt)
        
        if not script:
            raise Exception("LLM returned empty response")
        
        # Clean up the script
        script = script.strip()
        script = script.replace("**", "").replace("##", "").replace("* ", "")
        
        # Ensure reasonable length
        if len(script) < 100:
            logger.warning(f"Generated script is very short ({len(script)} chars)")
            script = _get_fallback_script(query_text)
        elif len(script) > 2000:
            logger.warning(f"Generated script is quite long ({len(script)} chars), truncating")
            # Truncate but try to end at a sentence
            truncated = script[:1800]
            last_period = truncated.rfind('.')
            if last_period > 1500:
                script = truncated[:last_period + 1]
            else:
                script = truncated
        
        logger.info(f"Final script length: {len(script)} characters")
        return script
        
    except Exception as e:
        logger.error(f"Failed to generate podcast script: {e}")
        return _get_fallback_script(query_text)

def _get_fallback_script(query_text: str) -> str:
    """Get a fallback script when LLM generation fails."""
    return f"""
Hello there! Today I want to talk to you about {query_text}.

This is actually a really interesting topic that has many practical applications. 
From the research I've gathered, it's clear that understanding {query_text} can 
provide valuable insights for both professionals and everyday problem-solving.

What makes this topic particularly fascinating is how it connects to broader themes 
and concepts that we encounter in various contexts. The key is to approach it with 
curiosity and an open mind.

There are several important aspects to consider when thinking about {query_text}. 
Each perspective adds another layer to our understanding and helps us see the bigger picture.

I hope this overview has been helpful and gives you a starting point for further 
exploration. Thanks for listening, and remember to keep learning!
""".strip()

def _ensure_temp_audio_dir() -> str:
    """Ensure the temporary audio directory exists."""
    temp_dir = os.getenv("TEMP_AUDIO_DIR", "./data/temp_audio")
    
    if not os.path.isabs(temp_dir):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        temp_dir = os.path.join(project_root, temp_dir)
    
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return temp_dir

def cleanup_old_audio_files(max_age_hours: int = 24):
    """Clean up old temporary audio files."""
    try:
        temp_dir = _ensure_temp_audio_dir()
        current_time = os.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        for file_path in Path(temp_dir).glob("podcast_*.mp3"):
            try:
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Failed to clean up file {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old audio files")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old audio files: {e}")

def test_tts_setup() -> bool:
    """Test if TTS is properly configured and working."""
    try:
        temp_dir = _ensure_temp_audio_dir()
        test_file = os.path.join(temp_dir, "tts_test.mp3")
        
        test_text = "This is a test of the text to speech system."
        result = generate_audio(test_text, test_file)
        
        success = os.path.exists(result) and os.path.getsize(result) > 100
        
        if os.path.exists(result):
            os.remove(result)
        
        return success
        
    except Exception as e:
        logger.error(f"TTS test failed: {e}")
        return False

def get_tts_provider_info() -> dict:
    """Get information about the current TTS provider configuration."""
    provider = os.getenv("TTS_PROVIDER", "azure").lower()
    
    info = {
        "provider": provider,
        "configured": False,
        "details": {}
    }
    
    if provider == "azure":
        info["configured"] = bool(
            os.getenv("AZURE_TTS_KEY") and 
            os.getenv("AZURE_TTS_ENDPOINT")
        )
        info["details"] = {
            "endpoint": os.getenv("AZURE_TTS_ENDPOINT", "Not set"),
            "deployment": os.getenv("AZURE_TTS_DEPLOYMENT", "tts"),
            "voice": os.getenv("AZURE_TTS_VOICE", "nova"),
            "api_version": os.getenv("AZURE_TTS_API_VERSION", "2024-08-01-preview")
        }
    
    return info
