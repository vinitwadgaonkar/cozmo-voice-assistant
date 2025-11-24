from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.groq.llm import GroqLLMService
from server.config import settings

# System prompt optimized for speed (shorter = faster)
SYSTEM_PROMPT = (
    "Hindi voice assistant. Chhote jawab do. 1 line max. "
    "Hindi mein bolo."
)

def create_llm():
    # Prioritize Groq for speed if available
    if settings.GROQ_API_KEY:
        return GroqLLMService(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.1-8b-instant",  # Fastest model
            # Optimize for ultra-low latency (<200ms target)
            temperature=0.3,  # Lower = faster, more deterministic
            max_tokens=15,     # Ultra-short responses for speed (reduced from 30)
            top_p=0.8,         # Faster sampling
            stream=True,       # Ensure streaming is enabled
        )
    elif settings.OPENAI_API_KEY:
        return OpenAILLMService(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini", # Low latency model
        )
    else:
        raise ValueError("No LLM API Key provided")

# Note: To swap to Sarvam-M later, you would create a `SarvamLLMService` 
# inheriting from `LLMService` similar to the STT/TTS services, 
# pointing to Sarvam's text generation endpoint.

