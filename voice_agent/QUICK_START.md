# Quick Start - Hindi LiveKit Voice Agent

## 30-Second Setup

```bash
# 1. Install
pip install -r requirements-voice-agent.txt

# 2. Configure (create .env file)
cat > .env << 'EOF'
SARVAM_API_KEY=your_key
OPENAI_API_KEY=your_key
LIVEKIT_URL=wss://your-server
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
VOICE_AGENT_DEFAULT_ROOM=test-room
EOF

# 3. Verify
python voice_agent/verify_setup.py

# 4. Run
python -m voice_agent.main
```

## Test It

1. Start the agent (command above)
2. Join the same LiveKit room from any client
3. Speak in Hindi or Hinglish
4. Agent responds in real-time!

## Common Commands

```bash
# Run with custom room
python -m voice_agent.main --room my-room

# Run with custom identity
python -m voice_agent.main --identity my-agent

# Using the shell script
./run_voice_agent.sh --room my-room --identity my-agent
```

## Need Help?

- Full guide: See `VOICE_AGENT_GUIDE.md`
- Troubleshooting: Run `python voice_agent/verify_setup.py`
- Issues: Check logs for detailed error messages

## Architecture in One Line

**LiveKit** (audio) → **Sarvam STT** (Hindi→text) → **OpenAI** (text→text) → **Sarvam TTS** (text→Hindi) → **LiveKit** (audio)

That's it! 🎉



