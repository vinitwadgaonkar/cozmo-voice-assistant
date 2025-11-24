# Use Pipecat's built-in Sarvam services instead of custom implementations
from loguru import logger  # type: ignore
from pipecat.frames.frames import (  # type: ignore
    Frame,
    StartFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    TextFrame,
    AudioRawFrame,
    UserAudioRawFrame,
)
from pipecat.services.sarvam.stt import SarvamSTTService  # type: ignore
from pipecat.services.sarvam.tts import SarvamTTSService  # type: ignore
from pipecat.transcriptions.language import Language  # type: ignore
from server.services.cartesia_tts import CartesiaTTSService
from server.config import settings


class LoggedSarvamSTTService(SarvamSTTService):
    """Sarvam STT with explicit connect/disconnect logging for debugging."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        @self.event_handler("on_connected")
        async def _on_connected(_stt):
            logger.info(
                f"🟢 Sarvam STT connected ({self.model_name}, sample_rate={self.sample_rate}Hz)"
            )

        @self.event_handler("on_disconnected")
        async def _on_disconnected(_stt):
            logger.info("⚪️ Sarvam STT disconnected")

        @self.event_handler("on_connection_error")
        async def _on_connection_error(_stt, error: str):
            logger.error(f"🔴 Sarvam STT connection error: {error}")
        
        @self.event_handler("on_transcription")
        async def _on_transcription(_stt, text: str, is_final: bool = False):
            logger.info(f"📝 Sarvam STT transcription: '{text}' (final={is_final})")
        
        @self.event_handler("on_error")
        async def _on_error(_stt, error: Exception):
            logger.error(f"🔴 Sarvam STT error: {error}")

    async def start(self, frame):  # type: ignore[override]
        logger.info(f"🚀 Sarvam STT start (frame rate={frame.audio_in_sample_rate}Hz)")
        await super().start(frame)

    async def process_frame(self, frame: Frame, direction):
        if isinstance(frame, StartFrame):
            logger.info("📡 Sarvam STT received StartFrame")
        elif isinstance(frame, TranscriptionFrame):
            logger.info(f"📝 STT TRANSCRIPT (FINAL): '{frame.text}' (user_id={frame.user_id})")
        elif isinstance(frame, InterimTranscriptionFrame):
            logger.info(f"📝 STT INTERIM (PARTIAL): '{frame.text}' - Starting LLM early!")
        elif isinstance(frame, TextFrame):
            logger.debug(f"📄 TextFrame from STT: '{frame.text}'")
        elif isinstance(frame, (AudioRawFrame, UserAudioRawFrame)):
            logger.debug(
                f"🎧 STT audio frame received (size={len(getattr(frame, 'audio', b''))} bytes, "
                f"type={type(frame).__name__})"
            )
        await super().process_frame(frame, direction)

    async def _connect(self):  # type: ignore[override]
        logger.info(
            f"🔌 Connecting to Sarvam STT (model={self.model_name}, target={self.sample_rate}Hz)"
        )
        try:
            await super()._connect()
            logger.info("🟢 Sarvam STT websocket established")
        except Exception as e:
            logger.error(f"❌ Failed to connect Sarvam STT: {e}", exc_info=True)
            raise

    async def _disconnect(self):  # type: ignore[override]
        if getattr(self, "_socket_client", None):
            logger.info("⚪️ Closing Sarvam STT websocket")
        await super()._disconnect()

    # Removed run_stt override - let base class handle audio processing
    # The base SarvamSTTService handles WAV encoding when input_audio_codec="wav" is set
    # This should be more reliable than manual WAV wrapping

def create_stt(sarvam_api_key: str):
    """Create STT service (Sarvam only for reliable Hindi support)."""
    logger.info("🟡 Using Sarvam STT (Deepgram disabled)")
    
    stt = LoggedSarvamSTTService(
        api_key=sarvam_api_key,
        model="saarika:v2.5",
        sample_rate=16000,
        input_audio_codec="wav",
        params=SarvamSTTService.InputParams(
            language=Language.HI_IN,
            high_vad_sensitivity=True,
            vad_signals=True
        )
    )
    # Event handlers are already registered in LoggedSarvamSTTService.__init__
    return stt

def create_tts(api_key: str):
    """Create TTS service - use Cartesia only for ultra-low latency."""
    if not settings.CARTESIA_API_KEY:
        raise ValueError("CARTESIA_API_KEY is required but not set")
    
    logger.info("🎯 Using Cartesia TTS (ultra-low latency)")
    # Use 16000 Hz to match LiveKit transport sample rate (avoids resampling)
    # Model: "sonic-3" is the latest, "sonic-2" is also available
    # Voice: Using a default English voice UUID - user should provide correct voice ID for Hindi
    # TODO: Get correct Hindi voice ID from Cartesia dashboard or API
    return CartesiaTTSService(
        api_key=settings.CARTESIA_API_KEY,
        voice_id="f9836c6e-a0bd-460e-9d3c-f7299fa60f94",  # Default voice from docs example
        model="sonic-3",  # Use sonic-3 instead of sonic-multilingual
        sample_rate=16000  # Match LiveKit transport to avoid resampling
    )

