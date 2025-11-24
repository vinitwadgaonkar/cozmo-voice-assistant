"""Cartesia Sonic TTS service implementation for Pipecat."""

import asyncio
from typing import AsyncGenerator, Optional

from loguru import logger

from pipecat.frames.frames import (
    CancelFrame,
    EndFrame,
    ErrorFrame,
    Frame,
    InterruptionFrame,
    LLMFullResponseEndFrame,
    StartFrame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.tts_service import TTSService
from pipecat.utils.tracing.service_decorators import traced_tts

try:
    from cartesia import Cartesia
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    logger.error("In order to use Cartesia, you need to `pip install cartesia`.")
    raise Exception(f"Missing module: {e}")


class CartesiaTTSService(TTSService):
    """Cartesia Sonic TTS service for ultra-low latency text-to-speech.
    
    Provides streaming TTS using Cartesia's Sonic model with support for
    multiple languages including Hindi. Optimized for sub-100ms latency.
    """

    def __init__(
        self,
        *,
        api_key: str,
        voice_id: str = "sonic-hindi",
        model: str = "sonic-multilingual",
        sample_rate: Optional[int] = 24000,
        **kwargs,
    ):
        """Initialize the Cartesia TTS service.

        Args:
            api_key: Cartesia API key.
            voice_id: Voice ID to use (e.g., "sonic-hindi", "sonic-english").
            model: Model to use (default: "sonic-multilingual").
            sample_rate: Audio sample rate in Hz. Defaults to 24000.
            **kwargs: Additional arguments passed to parent TTSService.
        """
        super().__init__(
            aggregate_sentences=False,  # Don't wait for sentence completion - start immediately
            push_text_frames=True,
            pause_frame_processing=True,
            push_stop_frames=True,
            sample_rate=sample_rate or 24000,
            **kwargs,
        )
        
        self._client = Cartesia(api_key=api_key)
        self._voice_id = voice_id
        self._model = model
        self._websocket = None
        self._ws_connection = None
        self._receive_task = None
        self._disconnecting = False
        self._started = False
        self._audio_queue = None
        
        self.set_model_name(model)
        self.set_voice(voice_id)

    def can_generate_metrics(self) -> bool:
        """Check if this service can generate processing metrics.

        Returns:
            True, as Cartesia service supports metrics generation.
        """
        return True

    async def start(self, frame: StartFrame):
        """Start the Cartesia TTS service.

        Args:
            frame: The start frame containing initialization parameters.
        """
        await super().start(frame)
        self._audio_queue = asyncio.Queue()
        await self._connect()

    async def stop(self, frame: EndFrame):
        """Stop the Cartesia TTS service.

        Args:
            frame: The end frame.
        """
        await super().stop(frame)
        await self._disconnect()

    async def cancel(self, frame: CancelFrame):
        """Cancel the Cartesia TTS service.

        Args:
            frame: The cancel frame.
        """
        await super().cancel(frame)
        await self._disconnect()

    async def push_frame(self, frame: Frame, direction: FrameDirection = FrameDirection.DOWNSTREAM):
        """Push a frame downstream with special handling for stop conditions.

        Args:
            frame: The frame to push.
            direction: The direction to push the frame.
        """
        await super().push_frame(frame, direction)
        if isinstance(frame, (TTSStoppedFrame, InterruptionFrame)):
            self._started = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process a frame and handle full response end."""
        # No no_more_inputs() method needed - ws.send() handles completion
        return await super().process_frame(frame, direction)

    async def flush_audio(self):
        """Flush any pending audio synthesis."""
        # ws.send() iterator handles completion automatically
        pass

    async def _connect(self):
        """Connect to Cartesia WebSocket."""
        await self._connect_websocket()
        # No background receive task needed - audio comes via ws.send() iterator

    async def _disconnect(self):
        """Disconnect from Cartesia WebSocket and clean up tasks."""
        try:
            self._disconnecting = True
            
            if self._receive_task:
                await self.cancel_task(self._receive_task, timeout=2.0)
                self._receive_task = None
            
            await self._disconnect_websocket()
            
        except Exception as e:
            logger.error(f"{self} exception: {e}")
            await self.push_error(ErrorFrame(error=f"{self} error: {e}"))
        finally:
            self._started = False
            self._websocket = None
            self._ws_connection = None
            self._disconnecting = False
            if self._audio_queue:
                # Put sentinel to unblock any waiting
                try:
                    self._audio_queue.put_nowait(None)
                except:
                    pass

    async def _connect_websocket(self):
        """Establish WebSocket connection to Cartesia API."""
        try:
            logger.info(f"🔌 Connecting to Cartesia TTS (model={self._model}, voice={self._voice_id}, sample_rate={self.sample_rate}Hz)")
            # Create websocket connection using Cartesia SDK
            # According to docs: ws.send() is called on websocket, returns iterator
            ws = self._client.tts.websocket()
            
            # Store websocket - we'll use ws.send() directly, not context
            self._ws_connection = ws
            self._websocket = ws  # Store websocket for send operations
            
            logger.info("🟢 Connected to Cartesia TTS Websocket")
            await self._call_event_handler("on_connected")
            
        except Exception as e:
            logger.error(f"❌ Cartesia TTS connection exception: {e}", exc_info=True)
            await self.push_error(ErrorFrame(error=f"{self} connection error: {e}"))
            self._websocket = None
            self._ws_connection = None
            await self._call_event_handler("on_connection_error", f"{e}")
            raise

    async def _receive_audio(self):
        """Background task to receive audio from Cartesia WebSocket.
        
        Note: According to Cartesia docs, ws.send() returns an iterator.
        Audio receiving is handled in run_tts() via the send() iterator.
        This method is kept for compatibility but may not be used.
        """
        # Audio is received via ws.send() iterator in run_tts()
        # This background task is not needed with the correct API pattern
        logger.debug("🎧 _receive_audio called - audio handled via ws.send() iterator")
        return

    async def _disconnect_websocket(self):
        """Close the WebSocket connection."""
        if self._ws_connection:
            try:
                await self._ws_connection.close()
            except Exception as e:
                logger.warning(f"Error closing websocket: {e}")
            finally:
                self._websocket = None
                self._ws_connection = None


    @traced_tts
    async def run_tts(self, text: str) -> AsyncGenerator[Frame, None]:
        """Generate speech audio frames from input text using Cartesia TTS.

        According to Cartesia docs: ws.send() returns an iterator that yields audio chunks.
        Pattern: for output in ws.send(model_id=..., transcript=..., voice=..., output_format=...)

        Args:
            text: The text input to synthesize.

        Yields:
            Frame objects including TTSStartedFrame, TTSAudioRawFrame(s), or TTSStoppedFrame.
        """
        logger.debug(f"Generating TTS: [{text}]")

        try:
            if not self._websocket:
                await self._connect()

            try:
                if not self._started:
                    await self.start_ttfb_metrics()
                    yield TTSStartedFrame()
                    self._started = True
                
                await self.start_tts_usage_metrics(text)
                
                # According to Cartesia docs: ws.send() returns iterator
                # for output in ws.send(model_id=..., transcript=..., voice=..., output_format=..., stream=True)
                logger.debug(f"📤 Calling Cartesia ws.send() with transcript: '{text[:50]}...'")
                
                # Use ws.send() which returns an iterator of audio chunks
                # Voice format: {"mode": "id", "id": "uuid"} or {"mode": "preset", "preset": "name"}
                # Try with language parameter for multilingual models
                voice_param = {"mode": "id", "id": self._voice_id}
                
                # For sonic-3, we can also try language parameter
                send_params = {
                    "model_id": self._model,
                    "transcript": text,
                    "voice": voice_param,
                    "output_format": {
                        "container": "raw",
                        "encoding": "pcm_s16le",
                        "sample_rate": self.sample_rate,
                    },
                    "stream": True,  # Enable streaming
                }
                
                # Add language if model supports it (for multilingual models)
                if "multilingual" in self._model.lower() or "sonic-3" in self._model.lower():
                    send_params["language"] = "hi"  # Hindi
                
                logger.debug(f"📤 Cartesia send params: model={self._model}, voice={voice_param}, sample_rate={self.sample_rate}")
                
                # ws.send() returns an iterator - iterate and yield frames
                try:
                    logger.debug("📤 About to call ws.send()...")
                    
                    # Try calling ws.send() and see what it returns
                    send_result = None
                    try:
                        send_result = self._ws_connection.send(**send_params)
                        logger.debug(f"📤 ws.send() returned: type={type(send_result)}, value={send_result}")
                    except Exception as send_error:
                        logger.error(f"❌ ws.send() raised exception: {send_error}", exc_info=True)
                        yield ErrorFrame(error=f"Cartesia TTS send() error: {send_error}")
                        yield TTSStoppedFrame()
                        return
                    
                    if send_result is None:
                        logger.error("❌ ws.send() returned None")
                        yield ErrorFrame(error="Cartesia TTS send() returned None")
                        yield TTSStoppedFrame()
                        return
                    
                    logger.debug("📤 Starting Cartesia ws.send() iteration...")
                    audio_received = False
                    
                    # ws.send() returns a generator that yields WebSocketTtsOutput objects
                    for output in send_result:
                        if self._disconnecting:
                            logger.debug("🛑 Disconnecting, stopping Cartesia iteration")
                            break
                        
                        # Process the output - WebSocketTtsOutput has .audio attribute
                        if hasattr(output, 'audio') and output.audio:
                            # WebSocketTtsOutput object with audio bytes
                            audio_bytes = output.audio
                            if audio_bytes:
                                audio_received = True
                                await self.stop_ttfb_metrics()
                                frame = TTSAudioRawFrame(
                                    audio=audio_bytes,
                                    sample_rate=self.sample_rate,
                                    num_channels=1,  # Mono audio
                                )
                                yield frame
                                logger.debug(f"🔊 Yielded Cartesia audio frame ({len(audio_bytes)} bytes)")
                        elif isinstance(output, dict):
                            # Fallback: dict format
                            if output.get("audio"):
                                audio_bytes = output["audio"]
                                if audio_bytes:
                                    audio_received = True
                                    await self.stop_ttfb_metrics()
                                    frame = TTSAudioRawFrame(
                                        audio=audio_bytes,
                                        sample_rate=self.sample_rate,
                                    )
                                    yield frame
                                    logger.debug(f"🔊 Yielded Cartesia audio frame ({len(audio_bytes)} bytes)")
                            elif output.get("error"):
                                error_msg = output.get("error", "Unknown error")
                                logger.error(f"❌ Cartesia TTS error: {error_msg}")
                                yield ErrorFrame(error=f"Cartesia TTS error: {error_msg}")
                        elif isinstance(output, bytes):
                            # Direct audio bytes
                            audio_received = True
                            await self.stop_ttfb_metrics()
                            frame = TTSAudioRawFrame(
                                audio=output,
                                sample_rate=self.sample_rate,
                            )
                            yield frame
                            logger.debug(f"🔊 Yielded Cartesia audio bytes ({len(output)} bytes)")
                        else:
                            logger.debug(f"📦 Cartesia output (type={type(output).__name__}): {str(output)[:100]}")
                    
                    if not audio_received:
                        logger.warning("⚠️ Cartesia ws.send() completed but no audio was received")
                        
                except Exception as e:
                    logger.error(f"❌ Error in Cartesia ws.send(): {e}", exc_info=True)
                    yield ErrorFrame(error=f"Cartesia TTS send error: {e}")
                
                yield TTSStoppedFrame()
                        
            except Exception as e:
                logger.error(f"{self} exception: {e}", exc_info=True)
                yield ErrorFrame(error=f"{self} error: {e}")
                yield TTSStoppedFrame()
                return
                
        except Exception as e:
            logger.error(f"{self} exception: {e}", exc_info=True)
            yield ErrorFrame(error=f"{self} error: {e}")
