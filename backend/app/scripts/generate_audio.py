
### 2. Fixed `backend/app/scripts/generate_audio.py`

import os
import subprocess
import requests
from pathlib import Path

# Add this at the top to ensure .env is loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip loading
    pass

def generate_audio(text, output_file, provider=None, voice=None):
    """
    Generate audio from text using the specified TTS provider.
    
    Args:
        text (str): Text to convert to speech
        output_file (str): Output file path
        provider (str, optional): TTS provider to use. Defaults to TTS_PROVIDER env var or "local"
        voice (str, optional): Voice to use. Defaults to provider-specific default
    
    Returns:
        str: Path to the generated audio file
    
    Raises:
        RuntimeError: If TTS provider is not available or synthesis fails
        ValueError: If text is empty or invalid
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    provider = provider or os.getenv("TTS_PROVIDER", "local").lower()
    
    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if provider == "azure":
        return _generate_azure_tts(text, output_file, voice)
    elif provider == "gcp":
        return _generate_gcp_tts(text, output_file, voice)
    elif provider == "local":
        return _generate_local_tts(text, output_file, voice)
    else:
        raise ValueError(f"Unsupported TTS_PROVIDER: {provider}")

def _generate_azure_tts(text, output_file, voice=None):
    """Generate audio using Azure OpenAI TTS - FIXED VERSION"""
    api_key = os.getenv("AZURE_TTS_KEY")
    endpoint = os.getenv("AZURE_TTS_ENDPOINT")
    deployment = os.getenv("AZURE_TTS_DEPLOYMENT", "tts")
    voice = voice or os.getenv("AZURE_TTS_VOICE", "alloy")
    api_version = os.getenv("AZURE_TTS_API_VERSION", "2024-08-01-preview")
    
    if not api_key or not endpoint:
        raise ValueError("AZURE_TTS_KEY and AZURE_TTS_ENDPOINT must be set for Azure OpenAI TTS")
    
    # Ensure voice is one of the valid Azure OpenAI TTS voices
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if voice not in valid_voices:
        print(f"Warning: Voice '{voice}' not in valid voices {valid_voices}, using 'alloy'")
        voice = "alloy"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Use the exact format that works in your test
    payload = {
        "model": deployment,
        "input": text,
        "voice": voice
    }
    
    try:
        print(f"Making TTS request with voice: {voice}, deployment: {deployment}")
        
        response = requests.post(
            f"{endpoint}/openai/deployments/{deployment}/audio/speech?api-version={api_version}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Response text: {response.text}")
            
        response.raise_for_status()
        
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        print(f"Azure OpenAI TTS audio saved to: {output_file} ({len(response.content)} bytes)")
        return output_file
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Azure OpenAI TTS failed: {e}")

def _generate_gcp_tts(text, output_file, voice=None):
    """Generate audio using Google Cloud Text-to-Speech."""
    try:
        from google.cloud import texttospeech
    except ImportError:
        raise RuntimeError("google-cloud-texttospeech library not installed. Please install it with: pip install google-cloud-texttospeech")
        
    api_key = os.getenv("GOOGLE_API_KEY")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    gcp_voice = voice or os.getenv("GCP_TTS_VOICE", "en-US-Neural2-F")
    language = os.getenv("GCP_TTS_LANGUAGE", "en-US")
    
    if not api_key and not credentials_path:
        raise ValueError("Either GOOGLE_API_KEY or GOOGLE_APPLICATION_CREDENTIALS must be set for Google Cloud TTS")
    
    try:
        if api_key:
            import requests
            import base64
            
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": language,
                    "name": gcp_voice
                },
                "audioConfig": {
                    "audioEncoding": "MP3"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            audio_content = base64.b64decode(response.json()["audioContent"])
            
            with open(output_file, "wb") as f:
                f.write(audio_content)
                
        else:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            client = texttospeech.TextToSpeechClient()
            
            input_text = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=language,
                name=gcp_voice
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = client.synthesize_speech(
                input=input_text,
                voice=voice_params,
                audio_config=audio_config
            )
            
            with open(output_file, "wb") as f:
                f.write(response.audio_content)
        
        print(f"Google Cloud TTS audio saved to: {output_file}")
        return output_file
        
    except Exception as e:
        raise RuntimeError(f"Google Cloud TTS failed: {e}")

def _generate_local_tts(text, output_file, voice=None):
    """Generate audio using local TTS implementation (espeak-ng)."""
    espeak_voice = voice or os.getenv("ESPEAK_VOICE", "en")
    espeak_speed = os.getenv("ESPEAK_SPEED", "150")
    
    temp_wav_file = output_file.replace('.mp3', '.wav')
    
    try:
        cmd = [
            'espeak-ng',
            '-v', espeak_voice,
            '-s', str(espeak_speed),
            '-w', temp_wav_file,
            text
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"espeak-ng failed: {result.stderr}")
        
        if not os.path.exists(temp_wav_file):
            raise RuntimeError(f"espeak-ng did not create output file {temp_wav_file}")
        
        if output_file.endswith('.mp3'):
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(temp_wav_file)
                audio.export(output_file, format="mp3")
                os.remove(temp_wav_file)
                
                print(f"Local TTS audio saved to: {output_file}")
                return output_file
                
            except ImportError:
                raise RuntimeError("pydub library not installed. Please install it with: pip install pydub")
            except Exception as e:
                raise RuntimeError(f"Failed to convert WAV to MP3: {e}")
        else:
            os.rename(temp_wav_file, output_file)
            print(f"Local TTS audio saved to: {output_file}")
            return output_file
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("espeak-ng synthesis timed out")
    except FileNotFoundError:
        raise RuntimeError("espeak-ng is not installed. Please install it first:\nUbuntu/Debian: sudo apt-get install espeak-ng\nmacOS: brew install espeak\nCentOS/RHEL: sudo yum install espeak-ng")
    except Exception as e:
        raise RuntimeError(f"Local TTS synthesis error: {str(e)}")

def test_tts_providers():
    """Test all available TTS providers."""
    test_text = "Hello, this is a test of text to speech functionality."
    test_file = "test_output"
    
    providers = ["local", "azure", "gcp"]
    
    for provider in providers:
        try:
            print(f"\nTesting {provider.upper()} TTS...")
            output_file = generate_audio(test_text, f"{test_file}_{provider}.mp3", provider=provider)
            print(f"✅ {provider.upper()} TTS test successful: {output_file}")
        except Exception as e:
            print(f"❌ {provider.upper()} TTS test failed: {e}")

if __name__ == "__main__":
    provider = os.getenv("TTS_PROVIDER", "azure").lower()
    
    print(f"Testing TTS provider: {provider.upper()}")
    print("="*50)
    
    test_text = "Hello, this is a test of text to speech functionality."
    test_file = f"test_output_{provider}.mp3"
    
    try:
        output_file = generate_audio(test_text, test_file, provider=provider)
        print(f"✅ {provider.upper()} TTS test successful: {output_file}")
    except Exception as e:
        print(f"❌ {provider.upper()} TTS test failed: {e}")
        print("\nTrying with fallback settings...")
        test_tts_providers()
