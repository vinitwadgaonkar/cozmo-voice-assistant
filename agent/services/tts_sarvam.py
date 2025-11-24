import asyncio
import json
import websockets
from typing import AsyncGenerator
from loguru import logger
from agent.config.settings import settings
from agent.services.tts_base import TTSProvider

class SarvamTTSService(TTSProvider):
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.url = "wss://api.sarvam.ai/v1/tts/streaming" # Placeholder
        self.voice_id = settings.SARVAM_VOICE_ID

    @property
    def name(self) -> str:
        return "sarvam"

    async def stream_audio(self, text_stream: AsyncGenerator[str, None], turn_id: str) -> AsyncGenerator[bytes, None]:
        logger.info(f"Starting Sarvam TTS for {turn_id}")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(self.url, extra_headers=headers) as ws:
                # Config
                await ws.send(json.dumps({
                    "voice_id": self.voice_id,
                    "output_format": "pcm_16000",
                    "model": "bulbul"
                }))
                
                async def sender():
                    async for token in text_stream:
                        await ws.send(json.dumps({"text": token}))
                    await ws.send(json.dumps({"type": "stop"}))
                
                sender_task = asyncio.create_task(sender())
                
                async for msg in ws:
                    # Assume binary messages are audio, text messages are control
                    if isinstance(msg, bytes):
                        yield msg
                    else:
                        data = json.loads(msg)
                        if data.get("audio"):
                            # base64 decode if necessary, but assuming bytes for now or base64 field
                            pass 
                            
        except Exception as e:
            logger.error(f"Sarvam TTS Error: {e}")

