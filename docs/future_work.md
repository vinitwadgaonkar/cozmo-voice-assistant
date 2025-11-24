# Future Work

1. **Local STT/TTS**: Explore using NVIDIA Rivad or local Whisper-v3-turbo on GPU for 0-latency network overhead.
2. **Function Calling**: Add tool use for the agent (calendar, weather).
3. **Phone Integration**: SIP trunking via LiveKit SIP.
4. **Better VAD**: Implement WebRTC VAD on client side to detect EOS faster than server-side silence detection.
5. **Caching**: Cache common responses (greetings, fillers) as raw PCM audio for 0ms latency.

