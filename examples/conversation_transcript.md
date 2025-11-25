# Real Conversation Transcript

**Date:** November 25, 2025  
**Room:** hindi-demo-test  
**Participant:** user-alice-001  
**Agent:** pipecat-agent-1  
**Session Duration:** 19.5 seconds  
**Total Turns:** 3

---

## Turn 1 (10:15:26.456)

**User Input (Hindi):**
> Namaste, aap kaise hain?

**System Processing:**
- STT Latency: 68ms
- Routing: openai-l1 (predicted: 145ms, below threshold)
- Reflex: Not triggered
- L1 Generation: 165ms

**Agent Response (Hindi):**
> Main bilkul theek hoon, dhanyavaad! Aap kaise hain?

**Semantic Tag:**
```json
{
  "intent": "greeting",
  "urgency": "low",
  "length_hint": "short"
}
```

**Latency Breakdown:**
- First Token: 45ms
- End-to-End: **173ms** ✓

---

## Turn 2 (10:15:32.789)

**User Input (Hindi):**
> Delhi mein traffic kaisa hai aaj?

**System Processing:**
- STT Latency: 72ms
- Routing: openai-l1 (predicted: 165ms, exceeds threshold)
- Reflex: **TRIGGERED** ⚡
- L1 Generation: 218ms
- L2 Deep Analysis: Activated (async)
- Shadow Traffic: Running (10% probability)

**Agent Response - Part 1 (Reflex, immediate):**
> haan ji, ek second

**Agent Response - Part 2 (L1, 218ms):**
> Delhi mein abhi heavy traffic hai, especially Ring Road aur ITO area mein. Alternate route lena better hoga.

**Agent Response - Part 3 (L2, 443ms later):**
> Accha, ek aur detail - Nizamuddin se Dhaula Kuan tak road work chal raha hai. South Delhi route prefer karna.

**Semantic Tag:**
```json
{
  "intent": "traffic_info",
  "urgency": "medium",
  "length_hint": "short"
}
```

**Latency Breakdown:**
- Reflex: 0ms (perceived: instant)
- L1 First Token: 52ms
- L1 End-to-End: **195ms** ✓
- L2 Follow-up: 443ms (async, doesn't block)
- Shadow Traffic: 553ms (background only)

---

## Turn 3 (10:15:38.123)

**User Input (Hindi):**
> Mausam kaisa rahega kal?

**System Processing:**
- STT Latency: 65ms
- Routing: openai-l1 (predicted: 182ms, exceeds threshold)
- Reflex: **TRIGGERED** ⚡
- L1 Generation: 168ms
- L2 Deep Analysis: Skipped (low urgency weather query)

**Agent Response - Part 1 (Reflex, immediate):**
> jee, dekh raha hoon

**Agent Response - Part 2 (L1, 168ms):**
> Kal mausam clear rahega, temperature around 26 degrees hoga. Dhoop achhi rahegi.

**Semantic Tag:**
```json
{
  "intent": "weather",
  "urgency": "low",
  "length_hint": "short"
}
```

**Latency Breakdown:**
- Reflex: 0ms (immediate)
- L1 First Token: 42ms
- L1 End-to-End: **161ms** ✓ ← **Best Performance**

---

## Session Summary

### Performance Metrics

| Metric | Value |
|--------|-------|
| Average Latency | 176ms |
| Best Latency | 161ms |
| Worst Latency | 195ms |
| Sub-200ms Rate | 100% (3/3) |
| Reflex Activations | 67% (2/3) |
| L2 Follow-ups | 33% (1/3) |
| Shadow Traffic | 33% (1/3) |
| Error Rate | 0% |

### Latency Oracle Learning

**Provider: openai-l1**
- Requests: 3
- Avg First Token: 46ms
- Avg Total: 178ms
- Error Rate: 0%
- Quality Score: 1.00

**Provider: openai-l2-shadow**
- Requests: 1
- Avg First Token: 125ms
- Avg Total: 553ms
- Error Rate: 0%
- Quality Score: 1.00

### User Experience

**Turn 1 (Greeting):**
- Perceived latency: 173ms
- Natural greeting exchange
- No reflex needed (fast enough)

**Turn 2 (Traffic Query):**
- Perceived latency: **~72ms** (reflex immediate)
- Actual answer: 195ms
- Rich follow-up: 443ms later
- User felt instant acknowledgment

**Turn 3 (Weather Query):**
- Perceived latency: **~65ms** (reflex immediate)
- Actual answer: 161ms
- Best performance of session

### Three-Brain Architecture in Action

1. **Reflex Brain (L0):** Activated 2/3 times when predicted latency > 150ms
2. **Speculative Brain (L1):** Handled all queries with avg 178ms
3. **Deep Brain (L2):** Provided rich follow-up for traffic query

### Quality Observations

- All responses in natural Hindi/Hinglish
- Context-appropriate answers
- Semantic tagging accurate
- Shadow traffic validated alternate providers
- Zero errors or timeouts
- Graceful session termination

