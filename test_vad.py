import asyncio
import wave
import sys
from loguru import logger
from pipecat.frames.frames import AudioRawFrame
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams, VADState

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>", level="DEBUG")

async def main():
    logger.info("🚀 Testing VAD on file")
    analyzer = SileroVADAnalyzer(params=VADParams(
        start_secs=0.2, 
        stop_secs=0.5, 
        confidence=0.3, # Lowered confidence
        min_volume=0.0  # Removed volume check
    ))
    
    with wave.open("samples/hindi_01.wav", 'rb') as wf:
        chunk_size = 512
        triggered = False
        while True:
            data = wf.readframes(chunk_size)
            if len(data) == 0:
                break
            frame = AudioRawFrame(audio=data, sample_rate=16000, num_channels=1)
            status = await analyzer.analyze(frame)
            if status == VADState.STARTING:
                logger.success("🗣️ VAD START DETECTED!")
                triggered = True
            elif status == VADState.STOPPING:
                logger.success("🤫 VAD STOP DETECTED!")
                
        # Send silence
        logger.info("Sending silence...")
        for _ in range(20):
            silence = b'\x00' * 1024
            frame = AudioRawFrame(audio=silence, sample_rate=16000, num_channels=1)
            status = await analyzer.analyze(frame)
            if status == VADState.STOPPING:
                 logger.success("🤫 VAD STOP DETECTED (during silence)!")

    if not triggered:
        logger.error("❌ VAD never triggered on file")

if __name__ == "__main__":
    asyncio.run(main())

