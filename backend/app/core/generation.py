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
    """Generates a 2-speaker podcast audio file."""
    
    snippets_text = "\n\n".join(f"Snippet {i+1}:\n{s}" for i, s in enumerate(related_snippets))
    
    script_prompt = f"""
You are a scriptwriter for a short, 2-minute educational podcast. Write an engaging, two-speaker script (Host and Expert) that discusses the topic "{query_text}".
Use the information provided in the following snippets to form the basis of the conversation. The dialogue must sound natural and conversational.
Structure the output with each line prefixed by the speaker, like 'Host: [dialogue]' or 'Expert: [dialoge]'.

**Snippets to use:**
{snippets_text}
"""
    
    script = chat_with_llm(script_prompt)
    if not script:
        raise Exception("Failed to generate podcast script from LLM.")

    lines = [line.strip() for line in script.split('\n') if line.strip()]
    audio_segments = []
    
    for line in lines:
        if line.startswith("Host:"):
            text = line.replace("Host:", "").strip()
            voice = "en-US-JennyNeural"
        elif line.startswith("Expert:"):
            text = line.replace("Expert:", "").strip()
            voice = "en-US-GuyNeural"
        else:
            continue
            
        if not text:  # Skip empty lines
            continue
            
        temp_filename = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.mp3")
        try:
            generated_file = generate_audio(text, temp_filename, voice=voice)
            
            if generated_file and os.path.exists(generated_file):
                audio_segments.append(AudioSegment.from_mp3(generated_file))
                os.remove(generated_file)
            else:
                logger.warning(f"Failed to generate audio for text: {text[:50]}...")
        except Exception as e:
            logger.error(f"Error generating audio for text '{text[:50]}...': {e}")
            continue

    if not audio_segments:
        raise Exception("Failed to synthesize any audio segments.")

    final_podcast = sum(audio_segments)
    
    final_filename = os.path.join(TEMP_AUDIO_DIR, f"podcast_{uuid.uuid4()}.mp3")
    final_podcast.export(final_filename, format="mp3")
    
    logger.info(f"Podcast generated successfully: {final_filename}")
    return final_filename


def _generate_podcast_script(query_text: str, related_snippets: List[str]) -> str:
    """
    Generate a conversational podcast script using LLM.
    
    Args:
        query_text (str): The original query
        related_snippets (List[str]): Related content snippets
        
    Returns:
        str: Generated podcast script
    """
    logger.info("Generating podcast script using LLM...")
    
    # Prepare context from related snippets
    context_text = ""
    if related_snippets:
        context_text = "\n\n".join([f"Source {i+1}: {snippet}" for i, snippet in enumerate(related_snippets[:5])])
    
    # Create podcast generation prompt
    prompt = f"""You are an AI assistant tasked with creating an engaging, conversational podcast script based on the provided query and related content sources.

QUERY/TOPIC: "{query_text}"

RELATED CONTENT SOURCES:
{context_text}

Please create a natural, conversational podcast script that:

1. **Introduction** (1-2 sentences): Start with a friendly greeting and introduce the topic
2. **Main Content** (3-4 paragraphs): 
   - Explain the main topic in an engaging, conversational tone
   - Incorporate insights from the related sources naturally
   - Present information as if you're having a friendly conversation with the listener
   - Include interesting details, examples, or connections between ideas
3. **Key Takeaways** (1-2 sentences): Summarize the most important points
4. **Conclusion** (1-2 sentences): Wrap up with encouraging or thought-provoking closing remarks

REQUIREMENTS:
- Write in first person, as if you're speaking directly to the listener
- Use a warm, conversational tone (like you're talking to a friend)
- Keep sentences flowing naturally for speech
- Avoid bullet points, lists, or formal structure
- Total length: 300-600 words (about 2-4 minutes when spoken)
- Make it engaging and easy to listen to

Do not include speaker labels, timestamps, or any formatting. Just provide the natural flowing script text that will be converted to speech.

Script:"""

    try:
        # Use the existing LLM chat function
        script = chat_with_llm(prompt)
        
        if not script:
            raise Exception("LLM returned empty response")
        
        # Clean up the script
        script = script.strip()
        
        # Remove any unwanted formatting that might have slipped through
        script = script.replace("**", "").replace("##", "").replace("* ", "")
        
        # Ensure it's not too short or too long
        if len(script) < 200:
            logger.warning(f"Generated script is quite short ({len(script)} chars)")
        elif len(script) > 4000:
            logger.warning(f"Generated script is quite long ({len(script)} chars), may need chunking")
        
        return script
        
    except Exception as e:
        logger.error(f"Failed to generate podcast script: {e}")
        # Fallback script
        fallback_script = f"""
        Hello there! Today we're exploring an interesting topic about {query_text}.

        {query_text} is a fascinating subject that connects to many different areas of knowledge. 
        From what I've gathered from various sources, there are several key points worth discussing.

        The main thing to understand is how this topic relates to your interests and daily life. 
        It's one of those subjects where the more you learn, the more connections you start to see 
        with other areas you might already know about.

        What makes this particularly interesting is how different perspectives can shed new light 
        on the same information. Each source adds another layer to our understanding.

        The key takeaway here is that knowledge builds upon itself, and exploring topics like this 
        helps us develop a more comprehensive understanding of the world around us.

        Thanks for listening, and I hope this gave you some useful insights to think about!
        """
        
        return fallback_script.strip()

def _ensure_temp_audio_dir() -> str:
    """
    Ensure the temporary audio directory exists.
    
    Returns:
        str: Path to the temporary audio directory
    """
    # Get temp directory from environment or use default
    temp_dir = os.getenv("TEMP_AUDIO_DIR", "./data/temp_audio")
    
    # If relative path, make it relative to the project root
    if not os.path.isabs(temp_dir):
        # Get the project root (assuming this file is in backend/app/core/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        temp_dir = os.path.join(project_root, temp_dir)
    
    # Create directory if it doesn't exist
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    
    return temp_dir

def cleanup_old_audio_files(max_age_hours: int = 24):
    """
    Clean up old temporary audio files.
    
    Args:
        max_age_hours (int): Maximum age of files to keep in hours
    """
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

# Additional utility functions that might be used elsewhere in the project

def test_tts_setup() -> bool:
    """
    Test if TTS is properly configured and working.
    
    Returns:
        bool: True if TTS is working, False otherwise
    """
    try:
        temp_dir = _ensure_temp_audio_dir()
        test_file = os.path.join(temp_dir, "tts_test.mp3")
        
        # Try to generate a simple test audio
        test_text = "This is a test of the text to speech system."
        result = generate_audio(test_text, test_file)
        
        # Check if file was created
        success = os.path.exists(result) and os.path.getsize(result) > 100
        
        # Clean up test file
        if os.path.exists(result):
            os.remove(result)
        
        return success
        
    except Exception as e:
        logger.error(f"TTS test failed: {e}")
        return False

def get_tts_provider_info() -> dict:
    """
    Get information about the current TTS provider configuration.
    
    Returns:
        dict: Information about TTS provider setup
    """
    provider = os.getenv("TTS_PROVIDER", "local").lower()
    
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
            "voice": os.getenv("AZURE_TTS_VOICE", "alloy"),
            "api_version": os.getenv("AZURE_TTS_API_VERSION", "2024-08-01-preview")
        }
    elif provider == "gcp":
        info["configured"] = bool(
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        info["details"] = {
            "voice": os.getenv("GCP_TTS_VOICE", "en-US-Neural2-F"),
            "language": os.getenv("GCP_TTS_LANGUAGE", "en-US")
        }
    elif provider == "local":
        info["configured"] = True  # Assume local is always available
        info["details"] = {
            "voice": os.getenv("ESPEAK_VOICE", "en"),
            "speed": os.getenv("ESPEAK_SPEED", "150")
        }
    
    return info

# Schedule periodic cleanup (this would be called from a background task)
def schedule_audio_cleanup():
    """
    Schedule periodic cleanup of old audio files.
    This should be called from the main application startup.
    """
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                cleanup_old_audio_files()
                # Sleep for 6 hours
                time.sleep(6 * 3600)
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                time.sleep(3600)  # Sleep for 1 hour on error
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Audio cleanup worker started")