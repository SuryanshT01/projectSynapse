import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_azure_tts():
    endpoint = os.getenv("AZURE_TTS_ENDPOINT")
    api_key = os.getenv("AZURE_TTS_KEY")
    deployment = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")
    
    if not endpoint or not api_key:
        print("❌ Missing Azure TTS configuration")
        return False
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": deployment,
        "input": "Hello, this is a test of Project Synapse TTS functionality.",
        "voice": "alloy"
    }
    
    try:
        response = requests.post(
            f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version=2024-08-01-preview",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        # Save test audio
        with open("test_audio.mp3", "wb") as f:
            f.write(response.content)
        
        print("✅ Azure OpenAI TTS setup successful!")
        print(f"Test audio saved as test_audio.mp3 ({len(response.content)} bytes)")
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI TTS test failed: {e}")
        return False

if __name__ == "__main__":
    test_azure_tts()
