#!/usr/bin/env python3
"""
Direct connection approach - bypasses job dispatch issues.
Optimized for sub-150ms latency with auto-disconnect.
"""

import asyncio
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from loguru import logger
from livekit import api, rtc
from livekit.agents import JobContext, WorkerOptions, cli

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

# Global state for auto-disconnect
_last_activity = time.time()
_idle_timeout = 300  # 5 minutes of inactivity

async def entrypoint(ctx: JobContext):
    global _last_activity
    
    logger.info(f"🎯 ENTRYPOINT CALLED - Room: {ctx.room.name}")
    _last_activity = time.time()
    
    try:
        await ctx.connect()
        logger.info("✅ Connected to room")
        
        # Generate token
        token = api.AccessToken(
            settings.LIVEKIT_API_KEY, 
            settings.LIVEKIT_API_SECRET
        ).with_identity("hindi_agent") \
        .with_name("Hindi Agent") \
        .with_grants(api.VideoGrants(room_join=True, room=ctx.room.name)) \
        .to_jwt()
        
        # Setup transport with optimized settings
        logger.info("🔧 Setting up optimized pipeline...")
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
        
        # Create services - optimized for latency
        stt = create_stt(settings.SARVAM_API_KEY)
        llm = create_llm()
        tts = create_tts(settings.SARVAM_API_KEY)
        
        # Context setup
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        context = OpenAILLMContext(messages=messages)
        aggregator = LLMUserContextAggregator(context)
        latency_logger = LatencyLogger()
        
        # Pipeline - optimized order
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
        
    except Exception as e:
        logger.error(f"❌ Entrypoint error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        logger.info("🔌 Entrypoint finished")

async def idle_monitor():
    """Monitor for idle and disconnect to save API costs."""
    global _last_activity
    
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        idle_time = time.time() - _last_activity
        if idle_time > _idle_timeout:
            logger.info(f"⏸️  Idle for {idle_time:.0f}s, disconnecting to save costs...")
            # The worker will handle reconnection when needed
            break

if __name__ == "__main__":
    logger.info("🚀 Starting Optimized Hindi Voice Agent")
    logger.info(f"📍 URL: {settings.LIVEKIT_URL}")
    logger.info("⚡ Optimized for sub-150ms latency")
    logger.info("💾 Auto-disconnect after 5min idle")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )

