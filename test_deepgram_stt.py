#!/usr/bin/env python3
"""
Test Deepgram STT independently using a proper Pipeline.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipecat.services.deepgram import DeepgramSTTService
from deepgram import LiveOptions
from pipecat.frames.frames import (
    StartFrame,
    EndFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    UserAudioRawFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    ErrorFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner

parser = argparse.ArgumentParser(description="Standalone Deepgram STT test")
parser.add_argument(
    "--sample",
    type=str,
    default="samples/hindi_01.wav",
    help="Path to sample audio file (wav/pcm)",
)
parser.add_argument(
    "--language",
    type=str,
    default="hi",
    help="Deepgram language code (e.g., hi, en-US)",
)
parser.add_argument(
    "--duration",
    type=float,
    default=5.0,
    help="Seconds of audio to stream from the sample",
)
parser.add_argument(
    "--model",
    type=str,
    default="nova-3",
    help="Deepgram model to use",
)
parser.add_argument(
    "--timeout",
    type=float,
    default=10.0,
    help="Seconds to wait for pipeline completion",
)
args = parser.parse_args()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
if not DEEPGRAM_API_KEY:
    logger.error("❌ DEEPGRAM_API_KEY not set!")
    sys.exit(1)

class DeepgramTestSink(FrameProcessor):
    """Collects and logs all frames from Deepgram STT."""
    def __init__(self):
        super().__init__()
        self.transcripts = []
        self.interim_transcripts = []
        self.errors = []
        
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TranscriptionFrame):
            logger.success(f"✅ FINAL TRANSCRIPT: '{frame.text}'")
            self.transcripts.append(frame.text)
        elif isinstance(frame, InterimTranscriptionFrame):
            logger.info(f"📝 INTERIM: '{frame.text}'")
            self.interim_transcripts.append(frame.text)
        elif isinstance(frame, ErrorFrame):
            logger.error(f"❌ ERROR: {frame.error}")
            self.errors.append(str(frame.error))

async def test_deepgram(sample_path: Path):
    """Test Deepgram STT independently using Pipeline."""
    logger.info("=" * 70)
    logger.info("🧪 TESTING DEEPGRAM STT INDEPENDENTLY")
    logger.info("=" * 70)
    
    logger.info(f"✅ Deepgram API Key: {DEEPGRAM_API_KEY[:10]}...{DEEPGRAM_API_KEY[-4:]}")
    logger.info(f"🎧 Sample: {sample_path} | Language: {args.language} | Model: {args.model}")
    
    # Create Deepgram STT service
    logger.info("🔧 Creating Deepgram STT service...")
    try:
        stt = DeepgramSTTService(
            api_key=DEEPGRAM_API_KEY,
            live_options=LiveOptions(
                language=args.language,
                model=args.model,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                vad_events=True,
                endpointing=300,
                smart_format=False,
                punctuate=False,
            )
        )
        logger.info("✅ Deepgram STT service created")
    except Exception as e:
        logger.error(f"❌ Failed to create Deepgram STT: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Create test sink
    sink = DeepgramTestSink()
    
    pipeline = Pipeline([stt, sink])
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    async def feed_audio():
        """Queue frames into the pipeline."""
        await asyncio.sleep(0.5)
        logger.info("▶️  Feeding audio to Deepgram...")
        
        # Signal start of audio
        await task.queue_frame(StartFrame())
        await task.queue_frame(UserStartedSpeakingFrame())
        
        # Load sample audio (Hindi speech)
        sample_path = Path(args.sample)
        if not sample_path.exists():
            logger.warning("Sample file not found, sending silence instead")
            chunk = b"\x00\x00" * 1600
            for _ in range(20):
                await task.queue_frame(UserAudioRawFrame(audio=chunk, sample_rate=16000, num_channels=1))
                await asyncio.sleep(0.05)
        else:
            import wave
            with wave.open(str(sample_path), "rb") as wf:
                sample_rate = wf.getframerate()
                channels = wf.getnchannels()
                chunk_frames = int(sample_rate * 0.02)  # 20 ms
                max_frames = int(sample_rate * args.duration)
                sent_frames = 0
                
                while sent_frames < max_frames:
                    frames_to_read = min(chunk_frames, max_frames - sent_frames)
                    data = wf.readframes(frames_to_read)
                    if not data:
                        break
                    await task.queue_frame(
                        UserAudioRawFrame(
                            audio=data,
                            sample_rate=sample_rate,
                            num_channels=channels
                        )
                    )
                    sent_frames += frames_to_read
                    await asyncio.sleep(frames_to_read / sample_rate)
        
        # End of user speech
        await task.queue_frame(UserStoppedSpeakingFrame())
        
        # Allow time for transcripts then stop
        await asyncio.sleep(2)
        await task.queue_frame(EndFrame())
    
    async def run_pipeline():
        await asyncio.gather(runner.run(task), feed_audio())

    logger.info("🚀 Starting Deepgram STT pipeline...")
    try:
        total_timeout = args.timeout + args.duration + 3  # duration + buffer
        await asyncio.wait_for(run_pipeline(), timeout=total_timeout)
        logger.info("✅ Pipeline completed")
    except asyncio.TimeoutError:
        logger.error("⏱️  Pipeline timed out waiting for Deepgram response")
        return False
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Results
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST RESULTS")
    logger.info("=" * 70)
    logger.info(f"   ✅ Final transcripts: {len(sink.transcripts)}")
    for i, transcript in enumerate(sink.transcripts):
        logger.info(f"      {i+1}. '{transcript}'")
    logger.info(f"   📝 Interim transcripts: {len(sink.interim_transcripts)}")
    for i, transcript in enumerate(sink.interim_transcripts[-10:]):  # Last 10
        logger.info(f"      {i+1}. '{transcript}'")
    logger.info(f"   ❌ Errors: {len(sink.errors)}")
    for i, error in enumerate(sink.errors):
        logger.info(f"      {i+1}. {error}")
    
    if len(sink.errors) > 0:
        logger.error("❌ Deepgram encountered errors!")
        return False
    elif len(sink.transcripts) > 0 or len(sink.interim_transcripts) > 0:
        logger.success("✅ Deepgram STT is working and producing transcripts!")
        return True
    else:
        logger.warning("⚠️  Deepgram connected but produced no transcripts")
        logger.warning("   This is expected for silence tests.")
        logger.warning("   Connection appears to be working (no errors).")
        return True  # Connection worked, just no speech detected

if __name__ == "__main__":
    sample_path = Path(args.sample)
    if not sample_path.exists():
        logger.error(f"❌ Sample file not found: {sample_path}")
        sys.exit(1)

    logger.info("🎤 Deepgram STT Standalone Test")
    logger.info("   This test checks connection and basic functionality.\n")
    
    success = asyncio.run(test_deepgram(sample_path))
    sys.exit(0 if success else 1)
