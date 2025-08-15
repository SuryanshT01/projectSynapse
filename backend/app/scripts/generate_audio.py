# backend/app/scripts/generate_audio.py
import os
import azure.cognitiveservices.speech as speechsdk

def generate_audio(text, output_filename, voice_name="en-US-JennyNeural"):
    tts_provider = os.environ.get("TTS_PROVIDER", "azure")

    if tts_provider == "azure":
        speech_key = os.environ.get("AZURE_TTS_KEY")
        service_region = os.environ.get("AZURE_TTS_ENDPOINT", "eastus").split('.')[0] # Heuristic
        
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
        speech_config.speech_synthesis_voice_name = voice_name
        
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesized for text [{text}] and saved to [{output_filename}]")
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print(f"Error details: {cancellation_details.error_details}")
            return False
    else:
        # Placeholder for other TTS providers like GCP or local
        print(f"TTS Provider '{tts_provider}' not implemented in this script.")
        return False