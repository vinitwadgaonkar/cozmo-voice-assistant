import json
import websockets
import asyncio
import base64
from typing import AsyncGenerator, Optional
from loguru import logger

from pipecat.services.tts_service import TTSService
from pipecat.frames.frames import AudioRawFrame, TextFrame, EndFrame, Frame, StartFrame, StopFrame

class SarvamTTSService(TTSService):
    def __init__(self, api_key: str, url: str, voice_id: str = "anushka", model: str = "bulbul:v2"):
        super().__init__()
        self.api_key = api_key
        self.url = url
        self.voice_id = voice_id
        self.model = model
        self.pace = 1.05
        self.min_buffer = 40
        self.max_chunk_length = 180
        
    async def run_tts(self, text_stream: AsyncGenerator[Frame, None]) -> AsyncGenerator[Frame, None]:
        """
        Streaming TTS: TextFrames IN -> AudioRawFrames OUT
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(self.url, extra_headers=headers) as ws:
                logger.info(f"Connected to Sarvam TTS ({self.model}/{self.voice_id})")

                # Initial Config
                await ws.send(json.dumps({
                    "voice_id": self.voice_id,
                    "output_format": "pcm_16000",
                    "model": self.model,
                    "pace": self.pace
                }))

                # We need to send text and receive audio simultaneously.
                # Similar pattern to STT.

                queue = asyncio.Queue()

                async def receiver_task():
                    try:
                        async for msg in ws:
                            # Sarvam sends audio as binary or JSON with audio field?
                            # Usually streaming TTS sends binary PCM chunks.
                            if isinstance(msg, bytes):
                                # Raw PCM 16k 16bit mono
                                await queue.put(AudioRawFrame(audio=msg, sample_rate=16000, num_channels=1))
                            else:
                                data = json.loads(msg)
                                if "audio" in data:
                                    # If base64 encoded in JSON
                                    audio = base64.b64decode(data["audio"])
                                    await queue.put(AudioRawFrame(audio=audio, sample_rate=16000, num_channels=1))
                    except Exception as e:
                        logger.error(f"TTS Receiver Error: {e}")
                    finally:
                        await queue.put(None)

                recv_task = asyncio.create_task(receiver_task())

                async def sender_task():
                    buffer = ""
                    async for frame in text_stream:
                        if isinstance(frame, TextFrame):
                            text = frame.text
                            if not text:
                                continue
                                
                            # Simple buffering/chunking if needed, or just send
                            # Sarvam might accept partials. 
                            # Prompt says: min_buffer_size=40, max_chunk_length=180
                            buffer += text
                            
                            # Check buffer constraints
                            # This is a simplified logic. Real logic handles sentence boundaries.
                            if len(buffer) >= self.min_buffer:
                                chunk = buffer[:self.max_chunk_length]
                                buffer = buffer[self.max_chunk_length:]
                                await ws.send(json.dumps({"text": chunk}))
                        
                        elif isinstance(frame, (EndFrame, StopFrame)):
                            # Flush remaining
                            if buffer:
                                await ws.send(json.dumps({"text": buffer}))
                            await ws.send(json.dumps({"type": "stop"})) # Or implicit close?
                            break
                            
                    # End of text stream
                    # Send stop signal if API requires it or just close
                    pass

                send_task = asyncio.create_task(sender_task())

                # Output loop
                while True:
                    frame = await queue.get()
                    if frame is None:
                        break
                    yield frame

                await send_task
                # await recv_task # Recv task finishes when WS closes

        except Exception as e:
            logger.error(f"Sarvam TTS Error: {e}")
            yield EndFrame()

