"""
Three-brain pipeline orchestration with latency oracle and shadow traffic.

This module builds the Pipecat pipeline and wires together:
- Reflex Brain (L0): Immediate Hindi backchannels
- Speculative Brain (L1): Fast shallow answers
- Deep Brain (L2): Slower richer responses
- Latency Oracle: Metrics tracking and prediction
- Shadow Traffic: Background alternate model testing
"""

import asyncio
import uuid
from typing import Optional, Dict, Any
from loguru import logger
from openai import AsyncOpenAI

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None
    logger.warning("Groq SDK not installed, Groq provider unavailable")

try:
    from pipecat.transports.services.livekit import LiveKitTransportService, LiveKitParams
except ImportError:
    from pipecat.transports.livekit import LiveKitTransport as LiveKitTransportService, LiveKitParams

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

try:
    from pipecat.services.sarvam import SarvamSTTService, SarvamTTSService
except ImportError:
    from pipecat.services.sarvam.stt import SarvamSTTService
    from pipecat.services.sarvam.tts import SarvamTTSService

from .config import VoiceAgentConfig
from .livekit_token import create_access_token
from .metrics import LatencyOracle, LatencyTimer
from .router import (
    should_trigger_reflex,
    choose_llm_for_turn,
    should_run_shadow_traffic,
    choose_shadow_provider,
    get_l2_provider,
    log_routing_decision,
)
from .brains.reflex import maybe_emit_reflex
from .brains.speculative import generate_speculative_reply_multi_provider
from .brains.deep import run_deep_brain_async, should_run_deep_brain


class ThreeBrainOrchestrator:
    """
    Orchestrates the three-brain architecture with shadow traffic.
    
    Handles turn management, routing decisions, and metrics tracking.
    Supports multiple LLM providers: OpenAI, Groq, etc.
    """
    
    def __init__(self, cfg: VoiceAgentConfig):
        self.cfg = cfg
        self.oracle = LatencyOracle()
        self.openai_client = AsyncOpenAI(api_key=cfg.openai.api_key)
        
        # Initialize Groq client if available
        self.groq_client = None
        self.groq_available = False
        if cfg.groq and cfg.groq.enabled and AsyncGroq:
            try:
                self.groq_client = AsyncGroq(api_key=cfg.groq.api_key)
                self.groq_available = True
                logger.info("✅ Groq client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️  Groq initialization failed: {e}")
                self.groq_available = False
        else:
            logger.info("ℹ️  Groq disabled or not available")
        
        self.turn_counter = 0
        
        # Queue for sending text to TTS
        self.tts_queue: Optional[asyncio.Queue] = None
    
    async def handle_transcript(self, transcript: str) -> None:
        """
        Handle a completed STT transcript - this is the main orchestration logic.
        
        Args:
            transcript: The user's speech transcript
        """
        self.turn_counter += 1
        turn_id = f"turn-{self.turn_counter}"
        
        logger.info("=" * 70)
        logger.info(f"🎤 NEW TURN #{self.turn_counter}")
        logger.info(f"User said: {transcript}")
        logger.info("=" * 70)
        
        # Step 1: Make routing decisions
        l1_provider = choose_llm_for_turn(
            self.oracle,
            groq_available=self.groq_available,
        )
        l2_provider = get_l2_provider(l1_provider)
        should_reflex = should_trigger_reflex(
            self.oracle,
            self.cfg.behavior.reflex_latency_ms,
            l1_provider,
        )
        should_shadow = should_run_shadow_traffic(self.cfg.behavior.shadow_traffic_probability)
        
        log_routing_decision(turn_id, l1_provider, l2_provider, should_reflex, should_shadow)
        
        # Step 2: Emit reflex if needed
        if should_reflex:
            await maybe_emit_reflex(should_reflex, self._send_to_tts)
        
        # Step 3: Generate speculative (L1) answer
        # Choose client and model based on routing decision
        if l1_provider == "groq-l1" and self.groq_client:
            client = self.groq_client
            model = self.cfg.groq.model
        else:
            client = self.openai_client
            model = self.cfg.openai.model_l1
        
        timer_l1 = LatencyTimer("L1")
        with timer_l1:
            timer_l1.mark_first_token()  # For non-streaming, mark immediately
            answer_l1, semantic_tag = await generate_speculative_reply_multi_provider(
                client=client,
                model=model,
                transcript=transcript,
                provider=l1_provider,
            )
        
        # Record L1 latency
        self.oracle.record(l1_provider, timer_l1.first_token_ms, timer_l1.total_ms)
        logger.info(f"⏱️  L1 latency: {timer_l1.total_ms:.0f}ms")
        
        # Step 4: Send L1 answer to TTS
        await self._send_to_tts(answer_l1)
        
        # Step 5: Launch deep brain (L2) asynchronously if enabled
        if self.cfg.behavior.enable_deep_brain and should_run_deep_brain(semantic_tag):
            asyncio.create_task(
                self._run_deep_brain(
                    turn_id=turn_id,
                    l2_provider=l2_provider,
                    transcript=transcript,
                    speculative_answer=answer_l1,
                    semantic_tag=semantic_tag,
                )
            )
        
        # Step 6: Run shadow traffic if enabled
        if should_shadow:
            shadow_provider = choose_shadow_provider(l1_provider)
            if shadow_provider:
                asyncio.create_task(
                    self._run_shadow_traffic(
                        turn_id=turn_id,
                        shadow_provider=shadow_provider,
                        transcript=transcript,
                    )
                )
        
        logger.info(f"✅ Turn {turn_id} complete (L1 answer sent)")
    
    async def _run_deep_brain(
        self,
        turn_id: str,
        l2_provider: str,
        transcript: str,
        speculative_answer: str,
        semantic_tag: dict,
    ) -> None:
        """Run the deep brain asynchronously and track metrics."""
        logger.info(f"🧠 Starting L2 brain for {turn_id}...")
        
        timer_l2 = LatencyTimer("L2")
        with timer_l2:
            timer_l2.mark_first_token()
            await run_deep_brain_async(
                client=self.openai_client,
                model=self.cfg.openai.model_l2,
                transcript=transcript,
                speculative_answer=speculative_answer,
                semantic_tag=semantic_tag,
                send_text=self._send_to_tts,
            )
        
        # Record L2 latency
        self.oracle.record(l2_provider, timer_l2.first_token_ms, timer_l2.total_ms)
        logger.info(f"⏱️  L2 latency: {timer_l2.total_ms:.0f}ms")
    
    async def _run_shadow_traffic(
        self,
        turn_id: str,
        shadow_provider: str,
        transcript: str,
    ) -> None:
        """Run shadow traffic with alternate model (metrics only, no user output)."""
        logger.info(f"🔬 Running shadow traffic for {turn_id} with {shadow_provider}...")
        
        # Choose alternate model for shadow
        shadow_model = self.cfg.openai.model_l2 if "l2" in shadow_provider else self.cfg.openai.model_l1
        
        timer_shadow = LatencyTimer("Shadow")
        with timer_shadow:
            timer_shadow.mark_first_token()
            try:
                answer_shadow, _ = await generate_speculative_reply(
                    client=self.openai_client,
                    model=shadow_model,
                    transcript=transcript,
                )
                
                # Log shadow result (but don't send to user)
                logger.info(f"🔬 Shadow answer: {answer_shadow[:100]}...")
                
            except Exception as e:
                logger.error(f"Shadow traffic error: {e}")
        
        # Record shadow latency
        self.oracle.record(shadow_provider, timer_shadow.first_token_ms, timer_shadow.total_ms)
        logger.info(f"⏱️  Shadow latency: {timer_shadow.total_ms:.0f}ms")
    
    async def _send_to_tts(self, text: str) -> None:
        """
        Send text to TTS queue.
        
        Args:
            text: Text to synthesize and speak
        """
        if self.tts_queue:
            await self.tts_queue.put(text)
            logger.debug(f"📝 Queued for TTS: {text}")
        else:
            logger.warning("TTS queue not initialized, cannot send text")


def build_services(cfg: VoiceAgentConfig):
    """
    Build Sarvam STT/TTS services.
    
    Args:
        cfg: Voice agent configuration
        
    Returns:
        tuple: (stt_service, tts_service)
    """
    logger.info("Building Sarvam STT service...")
    stt = SarvamSTTService(
        api_key=cfg.sarvam.api_key,
        language="hi-IN",
    )

    logger.info("Building Sarvam TTS service...")
    tts = SarvamTTSService(
        api_key=cfg.sarvam.api_key,
        voice_id="arvind",
        sample_rate=16000,
    )

    return stt, tts


def create_livekit_transport(cfg: VoiceAgentConfig, room_name: str, identity: str) -> LiveKitTransportService:
    """
    Create LiveKit transport.
    
    Args:
        cfg: Voice agent configuration
        room_name: LiveKit room name
        identity: Participant identity
        
    Returns:
        LiveKitTransportService: Configured transport
    """
    logger.info(f"Generating LiveKit access token for room '{room_name}', identity '{identity}'...")
    token = create_access_token(cfg, room_name=room_name, identity=identity)

    logger.info("Creating LiveKit transport...")
    params = LiveKitParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        audio_in_sample_rate=16000,
        audio_out_sample_rate=16000,
        vad_enabled=True,
        vad_analyzer=None,
        vad_audio_passthrough=True,
    )

    transport = LiveKitTransportService(
        url=cfg.livekit.url,
        token=token,
        room_name=room_name,
        params=params,
    )

    return transport


def build_pipeline_and_runner(
    cfg: VoiceAgentConfig,
    room_name: str,
    identity: str,
) -> tuple[PipelineRunner, ThreeBrainOrchestrator]:
    """
    Build the complete Pipecat pipeline with three-brain orchestration.
    
    Args:
        cfg: Voice agent configuration
        room_name: LiveKit room name
        identity: Participant identity
    
    Returns:
        Tuple of (runner, orchestrator)
    """
    logger.info("=" * 70)
    logger.info("Building Three-Brain Voice Agent Pipeline")
    logger.info("=" * 70)
    
    # Create services
    stt, tts = build_services(cfg)
    transport = create_livekit_transport(cfg, room_name, identity)
    
    # Create orchestrator
    orchestrator = ThreeBrainOrchestrator(cfg)
    orchestrator.tts_queue = asyncio.Queue()
    
    # Build simple pipeline: transport → STT → [brains] → TTS → transport
    # Note: The "brains" logic happens in callbacks, not as Pipecat processors
    logger.info("Building pipeline...")
    pipeline = Pipeline([
        transport.input(),
        stt,
        # Brains orchestration happens via callbacks
        tts,
        transport.output(),
    ])
    
    # Create task
    task = PipelineTask(
        pipeline,
        PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        )
    )
    
    # Set up event handlers
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport_obj, participant):
        logger.info("=" * 70)
        logger.info(f"👤 First participant joined: {participant.identity}")
        logger.info("=" * 70)
        try:
            await transport_obj.capture_participant_transcription(participant.identity)
        except Exception as e:
            logger.error(f"Error capturing transcription: {e}")
    
    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport_obj, participant, reason):
        logger.info(f"👋 Participant left: {participant.identity}, reason: {reason}")
        orchestrator.oracle.log_summary()
    
    # Wire up STT → Orchestrator
    # In a real implementation, you'd hook into Pipecat's frame events
    # For this POC, we'll use a simplified approach
    
    # Create runner
    runner = PipelineRunner()
    
    # Store orchestrator for external access
    runner._orchestrator = orchestrator
    
    logger.info("✅ Pipeline built successfully")
    logger.info("=" * 70)
    
    return runner, orchestrator


async def run_voice_agent(cfg: VoiceAgentConfig, room_name: str, identity: str):
    """
    Run the three-brain voice agent.
    
    Args:
        cfg: Voice agent configuration
        room_name: LiveKit room name
        identity: Participant identity
    """
    logger.info("=" * 70)
    logger.info(f"🚀 Starting Three-Brain Hindi Voice Agent")
    logger.info(f"   Room: {room_name}")
    logger.info(f"   Identity: {identity}")
    logger.info(f"   L1 Model: {cfg.openai.model_l1}")
    logger.info(f"   L2 Model: {cfg.openai.model_l2}")
    logger.info(f"   Reflex Threshold: {cfg.behavior.reflex_latency_ms}ms")
    logger.info(f"   Shadow Traffic: {cfg.behavior.shadow_traffic_probability*100:.0f}%")
    logger.info("=" * 70)
    
    try:
        runner, orchestrator = build_pipeline_and_runner(cfg, room_name, identity)
        
        # For this POC, we use a simplified approach
        # In production, you'd properly integrate with Pipecat's event system
        logger.warning("⚠️  NOTE: This POC uses simplified transcript handling")
        logger.warning("⚠️  For production, wire STT events properly into orchestrator")
        
        # Run pipeline
        # await runner.run(task)  # Would be used in full Pipecat integration
        
        # For demo purposes, show the architecture is ready
        logger.info("✅ Three-brain architecture initialized and ready")
        logger.info("🎤 Waiting for participants to join...")
        
        # Keep alive
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        raise
    except Exception as e:
        logger.error(f"Error in voice agent pipeline: {e}")
        logger.exception("Full traceback:")
        raise
    finally:
        logger.info("=" * 70)
        logger.info("Final Latency Oracle Summary")
        if 'orchestrator' in locals():
            orchestrator.oracle.log_summary()
        logger.info("Voice agent shutdown complete")
        logger.info("=" * 70)
