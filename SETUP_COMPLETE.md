# Hindi Voice Agent - Setup Complete ✅

## What Was Fixed

1. **Replaced Custom Services**: Switched from custom STT/TTS implementations to Pipecat's built-in Sarvam services which are production-ready and properly integrated.

2. **Configuration Updated**: 
   - LiveKit URL: Set via environment variable
   - API Keys: Set via environment variables (see setup instructions)

3. **Dependencies Installed**:
   - `sarvamai` package for Sarvam integration
   - All required Pipecat extensions

## How to Run

### Option 1: Using run.sh
```bash
export LIVEKIT_URL="your_livekit_url_here"
export LIVEKIT_API_KEY="your_livekit_api_key_here"
export LIVEKIT_API_SECRET="your_livekit_api_secret_here"
export SARVAM_API_KEY="your_sarvam_api_key_here"
export OPENAI_API_KEY="your_openai_key_here"
./run.sh
```

### Option 2: Direct Python
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
export LIVEKIT_URL="your_livekit_url_here"
export LIVEKIT_API_KEY="your_livekit_api_key_here"
export LIVEKIT_API_SECRET="your_livekit_api_secret_here"
export SARVAM_API_KEY="your_sarvam_api_key_here"
export OPENAI_API_KEY="your_openai_key_here"
python server/main.py dev
```

## Testing

1. The agent is now running and waiting for LiveKit room connections
2. Go to your LiveKit Cloud dashboard or use the LiveKit Playground
3. Create/join a room - the agent will automatically connect
4. Speak in **Hindi** - the agent will:
   - Transcribe your speech (Sarvam STT)
   - Generate a response (OpenAI GPT-4o-mini)
   - Speak back in Hindi (Sarvam TTS with "anushka" voice)

## Configuration Details

- **STT**: Sarvam Saarika v2.5 with Hindi (hi-IN), high VAD sensitivity
- **LLM**: OpenAI GPT-4o-mini (can switch to Groq if needed)
- **TTS**: Sarvam Bulbul v2 with "anushka" voice, pace=1.05
- **VAD**: Silero VAD with start=0.18s, stop=0.30s, confidence=0.6

## System Prompt

The agent is configured to respond in Hindi with short, concise answers (1-2 lines max).

## Next Steps

1. Test the connection by joining a LiveKit room
2. Monitor logs for any errors
3. Adjust VAD settings if needed for better turn-taking
4. Fine-tune the system prompt for your use case

