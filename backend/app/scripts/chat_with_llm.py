# backend/app/scripts/chat_with_llm.py
import os
from openai import OpenAI
import google.generativeai as genai

def get_llm_client(provider):
    if provider == "openai":
        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    elif provider == "gemini":
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        return genai
    elif provider == "ollama":
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def chat_with_llm(prompt, model_name=None):
    llm_provider = os.environ.get("LLM_PROVIDER", "gemini")
    
    if not model_name:
        model_name = os.environ.get("GEMINI_MODEL") if llm_provider == "gemini" \
                     else os.environ.get("OLLAMA_MODEL") if llm_provider == "ollama" \
                     else "gpt-3.5-turbo"

    client = get_llm_client(llm_provider)

    try:
        if llm_provider == "gemini":
            model = client.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        else: # OpenAI compatible
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return None