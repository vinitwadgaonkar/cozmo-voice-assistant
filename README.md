# Cozmo - Ultra-Low Latency Hindi Voice Assistant

A real-time Hindi voice assistant optimized for **sub-200ms latency** using:
- **Sarvam STT** for Hindi speech recognition
- **Groq LLM** (llama-3.1-8b-instant) for fast text generation
- **Cartesia TTS** (Sonic-3) for ultra-low latency text-to-speech

## 🎯 Latency Performance

**Target: <200ms end-to-end latency** (user stops speaking → first audio frame)

### Current Performance Breakdown

```
STT Processing:        ~100-150ms  (with interim transcripts)
LLM First Token:       ~50-100ms   (streaming enabled)
TTS First Audio:       ~50-100ms   (Cartesia streaming)
─────────────────────────────────────────────
Total Latency:         ~200-350ms  (target: <200ms)
```

### Optimization Strategy

1. **STT Optimization**
   - Uses interim/partial transcripts to trigger LLM early
   - VAD optimized for fast detection (0.1s start/stop)
   - Sarvam STT with Hindi language support

2. **LLM Optimization**
   - Groq llama-3.1-8b-instant (fastest model)
   - `max_tokens=15` (ultra-short responses)
   - `temperature=0.3` (faster, deterministic)
   - Streaming enabled for immediate token generation

3. **TTS Optimization**
   - Cartesia Sonic-3 model
   - `aggregate_sentences=False` (no buffering, immediate processing)
   - 16kHz sample rate (matches LiveKit transport)
   - WebSocket streaming for real-time audio

## 🏗️ Architecture

```
User Audio → STT → LLM → TTS → Audio Output
    ↓         ↓     ↓     ↓
  VAD    Interim  Stream Stream
         Transcript
```

### Pipeline Flow

1. **User speaks** → VAD detects speech
2. **STT processes** → Emits interim transcripts immediately
3. **LLM receives** → Starts generating on first interim transcript
4. **TTS receives** → Starts synthesis on first LLM token (streaming)
5. **Audio output** → First audio frame arrives

## 📊 Latency Calculation

The system tracks latency at multiple points:

- **STT Latency**: `user_stop → first_transcript`
- **LLM Latency**: `transcript → first_token`
- **TTS Latency**: `first_token → first_audio`
- **Total Latency**: `user_stop → first_audio_frame`

All metrics are logged with detailed breakdowns showing:
- Component-level timing
- Streaming vs batch processing
- Target achievement status

## 🚀 Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export SARVAM_API_KEY="your_sarvam_key"
export GROQ_API_KEY="your_groq_key"
export CARTESIA_API_KEY="your_cartesia_key"
export LIVEKIT_URL="your_livekit_url"
export LIVEKIT_API_KEY="your_livekit_key"
export LIVEKIT_API_SECRET="your_livekit_secret"
```

3. Run the agent:
```bash
python -m server.main
```

## 📈 Performance Monitoring

The system includes comprehensive latency logging:

- `⏱️ TOTAL LATENCY`: End-to-end latency measurement
- `📊 BREAKDOWN`: Component-level timing breakdown
- `🎵 FIRST AUDIO FRAME`: Most accurate latency (first audio byte)
- `✅ TARGET ACHIEVED`: Confirms <200ms target
- `⚠️ TARGET MISSED`: Warns if >200ms

## 🔧 Configuration

Key optimization parameters in `server/services/llm.py`:
- `max_tokens=15`: Ultra-short responses
- `temperature=0.3`: Fast, deterministic generation
- `stream=True`: Enable streaming

Key optimization parameters in `server/services/cartesia_tts.py`:
- `aggregate_sentences=False`: No sentence buffering
- `sample_rate=16000`: Match LiveKit transport

## 📝 Notes

- Uses interim transcripts to start LLM processing early
- LLM streaming ensures TTS starts on first token
- Cartesia TTS provides sub-100ms audio generation
- All components optimized for minimal buffering

## 🎯 Future Optimizations

To achieve <150ms latency:
1. Further reduce `max_tokens` to 10
2. Use faster VAD settings (0.05s detection)
3. Optimize network latency (use closer regions)
4. Consider edge deployment for STT/LLM
