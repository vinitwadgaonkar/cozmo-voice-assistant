import sys
import asyncio
from loguru import logger

# Pipecat imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_response import LLMUserContextAggregator
from pipecat.frames.frames import LLMMessagesFrame, EndFrame

# LiveKit Transport (Pipecat's built-in wrapper for LiveKit)
from pipecat.transports.services.livekit import LiveKitTransport, LiveKitParams

# Custom components
from server.config import settings
from server.services.sarvam_stt import SarvamSTTService
from server.services.sarvam_tts import SarvamTTSService
from server.services.llm import create_llm, SYSTEM_PROMPT
from server.utils.vad import create_vad

async def run_pipeline():
    logger.info("Starting Hindi Voice Agent Pipeline")

    # 1. Transport Setup
    # We use Pipecat's LiveKitTransport which handles the WebRTC connection
    transport = LiveKitTransport(
        url=settings.LIVEKIT_URL,
        token=settings.LIVEKIT_TOKEN, # Or generated from API Key/Secret in Main
        params=LiveKitParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True, # We will provide the analyzer
            vad_analyzer=create_vad(),
            transcription_enabled=False # We use our own Sarvam STT
        )
    )

    # 2. Services Setup
    stt = SarvamSTTService(
        api_key=settings.SARVAM_API_KEY,
        url=settings.SARVAM_STT_URL,
        language="hi-IN"
    )

    llm = create_llm()

    tts = SarvamTTSService(
        api_key=settings.SARVAM_API_KEY,
        url=settings.SARVAM_TTS_URL,
        voice_id="anushka",
        model="bulbul:v2"
    )

    # 3. Context Aggregator
    # Manages conversation history context for the LLM
    context_aggregator = LLMUserContextAggregator(context=None) # Can inject initial context
    
    # Initial System Message
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    user_context = LLMMessagesFrame(messages=messages)


    # 4. Pipeline Definition
    # Flow: Input -> STT -> Context Aggregator -> LLM -> TTS -> Output
    pipeline = Pipeline([
        transport.input(),      # Microphone Audio
        stt,                    # Audio -> Text
        context_aggregator.user(), # Text -> LLM Context
        llm,                    # Context -> Text Stream
        tts,                    # Text Stream -> Audio Stream
        transport.output()      # Audio Stream -> Speaker
    ])

    # 5. Runner
    task = PipelineTask(pipeline)
    
    # Push initial context
    await task.queue_frame(user_context)

    runner = PipelineRunner()
    
    # Run
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(run_pipeline())

