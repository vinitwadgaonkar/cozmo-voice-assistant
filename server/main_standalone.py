#!/usr/bin/env python3
"""
Standalone agent - connects directly to rooms without job dispatch.
Optimized for sub-150ms latency.
"""

import asyncio
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from loguru import logger
from livekit import api, rtc
from livekit.agents import auto_connect, RoomContext

from server.config import settings
from pipecat.transports.services.livekit import LiveKitTransport, LiveKitParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_response import LLMUserContextAggregator
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

from server.services.sarvam_services import create_stt, create_tts
from server.services.llm import create_llm, SYSTEM_PROMPT
from server.utils.vad import create_vad
from server.utils.latency_logger import LatencyLogger

async def on_participant_connected(ctx: RoomContext):
    """Called when a participant connects - start pipeline immediately."""
    logger.info(f"👤 Participant connected: {ctx.participant.identity}")
    
    # Generate token for agent
    token = api.AccessToken(
        settings.LIVEKIT_API_KEY, 
        settings.LIVEKIT_API_SECRET
    ).with_identity("hindi_agent") \
    .with_name("Hindi Agent") \
    .with_grants(api.VideoGrants(room_join=True, room=ctx.room.name)) \
    .to_jwt()
    
    # Setup transport
    logger.info("🔧 Setting up pipeline...")
    transport = LiveKitTransport(
        url=settings.LIVEKIT_URL,
        token=token,
        room_name=ctx.room.name,
        params=LiveKitParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=create_vad(),
            transcription_enabled=False
        )
    )
    
    # Create services
    stt = create_stt(settings.SARVAM_API_KEY)
    llm = create_llm()
    tts = create_tts(settings.SARVAM_API_KEY)
    
    # Context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = OpenAILLMContext(messages=messages)
    aggregator = LLMUserContextAggregator(context)
    latency_logger = LatencyLogger()
    
    # Pipeline
    pipeline = Pipeline([
        transport.input(),
        latency_logger,
        stt,
        aggregator,
        llm,
        tts,
        transport.output()
    ])
    
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    logger.info("🚀 Starting pipeline...")
    await runner.run(task)

if __name__ == "__main__":
    logger.info("🚀 Starting Standalone Hindi Voice Agent")
    logger.info(f"📍 URL: {settings.LIVEKIT_URL}")
    logger.info("⚡ Optimized for sub-150ms latency")
    
    # Use auto_connect to monitor rooms and connect when participants join
    auto_connect(
        settings.LIVEKIT_URL,
        settings.LIVEKIT_API_KEY,
        settings.LIVEKIT_API_SECRET,
        participant_connected=on_participant_connected,
    )

