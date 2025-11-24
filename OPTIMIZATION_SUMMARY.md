# 🚀 Sub-150ms Latency Optimization Summary

## ✅ Optimizations Applied

### 1. **VAD (Voice Activity Detection)**
- **Start**: 0.15s (was 0.18s) - Faster speech detection
- **Stop**: 0.15s (was 0.20s) - Ultra-fast turn-taking
- **Confidence**: 0.5 (was 0.6) - Lower threshold for faster detection
- **Min Volume**: 0.4 (was 0.5) - More sensitive

### 2. **STT (Speech-to-Text) - Deepgram**
- **Model**: `nova-2` (fastest)
- **Interim Results**: ✅ Enabled (~50ms latency)
- **VAD Events**: ✅ Enabled (faster turn detection)
- **Endpointing**: 300ms (faster endpointing)
- **Smart Format**: ❌ Disabled (saves ~10-20ms)
- **Punctuation**: ❌ Disabled (saves ~5-10ms)

### 3. **LLM (Language Model) - Groq**
- **Model**: `llama-3.1-8b-instant` (fastest)
- **Temperature**: 0.7 (lower = faster, more deterministic)
- **Max Tokens**: 50 (limit response length for speed)

### 4. **TTS (Text-to-Speech) - Sarvam**
- **Model**: `bulbul:v2`
- **Voice**: `anushka`
- **Pace**: 1.05 (slightly faster)
- **Min Buffer**: 40 (smaller = faster first audio)
- **Max Chunk**: 180 (optimized for streaming)

## 📊 Expected Latency Breakdown

| Component | Target | Status |
|-----------|--------|--------|
| VAD Detection | <50ms | ✅ Optimized |
| STT (Deepgram) | ~50ms | ✅ Optimized |
| LLM (Groq) | ~100-200ms | ✅ Optimized |
| TTS (Sarvam) | ~200-300ms | ⚠️ Bottleneck |
| **Total E2E** | **<150ms** | **In Progress** |

## 🔧 Current Issue

**Entrypoint not being called** - Agent joins room but pipeline never starts.

**Possible Causes:**
1. LiveKit Cloud not dispatching jobs to self-hosted worker
2. Job dispatch configuration issue
3. Agent worker not properly registered

## 🧪 Testing

### Run Autonomous Test:
```bash
python auto_test_latency.py
```

### Start Optimized Agent:
```bash
./run_optimized.sh
```

### View Logs:
```bash
tail -f agent_debug.log | grep -E "🎤|📝|🤖|💬|🔊|⏱️|📊|ENTRYPOINT"
```

## 💡 Next Steps

1. **Fix Entrypoint Dispatch**: Ensure jobs are dispatched when participants join
2. **TTS Optimization**: Consider Cartesia Sonic (if working) or optimize Sarvam further
3. **Parallel Processing**: Start TTS generation as soon as first LLM token arrives
4. **Pre-warming**: Pre-connect services to reduce connection overhead

## 📝 Files Modified

- `server/utils/vad.py` - Ultra-aggressive VAD settings
- `server/services/llm.py` - Groq optimization (temperature, max_tokens)
- `server/services/sarvam_services.py` - Deepgram optimization (endpointing, formatting)
- `run_optimized.sh` - Easy startup script
- `auto_test_latency.py` - Autonomous testing

## 🎯 Target: <150ms Perceived Latency

**Current Status**: Components optimized, but entrypoint dispatch needs fixing.

