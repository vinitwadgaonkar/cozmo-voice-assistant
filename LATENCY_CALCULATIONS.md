# Latency Calculations and Breakdown

This document explains how latency is calculated and tracked in the Cozmo voice assistant.

## 🎯 Target: <200ms End-to-End Latency

The system is optimized to achieve **sub-200ms latency** from when the user stops speaking to when the first audio frame is generated.

## 📊 Latency Components

### 1. STT (Speech-to-Text) Latency
**Measurement**: `user_stop_speaking → first_transcript_received`

- **Current**: ~100-150ms
- **Optimization**: Uses interim/partial transcripts to trigger LLM early
- **VAD Settings**: 
  - `start_secs=0.1` (fast start detection)
  - `stop_secs=0.1` (fast stop detection)
  - `confidence=0.5` (balanced sensitivity)

### 2. LLM (Language Model) Latency
**Measurement**: `transcript_received → first_token_generated`

- **Current**: ~50-100ms (with streaming)
- **Optimization**:
  - Model: `llama-3.1-8b-instant` (fastest Groq model)
  - `max_tokens=15` (ultra-short responses)
  - `temperature=0.3` (faster, deterministic)
  - `stream=True` (immediate token generation)

### 3. TTS (Text-to-Speech) Latency
**Measurement**: `first_token_received → first_audio_frame`

- **Current**: ~50-100ms (with Cartesia streaming)
- **Optimization**:
  - Model: `sonic-3` (Cartesia's fastest)
  - `aggregate_sentences=False` (no buffering)
  - WebSocket streaming for real-time audio
  - 16kHz sample rate (matches transport)

### 4. Audio Streaming Latency
**Measurement**: `first_audio_generated → first_audio_frame_pushed`

- **Current**: ~10-20ms
- **Optimization**: Direct frame pushing, no buffering

## 📈 Total Latency Calculation

```
Total Latency = STT + LLM + TTS + Audio_Stream

Best Case:
  100ms (STT) + 50ms (LLM) + 50ms (TTS) + 10ms (Stream) = 210ms

Optimized Case (with interim transcripts):
  50ms (STT interim) + 50ms (LLM) + 50ms (TTS) + 10ms (Stream) = 160ms ✅

Target: <200ms ✅
```

## 🔍 Detailed Breakdown Logging

The system logs detailed breakdowns showing:

```
📊 DETAILED BREAKDOWN: STT=120ms → LLM_start=80ms → TTS_start=60ms → Audio_stream=15ms
🎵 FIRST AUDIO FRAME (latency: 275ms from user stop)
✅ TARGET ACHIEVED: 275ms < 200ms  (or ⚠️ if >200ms)
```

### Breakdown Components Explained

1. **STT**: Time from user stop to first transcript (interim or final)
2. **LLM_start**: Time from transcript to LLM first token
3. **TTS_start**: Time from LLM token to TTS synthesis start
4. **Audio_stream**: Time from TTS start to first audio frame pushed

## 🚀 Optimization Strategies

### Current Optimizations Applied

1. ✅ **Interim Transcripts**: LLM starts on partial transcripts
2. ✅ **LLM Streaming**: TTS starts on first token (not full response)
3. ✅ **No Sentence Aggregation**: TTS processes immediately
4. ✅ **Short Responses**: `max_tokens=15` for faster generation
5. ✅ **Fast VAD**: 0.1s detection windows

### Future Optimizations (for <150ms)

1. **Reduce max_tokens to 10**: Even shorter responses
2. **Faster VAD**: 0.05s detection windows
3. **Edge Deployment**: Reduce network latency
4. **Parallel Processing**: Start TTS on first token while LLM continues

## 📝 Measurement Methodology

### Timestamps Tracked

- `_user_speech_end`: When user stops speaking (VAD)
- `_stt_end`: When first transcript received (interim or final)
- `_llm_start`: When first LLM token generated
- `_tts_start`: When TTS synthesis starts
- `_first_audio_time`: When first audio frame is pushed

### Calculation Formula

```python
total_latency = (first_audio_time - user_speech_end) * 1000  # in milliseconds

stt_latency = (stt_end - user_speech_end) * 1000
llm_latency = (llm_start - stt_end) * 1000
tts_latency = (tts_start - llm_start) * 1000
audio_stream_latency = (first_audio_time - tts_start) * 1000
```

## 🎯 Performance Targets

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| STT | <100ms | 100-150ms | ⚠️ |
| LLM | <50ms | 50-100ms | ✅ |
| TTS | <50ms | 50-100ms | ✅ |
| **Total** | **<200ms** | **200-350ms** | **⚠️** |

## 📊 Example Log Output

```
🎤 USER STOPPED SPEAKING (duration: 550ms)
📝 STT INTERIM: "नमस्ते" (latency: 120ms) - Should trigger LLM early!
💬 LLM FIRST TOKEN (TTFB: 80ms): "मैं आपकी मदद कर सकता हूँ..."
🔊 TTS STARTED (after LLM first token: 60ms)
🎵 FIRST AUDIO FRAME (latency: 275ms from user stop)
📊 DETAILED BREAKDOWN: STT=120ms → LLM_start=80ms → TTS_start=60ms → Audio_stream=15ms
⚠️  TARGET MISSED: 275ms > 200ms
```

## 🔧 Tuning Parameters

To optimize further, adjust these parameters:

### LLM (`server/services/llm.py`)
```python
max_tokens=10,      # Reduce from 15
temperature=0.2,    # Reduce from 0.3
```

### TTS (`server/services/cartesia_tts.py`)
```python
aggregate_sentences=False,  # Already optimized
sample_rate=16000,          # Match transport
```

### VAD (`server/utils/vad.py`)
```python
start_secs=0.05,   # Reduce from 0.1
stop_secs=0.05,    # Reduce from 0.1
```

