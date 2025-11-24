import asyncio
from typing import AsyncGenerator, Callable
from loguru import logger
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.rtc import AudioStream, AudioSource, AudioFrame

class LiveKitTransport:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.room = ctx.room
        self.audio_out: AudioSource = None
        self.audio_stream: AudioStream = None
        self.participant_identity = None

    async def connect(self):
        logger.info(f"Connecting to room {self.room.name}")
        await self.ctx.connect()
        
        # Setup Audio Output
        self.audio_out = AudioSource(self.ctx.room.local_participant.source_enabled_audio)
        # Ideally we publish a track, but livekit-agents handles this usually via `agent` helpers
        # We'll use the standard way to emit audio
        
        # Wait for participant
        participant = await self.ctx.wait_for_participant()
        self.participant_identity = participant.identity
        logger.info(f"Participant {self.participant_identity} joined")
        
        # Subscribe to audio
        track = participant.track_publications[0].track # Simplified
        self.audio_stream = AudioStream(track)

    async def stream_in(self) -> AsyncGenerator[bytes, None]:
        """Yields PCM audio bytes from the user"""
        async for frame in self.audio_stream:
            yield frame.data.tobytes()

    async def send_audio(self, chunk: bytes):
        """Sends PCM audio bytes to the user"""
        # Create AudioFrame
        frame = AudioFrame(data=chunk, sample_rate=16000, num_channels=1, samples_per_channel=len(chunk)//2)
        await self.audio_out.capture_frame(frame)

    async def wait_for_track(self):
        # Helper to ensure we have a track to read from
        pass

