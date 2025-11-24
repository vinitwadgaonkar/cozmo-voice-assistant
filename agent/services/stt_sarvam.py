import asyncio
import json
import websockets
from typing import AsyncGenerator, Optional, Callable
from loguru import logger
from agent.config.settings import settings

class SarvamSTTService:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        # Placeholder URL - would need actual Sarvam websocket endpoint
        self.url = "wss://api.sarvam.ai/v1/stt/streaming" 
        self.language = "hi-IN"

    async def stream_transcription(
        self, 
        audio_stream: AsyncGenerator[bytes, None],
        on_start_turn: Callable[[str], None],
        on_partial: Callable[[str, str], None], # turn_id, text
        on_final: Callable[[str, str], None]    # turn_id, text
    ):
        """
        Connects to Sarvam WebSocket and streams audio.
        Yields events or calls callbacks.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(self.url, extra_headers=headers) as ws:
                logger.info("Connected to Sarvam STT")
                
                # Config message
                await ws.send(json.dumps({
                    "config": {
                        "language_code": self.language,
                        "model": "saarika",
                        "encoding": "linear16",
                        "sample_rate": 16000,
                        "channels": 1
                    }
                }))

                # Start sender task
                async def sender():
                    try:
                        async for chunk in audio_stream:
                            await ws.send(chunk)
                        await ws.send(json.dumps({"type": "stop"}))
                    except Exception as e:
                        logger.error(f"Error sending audio to Sarvam: {e}")

                sender_task = asyncio.create_task(sender())

                # Receive loop
                current_turn_id = f"turn_{asyncio.get_event_loop().time()}"
                on_start_turn(current_turn_id)
                
                async for msg in ws:
                    data = json.loads(msg)
                    
                    if data.get("type") == "partial":
                        transcript = data.get("transcript", "")
                        if transcript:
                            on_partial(current_turn_id, transcript)
                            
                    elif data.get("type") == "final":
                        transcript = data.get("transcript", "")
                        if transcript:
                            on_final(current_turn_id, transcript)
                            # New turn starts after final? Or keep same stream?
                            # Depending on VAD logic, usually we keep stream open.
                            
        except Exception as e:
            logger.error(f"Sarvam STT connection failed: {e}")
            # Reconnection logic would go here

