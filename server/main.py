# Ignore deprecation warning from pipecat
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import os
from loguru import logger
from livekit import api
from livekit.agents import JobContext, WorkerOptions, cli, JobProcess, JobRequest

from server.config import settings
from pipecat.transports.services.livekit import LiveKitTransport, LiveKitParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_response import LLMUserContextAggregator
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.frames.frames import LLMMessagesFrame

from server.services.sarvam_services import create_stt, create_tts
from server.services.llm import create_llm, SYSTEM_PROMPT
from server.utils.vad import create_vad
from server.utils.latency_logger import LatencyLogger

async def entrypoint(ctx: JobContext):
    logger.info(f"🎯 ENTRYPOINT CALLED - Agent connecting to room: {ctx.room.name}")
    
    # Connect to the room using JobContext (already connected by LiveKit Agents framework)
    await ctx.connect()
    logger.info("✅ Connected to room via JobContext")
    
    # Don't wait for participant - LiveKitTransport will handle connections automatically
    # The pipeline will start processing audio as soon as participants join
    
    # Generate Token for the bot to join (for Pipecat transport)
    token = api.AccessToken(
        settings.LIVEKIT_API_KEY, 
        settings.LIVEKIT_API_SECRET
    ).with_identity("hindi_agent") \
    .with_name("Hindi Agent") \
    .with_grants(api.VideoGrants(room_join=True, room=ctx.room.name)) \
    .to_jwt()
    
    # Transport Setup - Pipecat's LiveKitTransport will create its own connection
    # This is fine - it will connect to the same room
    logger.info("🔧 Setting up Pipecat transport...")
    transport = LiveKitTransport(
        url=settings.LIVEKIT_URL,
        token=token,
        room_name=ctx.room.name,  # Use the room name from JobContext
        params=LiveKitParams(
            audio_in_enabled=True,
            audio_in_sample_rate=16000,  # Downsample LiveKit input to Sarvam's expected 16 kHz
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=create_vad(),
            transcription_enabled=False
        )
    )
    
    stt = create_stt(settings.SARVAM_API_KEY)
    llm = create_llm()
    tts = create_tts(settings.SARVAM_API_KEY)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = OpenAILLMContext(messages=messages)
    aggregator = LLMUserContextAggregator(context)
    
    latency_logger = LatencyLogger()
    
    pipeline = Pipeline([
        transport.input(),
        latency_logger,
        stt,
        aggregator,  # LLMUserContextAggregator processes frames directly
        llm,
        tts,
        transport.output()
    ])
    
    task = PipelineTask(pipeline)
    # Do not queue context as frame, it's managed by aggregator
    runner = PipelineRunner()
    
    logger.info("Starting pipeline...")
    await runner.run(task)


if __name__ == "__main__":
    # The worker connects to LiveKit Cloud using environment variables
    # Make sure LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET are set
    # The worker will automatically receive job dispatches when rooms are created
    logger.info(f"Starting LiveKit Agent Worker")
    logger.info(f"Connecting to: {settings.LIVEKIT_URL}")
    
    # IMPORTANT: Don't set agent_name if you want automatic dispatch!
    # Setting agent_name turns OFF automatic dispatch and requires explicit dispatch
    # For automatic dispatch (agent joins all rooms automatically), don't set agent_name
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Don't set request_fnc - default behavior accepts all jobs
            # Leave agent_name unset for automatic dispatch to all rooms
        )
    )
