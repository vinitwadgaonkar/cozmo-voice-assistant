import asyncio
from typing import AsyncGenerator
from openai import AsyncOpenAI
from loguru import logger
from agent.config.settings import settings
from agent.core.latency_tracker import tracker

class OpenAILLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini" # Fastest available as requested

    async def stream_response(self, history: list, turn_id: str) -> AsyncGenerator[str, None]:
        """
        Streams tokens from OpenAI.
        """
        logger.info(f"LLM Request for {turn_id}")
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=history,
                stream=True,
                max_tokens=150, # Keep responses short
            )

            first_token = True
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    if first_token:
                        tracker.mark(turn_id, "t_llm_first_token")
                        first_token = False
                    
                    yield content
            
            tracker.mark(turn_id, "t_llm_last_token")
            
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield "Sorry, I encountered an error."

