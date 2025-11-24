import asyncio
import wave
import sys
from loguru import logger

# Pipecat imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.aggregators.llm_response import LLMUserContextAggregator
from pipecat.frames.frames import (
    LLMMessagesFrame, EndFrame, AudioRawFrame, TextFrame, TranscriptionFrame,
    UserStartedSpeakingFrame, UserStoppedSpeakingFrame
)
from pipecat.processors.frame_processor import FrameProcessor

# Service imports
from server.config import settings
from server.services.sarvam_services import create_stt, create_tts
from server.services.llm import create_llm, SYSTEM_PROMPT

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level="DEBUG")

async def audio_source(filepath):
    """Reads wav file and yields AudioRawFrames"""
    with wave.open(filepath, 'rb') as wf:
        chunk_size = 1024 # Larger chunks
        while True:
            data = wf.readframes(chunk_size)
            if len(data) == 0:
                break
            yield AudioRawFrame(audio=data, sample_rate=16000, num_channels=1)
            await asyncio.sleep(0.02) 

class AudioWriterSink(FrameProcessor):
    def __init__(self, output_filename="output_response.wav"):
        super().__init__()
        self.output_filename = output_filename
        self.audio_data = bytearray()
        self.received_stt = False
        self.received_llm = False
        self.received_tts = False
        
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TranscriptionFrame):
            logger.success(f"📝 STT Transcript: '{frame.text}'")
            self.received_stt = True
            
        elif isinstance(frame, TextFrame):
            logger.success(f"🤖 LLM Response: '{frame.text}'")
            self.received_llm = True
            
        elif isinstance(frame, AudioRawFrame):
            if not self.received_tts:
                logger.success("🔊 First TTS Audio Chunk Received!")
            self.received_tts = True
            self.audio_data.extend(frame.audio)

    def save_audio(self):
        if not self.audio_data:
            logger.warning("No audio data to save.")
            return
            
        logger.info(f"💾 Saving output audio to {self.output_filename}...")
        try:
            with wave.open(self.output_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(24000) # Sarvam TTS output rate
                wf.writeframes(self.audio_data)
            logger.success(f"✅ Audio saved successfully: {self.output_filename}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")

async def main():
    logger.info("🚀 Starting Automated Pipeline Simulation")
    logger.info(f"📂 Input: samples/hindi_01.wav")
    
    try:
        stt = create_stt(settings.SARVAM_API_KEY)
        llm = create_llm()
        tts = create_tts(settings.SARVAM_API_KEY)
    except Exception as e:
        logger.error(f"Failed to create services: {e}")
        return

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = LLMMessagesFrame(messages=messages)
    aggregator = LLMUserContextAggregator(context)
    sink = AudioWriterSink("output_response.wav")
    
    # No VAD processor - we will manually signal speech start/stop
    pipeline = Pipeline([
        stt,
        aggregator,
        llm,
        tts,
        sink
    ])
    
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    await task.queue_frame(context)
    
    async def feed_audio():
        await asyncio.sleep(2) # Warmup
        
        logger.info("🗣️  User Started Speaking (Manual Signal)")
        await task.queue_frame(UserStartedSpeakingFrame())
        
        logger.info("▶️  Playing audio...")
        async for frame in audio_source("samples/hindi_01.wav"):
            await task.queue_frame(frame)
        logger.info("⏹️  Audio finished")
        
        logger.info("🤫 User Stopped Speaking (Manual Signal)")
        await task.queue_frame(UserStoppedSpeakingFrame())
        
        logger.info("⏳ Waiting for response...")
        # Wait loop
        for _ in range(150): 
            if sink.received_tts and len(sink.audio_data) > 50000: # Wait for substantial audio
                break
            await asyncio.sleep(0.1)
            
        if sink.received_tts:
            logger.success("✅ Pipeline Test Passed: Audio -> STT -> LLM -> TTS -> Audio")
        else:
            logger.error("❌ Pipeline Test Failed: No TTS output received")
        
        await task.queue_frame(EndFrame())
        sink.save_audio()

    await asyncio.gather(
        runner.run(task),
        feed_audio()
    )

if __name__ == "__main__":
    asyncio.run(main())
