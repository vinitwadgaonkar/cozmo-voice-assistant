from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

def create_vad():
    # ULTRA-AGGRESSIVE VAD for sub-150ms latency
    # Reduced stop_secs to absolute minimum for fastest turn-taking
    return SileroVADAnalyzer(
        params=VADParams(
            start_secs=0.15,  # Faster start detection
            stop_secs=0.15,   # Ultra-fast stop (was 0.20)
            confidence=0.5,   # Lower threshold for faster detection
            min_volume=0.4    # Lower volume threshold
        )
    )

