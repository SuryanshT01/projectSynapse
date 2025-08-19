# backend/app/scripts/chat_with_llm.py

import os
import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema.messages import HumanMessage, SystemMessage

# Configure a logger for this module
logger = logging.getLogger(__name__)

def chat_with_llm(prompt: str, system_message: Optional[str] = None) -> str:
    """
    Communicates with the configured LLM provider (Gemini) to get a response.

    This function acts as a centralized interface for all LLM calls. It correctly
    formats the input prompt and optional system message into the list-based
    format required by LangChain's `invoke` method, resolving the core
    'NoneType' is not iterable error.

    Args:
        prompt: The main user query or data to be processed by the LLM.
        system_message: An optional instruction that defines the LLM's role,
                        persona, or output format.

    Returns:
        The content of the LLM's response as a string.

    Raises:
        ValueError: If the required GOOGLE_API_KEY environment variable is not set.
        RuntimeError: If the API call to Gemini fails for any reason.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider!= "gemini":
        # For the hackathon, we are focusing only on the Gemini implementation.
        # The other providers from the sample are omitted for clarity.
        logger.error(f"Unsupported LLM_PROVIDER configured: {provider}. This project is configured for 'gemini'.")
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash") # Updated to a common, effective model

    if not api_key:
        logger.critical("GOOGLE_API_KEY environment variable is not set. The application cannot connect to the LLM.")
        raise ValueError("GOOGLE_API_KEY must be set in the environment.")

    # --- The Core Fix: Constructing the correct message format ---
    # LangChain's invoke() method expects a list of message objects.
    messages = []
    if system_message:
        messages.append(SystemMessage(content=system_message))
    messages.append(HumanMessage(content=prompt))
    # -------------------------------------------------------------

    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.5, # Lowered for more deterministic, factual output
            convert_system_message_to_human=True # Ensures compatibility for models that prefer user/model turns
        )
        
        logger.info(f"Invoking Gemini model '{model_name}' with {len(messages)} messages.")
        response = llm.invoke(messages)
        
        # The response object has a 'content' attribute with the text
        return response.content

    except Exception as e:
        logger.error(f"LLM call to Gemini failed: {e}", exc_info=True)
        # Provide a more informative error to the calling function
        raise RuntimeError(f"Gemini API call failed: {e}")

if __name__ == "__main__":
    # This block allows for direct testing of this script.
    # Ensure your.env file is in the parent directory or GOOGLE_API_KEY is exported.
    from dotenv import load_dotenv
    import sys
    # Add project root to path to allow for relative imports if run directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    load_dotenv()

    print("--- Running Standalone Test for chat_with_llm.py ---")
    
    test_system_message = "You are a helpful assistant that provides concise answers."
    test_prompt = "What is the capital of France?"
    
    print(f"System Message: {test_system_message}")
    print(f"User Prompt: {test_prompt}")

    try:
        reply = chat_with_llm(prompt=test_prompt, system_message=test_system_message)
        print("\nLLM Response:", reply)
    except Exception as e:
        print("\nError during test:", str(e))