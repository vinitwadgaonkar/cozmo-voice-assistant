# Design Decisions

## Why Sarvam for STT?
- **Pros**: Native Hindi support, handles code-switching (Hinglish) better than Whisper, optimized for Indian accents.
- **Cons**: Proprietary API.

## Why Cartesia Sonic + Sarvam Bulbul?
- **Cartesia**: Currently the state-of-the-art for latency (sub-100ms).
- **Sarvam Bulbul**: High quality native Indian voices.
- **The Race**: By racing them, we get the best of both worlds: Speed (usually Cartesia) and Quality/Fallback (Sarvam).

## Why OpenAI Mini?
- **Cost/Speed Balance**: GPT-4o-mini is significantly faster (TTFT) than GPT-4o and sufficient for conversational tasks.

## Why Custom Racer instead of Pipecat default?
- Pipecat is great, but our "Winner Takes All" cancellation logic is specific to this ultra-low-latency requirement. We needed granular control over the `tee` mechanism and stream cancellation.

