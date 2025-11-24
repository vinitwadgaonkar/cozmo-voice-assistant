import asyncio
from typing import AsyncGenerator, List
from loguru import logger
from agent.config.settings import settings
from agent.services.tts_base import TTSProvider
from agent.core.latency_tracker import tracker

class TTSRacer:
    def __init__(self, providers: List[TTSProvider]):
        self.providers = providers
        self.mode = settings.TTS_MODE

    async def stream_audio(self, text_stream_factory, turn_id: str) -> AsyncGenerator[bytes, None]:
        """
        text_stream_factory: A function that returns a new AsyncGenerator for text.
        We need to produce multiple text streams for the racers.
        """
        
        if self.mode != "race":
            # Select single provider
            provider = next((p for p in self.providers if p.name == self.mode), self.providers[0])
            logger.info(f"Using single TTS provider: {provider.name}")
            async for chunk in provider.stream_audio(text_stream_factory(), turn_id):
                tracker.mark(turn_id, "t_tts_first_audio")
                yield chunk
            return

        # RACE MODE
        logger.info(f"Starting TTS Race for {turn_id}")
        
        queue = asyncio.Queue()
        winner_event = asyncio.Event()
        active_tasks = []
        winner_name = None

        async def run_provider(p: TTSProvider):
            nonlocal winner_name
            try:
                first_chunk = True
                async for chunk in p.stream_audio(text_stream_factory(), turn_id):
                    if winner_event.is_set():
                        if winner_name != p.name:
                            # We lost, stop processing
                            break
                    else:
                        # We are the first!
                        winner_name = p.name
                        winner_event.set()
                        logger.info(f"WINNER: {p.name} for {turn_id}")
                        tracker.set_winner(turn_id, p.name)
                        tracker.mark(turn_id, "t_tts_first_audio")
                    
                    if winner_name == p.name:
                        await queue.put(chunk)
            except Exception as e:
                logger.error(f"Provider {p.name} failed: {e}")
            finally:
                if winner_name == p.name:
                    await queue.put(None) # Signal end

        # Start racers
        for p in self.providers:
            active_tasks.append(asyncio.create_task(run_provider(p)))

        # Yield from queue
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
            
        # Cleanup
        for task in active_tasks:
            task.cancel()

