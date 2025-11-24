# Latency Budget

**Target:** < 150ms (Time from User End-of-Speech to First Audio Response)

## Budget Breakdown

| Component | Target Latency | Notes |
|-----------|----------------|-------|
| **Network (One-way)** | 20ms | Assumes good 4G/Wifi |
| **VAD / EOS Detection** | 50ms | Sarvam silence threshold |
| **STT Processing** | 10ms | Streaming partials / optimized final |
| **LLM First Token** | 40ms | OpenAI GPT-4o-mini (Streaming) |
| **TTS First Byte** | 20ms | Cartesia Sonic / Sarvam Race |
| **Network (Return)** | 20ms | |
| **Client Buffer** | 10ms | Minimal buffer |

**Total Expected:** ~170ms (Conservative)
**Optimized Goal:** ~120ms (With Aggro mode + Pre-fetching)

## Strategies for Speed

1. **TTS Race**: Parallel request to two providers guarantees the fastest start time, mitigating network jitter or provider cold-starts.
2. **Aggro Mode**: Starts LLM generation on partial STT results (speculative execution). If the final result changes significantly, we discard and restart, but 80% of the time we gain ~200ms.
3. **Streaming Everywhere**: No buffering of full sentences. Token-by-token processing.
4. **Region Co-location**: Servers should be deployed close to user/providers (e.g., Mumbai/Singapore for Sarvam).

