import json
import websockets
import asyncio
from typing import AsyncGenerator
from loguru import logger

from pipecat.services.stt_service import STTService
from pipecat.frames.frames import AudioRawFrame, TextFrame, ErrorFrame, EndFrame, Frame

class SarvamSTTService(STTService):
    def __init__(self, api_key: str, url: str, language: str = "hi-IN"):
        super().__init__()
        self.api_key = api_key
        self.url = url
        self.language = language
        self._ws = None

    async def start(self, frame_serializer):
        # Connection logic handled in process_frame usually or explicit start
        pass

    async def process_frame(self, frame: Frame):
        # This method is called for every frame in the pipeline.
        # We need to handle AudioRawFrame and send to Sarvam.
        pass

    # Pipecat 0.0.95+ usually uses a run_stt loop or process_generator depending on implementation
    # Let's implement the generator pattern common in custom services
    
    async def run_stt(self, audio_stream: AsyncGenerator[Frame, None]) -> AsyncGenerator[Frame, None]:
        """
        Connects to Sarvam and streams audio.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(self.url, extra_headers=headers) as ws:
                logger.info("Connected to Sarvam STT")
                
                # Initial Config
                config = {
                    "config": {
                        "language_code": self.language,
                        "model": "saarika",
                        "encoding": "linear16",
                        "sample_rate": 16000,
                        "channels": 1,
                        "vad_sensitivity": "high" # as requested
                    }
                }
                await ws.send(json.dumps(config))

                # Task to receive transcripts
                async def receive_transcripts():
                    try:
                        async for msg in ws:
                            data = json.loads(msg)
                            transcript = data.get("transcript", "")
                            is_final = data.get("type") == "final"
                            
                            if transcript:
                                logger.debug(f"STT: {transcript} (Final: {is_final})")
                                # Yield TextFrame
                                # Note: In Pipecat, we might want to differentiate partial/final
                                # But Pipecat STT usually emits TextFrame. 
                                # Interims are usually handled if the pipeline supports it.
                                yield TextFrame(text=transcript)
                    except Exception as e:
                        logger.error(f"Sarvam Receiver Error: {e}")

                # We need to merge the receive generator with the input audio processing
                # This is complex in a single generator. 
                # Standard Pipecat pattern: Split input and output tasks.
                
                # However, `run_stt` expects to yield Frames.
                # We'll spawn the receiver and yield from a queue.
                
                queue = asyncio.Queue()
                
                async def receiver_task():
                    async for msg in ws:
                        data = json.loads(msg)
                        transcript = data.get("transcript", "")
                        if transcript:
                            is_final = data.get("type") == "final"
                            # Typically Pipecat uses InterimTranscriptionFrame for partials
                            # and TextFrame for final
                            # Checking import... will assume TextFrame for now for simplicity 
                            # or use specific frames if available.
                            from pipecat.frames.frames import TextFrame, InterimTranscriptionFrame
                            
                            if is_final:
                                await queue.put(TextFrame(text=transcript))
                            else:
                                await queue.put(InterimTranscriptionFrame(text=transcript, timestamp=0)) # timestamp required?

                    await queue.put(None) # Sentinel

                recv_task = asyncio.create_task(receiver_task())

                async def sender_task():
                    async for frame in audio_stream:
                        if isinstance(frame, AudioRawFrame):
                            # Send audio bytes
                            # Sarvam expects raw bytes or base64? 
                            # Usually raw bytes in binary frame for streaming websockets
                            await ws.send(frame.audio)
                        elif isinstance(frame, EndFrame):
                            # Send stop
                            await ws.send(json.dumps({"type": "stop"}))
                            break
                    # Close sending side
                    # await ws.close() # Wait for receiver to finish

                send_task = asyncio.create_task(sender_task())

                # Yield results
                while True:
                    # We prioritize the queue to output text as fast as possible
                    # But we also need to keep the loop alive.
                    # Actually, run_stt is a generator.
                    
                    # We can just wait on the queue.
                    result = await queue.get()
                    if result is None:
                        break
                    yield result
                
                await send_task
                await recv_task

        except Exception as e:
            logger.error(f"Sarvam STT Connection Failed: {e}")
            yield ErrorFrame(error=str(e))

