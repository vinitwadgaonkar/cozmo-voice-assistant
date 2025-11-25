# Hindi LiveKit Voice Agent - Complete Guide

A fully functional Hindi voice agent using **LiveKit** (WebRTC), **Pipecat** (orchestration), **Sarvam AI** (Hindi STT/TTS), and **OpenAI** (LLM).

## 🎯 What This Is

This is a **real, production-ready voice agent** that:
- Connects to LiveKit rooms via WebRTC for real-time audio streaming
- Transcribes Hindi/Hinglish speech using Sarvam STT
- Generates natural conversational responses using OpenAI GPT-4o-mini
- Synthesizes high-quality Hindi speech using Sarvam TTS
- Handles multiple participants, interruptions, and edge cases

**No placeholders. No TODOs. No dummy handlers. Just working code.**

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-voice-agent.txt
```

This installs:
- `pipecat-ai[daily,openai,sarvam]` - Pipeline orchestration with all integrations
- `livekit` - Python SDK for token generation
- `python-dotenv` - Environment variable management
- `loguru` - Clean logging

### 2. Set Up Environment Variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Sarvam AI - Get from https://sarvam.ai
SARVAM_API_KEY=your_sarvam_key_here

# OpenAI - Get from https://platform.openai.com
OPENAI_API_KEY=your_openai_key_here

# LiveKit - Get from your LiveKit server or https://cloud.livekit.io
LIVEKIT_URL=wss://your-livekit-host
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Optional: Configure defaults
VOICE_AGENT_DEFAULT_ROOM=cozmo-hindi-test
VOICE_AGENT_DEFAULT_IDENTITY=pipecat-agent-1
VOICE_AGENT_OPENAI_MODEL=gpt-4o-mini
```

### 3. Verify Setup

Run the verification script to check everything is configured correctly:

```bash
python voice_agent/verify_setup.py
```

This checks:
- ✅ All required packages are installed
- ✅ Pipecat services are available
- ✅ Environment variables are set
- ✅ Configuration loads successfully

### 4. Run the Agent

**Option A: Using the convenience script**

```bash
./run_voice_agent.sh
```

**Option B: Using Python directly**

```bash
python -m voice_agent.main --room cozmo-hindi-test --identity pipecat-agent-1
```

**Option C: Using environment variables**

```bash
export VOICE_AGENT_DEFAULT_ROOM=my-room
python -m voice_agent.main
```

## 🎤 How to Test

### Using LiveKit Web Client

1. Start the agent (see above)
2. Join the same room from a LiveKit web client
3. Speak in Hindi or Hinglish
4. The agent will respond in real-time

### Using LiveKit Playground

1. Go to your LiveKit dashboard
2. Navigate to the "Playground" section
3. Enter the same room name as your agent
4. Enable microphone and start speaking

### Using Your Own Client

Connect any LiveKit-compatible client to the same room. The agent will automatically:
- Detect when participants join
- Start transcribing their speech
- Generate and speak responses
- Handle interruptions gracefully

## 🏗️ Architecture

### Pipeline Flow

```
User Speech (LiveKit)
    ↓
[LiveKit Transport Input]
    ↓
[Sarvam STT] ← Speech to text (Hindi/Hinglish)
    ↓
[LLM Context Aggregator] ← Manages conversation history
    ↓
[OpenAI LLM] ← Generates response
    ↓
[Sarvam TTS] ← Text to speech (Hindi)
    ↓
[LiveKit Transport Output]
    ↓
Agent Speech (LiveKit)
```

### Component Details

**LiveKit Transport (`LiveKitTransportService`)**
- WebRTC audio streaming (16kHz, mono PCM)
- Built-in VAD (Voice Activity Detection)
- Automatic participant management
- Event handlers for join/leave/state changes

**Sarvam STT (`SarvamSTTService`)**
- Real-time Hindi/Hinglish speech recognition
- VAD signals for turn detection
- Optimized for conversational speech
- Low latency transcription

**OpenAI LLM (`OpenAILLMService`)**
- GPT-4o-mini for fast, cost-effective responses
- Streaming token generation
- Context management for multi-turn conversations
- Concise responses (under 3 sentences)

**Sarvam TTS (`SarvamTTSService`)**
- High-quality Hindi voice synthesis
- "Arvind" voice (male, natural)
- 16kHz output matching LiveKit format
- Low latency audio generation

## 📁 Project Structure

```
voice_agent/
├── __init__.py              # Package metadata
├── config.py                # Configuration loading from .env
├── livekit_token.py         # JWT token generation for LiveKit
├── pipeline.py              # Core Pipecat pipeline setup
├── main.py                  # CLI entrypoint
└── verify_setup.py          # Setup verification script

requirements-voice-agent.txt  # Python dependencies
run_voice_agent.sh           # Convenience run script
.env.example                 # Environment variable template
.env                         # Your actual credentials (not in git)
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SARVAM_API_KEY` | ✅ Yes | - | Sarvam AI API key |
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key |
| `LIVEKIT_URL` | ✅ Yes | - | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | ✅ Yes | - | LiveKit API key |
| `LIVEKIT_API_SECRET` | ✅ Yes | - | LiveKit API secret |
| `VOICE_AGENT_DEFAULT_ROOM` | ❌ No | `cozmo-hindi-test` | Default room name |
| `VOICE_AGENT_DEFAULT_IDENTITY` | ❌ No | `pipecat-agent-1` | Default agent identity |
| `VOICE_AGENT_OPENAI_MODEL` | ❌ No | `gpt-4o-mini` | OpenAI model to use |

### Command-Line Options

```bash
python -m voice_agent.main [OPTIONS]

Options:
  --room ROOM_NAME       LiveKit room name (overrides env var)
  --identity IDENTITY    Participant identity (overrides env var)
```

## 🐛 Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, ensure all extras are installed:

```bash
pip install 'pipecat-ai[daily,openai,sarvam]'
```

The `voice_agent/pipeline.py` has fallback imports for different Pipecat API versions.

### Configuration Errors

Run the verification script to diagnose:

```bash
python voice_agent/verify_setup.py
```

Common issues:
- ❌ `.env` file missing → Copy from `.env.example`
- ❌ Missing API keys → Add them to `.env`
- ❌ Wrong API key format → Check for extra quotes or spaces

### Audio Issues

Ensure audio format consistency:
- Sample rate: **16kHz**
- Channels: **Mono (1)**
- Encoding: **PCM (linear16)**

All services (LiveKit, Sarvam STT/TTS) are configured to use these settings.

### Connection Issues

Check LiveKit URL format:
- ✅ Good: `wss://your-server.livekit.cloud`
- ❌ Bad: `https://your-server.livekit.cloud` (wrong protocol)
- ❌ Bad: `your-server.livekit.cloud` (missing protocol)

## 🎨 Customization

### Change the System Prompt

Edit `voice_agent/pipeline.py`, function `run_voice_agent()`:

```python
context = OpenAILLMContext(
    messages=[
        {
            "role": "system",
            "content": "Your custom prompt here"
        }
    ]
)
```

### Use a Different TTS Voice

Edit `voice_agent/pipeline.py`, function `build_services()`:

```python
tts = SarvamTTSService(
    api_key=cfg.sarvam.api_key,
    voice_id="meera",  # Female voice instead of "arvind"
    sample_rate=16000,
)
```

Available Sarvam voices: Check Sarvam AI documentation.

### Adjust Response Length

Edit `voice_agent/pipeline.py`:

```python
llm = OpenAILLMService(
    api_key=cfg.openai.api_key,
    model=cfg.openai.model,
    max_tokens=256,  # Longer responses
)
```

### Enable Interruptions

Already enabled by default in `PipelineParams`:

```python
task = PipelineTask(
    pipeline,
    PipelineParams(
        allow_interruptions=True,  # User can interrupt agent
        enable_metrics=True,
        enable_usage_metrics=True,
    )
)
```

## 📊 Monitoring & Logging

The agent uses `loguru` for clean, informative logging:

```
[INFO] Starting LiveKit Hindi voice agent in room=cozmo-hindi-test, identity=pipecat-agent-1
[INFO] Building Sarvam STT service...
[INFO] Building Sarvam TTS service...
[INFO] Building OpenAI LLM service (model: gpt-4o-mini)...
[INFO] Generating LiveKit access token...
[INFO] Creating LiveKit transport...
[INFO] Setting up LLM context and aggregator...
[INFO] Building pipeline...
[INFO] Starting pipeline runner...
[INFO] First participant joined: user-123
```

### Enable Debug Logging

Add to your script:

```python
from loguru import logger
logger.add(sys.stderr, level="DEBUG")
```

## 🚀 Deployment

### Running in Production

1. **Use environment variables** instead of `.env` file
2. **Set up process management** (systemd, supervisor, pm2)
3. **Add health checks** to monitor agent status
4. **Configure log rotation** for long-running agents
5. **Use secrets management** for API keys (Vault, AWS Secrets Manager)

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements-voice-agent.txt .
RUN pip install -r requirements-voice-agent.txt

COPY voice_agent/ voice_agent/

CMD ["python", "-m", "voice_agent.main"]
```

Build and run:

```bash
docker build -t hindi-voice-agent .
docker run --env-file .env hindi-voice-agent
```

### Scaling

To run multiple agents:

```bash
# Terminal 1
python -m voice_agent.main --room room-1 --identity agent-1

# Terminal 2
python -m voice_agent.main --room room-2 --identity agent-2

# Terminal 3
python -m voice_agent.main --room room-3 --identity agent-3
```

Each agent joins a different room independently.

## 🔐 Security Notes

1. **Never commit `.env`** - It's in `.gitignore` by default
2. **Rotate API keys regularly**
3. **Use least-privilege LiveKit tokens** - Grant only necessary permissions
4. **Validate room names** - Sanitize user input before creating rooms
5. **Monitor usage** - Track API calls to prevent abuse

## 📚 References

- [Pipecat Documentation](https://docs.pipecat.ai/)
- [LiveKit Python SDK](https://docs.livekit.io/realtime/server/python/)
- [Sarvam AI API](https://docs.sarvam.ai/)
- [OpenAI API](https://platform.openai.com/docs/)

## 💡 Next Steps

After getting the basic agent working:

1. **Add conversation history** - Persist context across sessions
2. **Implement custom intents** - Handle specific commands or queries
3. **Add multilingual support** - Switch between Hindi and English
4. **Integrate with your backend** - Call your APIs from the agent
5. **Add analytics** - Track usage, latency, errors

## 🤝 Contributing

This is a self-contained package within the Cozmo repository. To extend:

1. Keep dependencies minimal
2. Maintain compatibility with the existing codebase
3. Add tests for new features
4. Update this guide with new functionality

## 📝 License

Part of the Cozmo voice assistant project. See main repository for license.

---

**Built with ❤️ using LiveKit, Pipecat, Sarvam AI, and OpenAI**



