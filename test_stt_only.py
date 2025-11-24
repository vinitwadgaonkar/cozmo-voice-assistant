import asyncio
import wave
import sys
from loguru import logger
from pipecat.frames.frames import AudioRawFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame, EndFrame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.processors.frame_processor import FrameProcessor
from server.config import settings
from server.services.sarvam_services import create_stt

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level="DEBUG")

class PrinterSink(FrameProcessor):
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            logger.success(f"📝 STT Transcript: '{frame.text}'")

async def main():
    logger.info("🚀 Testing STT Only")
    
    stt = create_stt(settings.SARVAM_API_KEY)
    sink = PrinterSink()
    
    pipeline = Pipeline([stt, sink])
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    async def feed_audio():
        await asyncio.sleep(1)
        logger.info("▶️  Playing audio...")
        # Simulate VAD start
        await task.queue_frame(UserStartedSpeakingFrame())
        
        with wave.open("samples/hindi_01.wav", 'rb') as wf:
            chunk_size = 1024
            while True:
                data = wf.readframes(chunk_size)
                if len(data) == 0: break
                await task.queue_frame(AudioRawFrame(audio=data, sample_rate=16000, num_channels=1))
                await asyncio.sleep(0.01)
        
        logger.info("⏹️  Audio finished")
        # Simulate VAD stop
        await task.queue_frame(UserStoppedSpeakingFrame())
        
        await asyncio.sleep(5)
        await task.queue_frame(EndFrame())

    await asyncio.gather(runner.run(task), feed_audio())

if __name__ == "__main__":
    asyncio.run(main())

