#!/usr/bin/env python3
"""
Generate a Hindi speech sample using Sarvam TTS and save it to samples/hindi_01.wav.
"""

import asyncio
import wave
from pathlib import Path
import sys

from loguru import logger

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipecat.frames.frames import (
    AudioRawFrame,
    EndFrame,
    Frame,
    StartFrame,
    TextFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from server.config import settings
from server.services.sarvam_services import create_tts


SAMPLE_PATH = Path("samples/hindi_01.wav")
SAMPLE_TEXT = (
    "नमस्ते! मैं आपका तेज़ हिंदी सहायक हूँ। "
    "मैं कुछ वाक्यों के जरिए नमूना ऑडियो तैयार कर रहा हूँ। "
    "इस फ़ाइल को डीपग्राम स्ट्रीमिंग टेस्ट के लिए इस्तेमाल करें।"
)


class TextSource(FrameProcessor):
    """Pushes a Hindi TextFrame when the pipeline starts."""

    def __init__(self, text: str):
        super().__init__()
        self._text = text
        self._sent = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame) and not self._sent:
            self._sent = True
            await self.push_frame(TextFrame(text=self._text))
            # Signal no more text
            await self.push_frame(EndFrame())


class AudioFileSink(FrameProcessor):
    """Collects AudioRawFrames and writes them to a WAV file."""

    def __init__(self, output_path: Path, sample_rate: int = 16000):
        super().__init__()
        self._output_path = output_path
        self._sample_rate = sample_rate
        self._audio_buffer = bytearray()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, AudioRawFrame):
            self._audio_buffer.extend(frame.audio)
        elif isinstance(frame, EndFrame):
            await self._write_wav()

    async def _write_wav(self):
        if not self._audio_buffer:
            logger.warning("No audio received; skipping file write.")
            return

        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(self._output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(bytes(self._audio_buffer))

        logger.success(f"✅ Saved Hindi sample to {self._output_path}")


async def generate_sample():
    logger.info("🎙️ Generating Hindi sample via Sarvam TTS...")

    tts_service = create_tts(settings.SARVAM_API_KEY)
    source = TextSource(SAMPLE_TEXT)
    sink = AudioFileSink(SAMPLE_PATH)

    pipeline = Pipeline([source, tts_service, sink])
    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    # Kick off the pipeline
    await task.queue_frame(StartFrame())
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(generate_sample())

