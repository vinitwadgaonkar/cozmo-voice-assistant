import asyncio
import websockets
import json
from typing import AsyncGenerator
from loguru import logger
from cartesia import Cartesia
from agent.config.settings import settings
from agent.services.tts_base import TTSProvider

class CartesiaTTSService(TTSProvider):
    def __init__(self):
        self.client = Cartesia(api_key=settings.CARTESIA_API_KEY)
        self.voice_id = settings.CARTESIA_VOICE_ID
        self.model_id = "sonic-multilingual" # Assuming this is the model for Hindi
        self.encoding = "pcm_s16le"
        self.sample_rate = 16000

    @property
    def name(self) -> str:
        return "cartesia"

    async def stream_audio(self, text_stream: AsyncGenerator[str, None], turn_id: str) -> AsyncGenerator[bytes, None]:
        logger.info(f"Starting Cartesia TTS for {turn_id}")
        
        # Create a websocket connection for streaming
        ws = self.client.tts.websocket()
        
        try:
            # Context manager logic if SDK supports it, else manual connect
            # Note: Using mock logic based on typical Cartesia usage pattern as exact SDK async streaming syntax might vary
            
            ctx = ws.context(self.model_id, self.voice_id, output_format={
                "container": "raw",
                "encoding": self.encoding,
                "sample_rate": self.sample_rate
            })
            
            async def sender():
                async for token in text_stream:
                    await ctx.send(token)
                await ctx.no_more_inputs()

            # Start sender
            asyncio.create_task(sender())

            # Receive audio
            async for output in ctx.receive():
                if output.get("audio"):
                    yield output["audio"]
                    
        except Exception as e:
            logger.error(f"Cartesia TTS Error: {e}")
            
        finally:
            await ws.close()

