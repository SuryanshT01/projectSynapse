# backend/app/core/generation.py

import logging
import os
import uuid
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
You are a world-class research assistant. Your task is to analyze a user's selected text and several related text snippets from their document library and provide deep insights.

**User's Selected Text:**
"{query_text}"

**Related Snippets from Documents:**
{snippets_text}

---

Based **ONLY** on the information provided above, please generate the following insights. If an insight cannot be derived from the text, state that clearly. Structure your response in a clear, well-formatted way.

1.  **Contradictions / Counterpoints:** Identify any direct contradictions or opposing viewpoints between the user's text and the snippets. Quote the relevant parts.
2.  **Key Takeaways:** Synthesize the main ideas into 3-4 important, concise takeaways.
3.  **Illustrative Examples:** Find the best concrete example or case study that illustrates the main concept.
"""
    
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
            
        temp_filename = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.mp3")
        success = generate_audio(text, temp_filename, voice_name=voice)
        
        if success:
            audio_segments.append(AudioSegment.from_mp3(temp_filename))
            os.remove(temp_filename)

    if not audio_segments:
        raise Exception("Failed to synthesize any audio segments.")

    final_podcast = sum(audio_segments)
    
    final_filename = os.path.join(TEMP_AUDIO_DIR, f"podcast_{uuid.uuid4()}.mp3")
    final_podcast.export(final_filename, format="mp3")
    
    logger.info(f"Podcast generated successfully: {final_filename}")
    return final_filename