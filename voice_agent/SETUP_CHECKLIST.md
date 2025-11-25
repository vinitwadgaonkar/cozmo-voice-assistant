# Voice Agent Setup Checklist

Follow this checklist to get your Hindi LiveKit voice agent running.

## ☑️ Pre-requisites

- [ ] Python 3.10 or higher installed
- [ ] pip package manager installed
- [ ] Terminal/command line access
- [ ] Text editor (for creating .env file)

## ☑️ API Keys & Accounts

### Required Accounts

- [ ] **Sarvam AI** account
  - Sign up at: https://sarvam.ai
  - Navigate to API keys section
  - Generate and copy API key
  
- [ ] **OpenAI** account
  - Sign up at: https://platform.openai.com
  - Navigate to API keys
  - Create new key with appropriate permissions
  
- [ ] **LiveKit** server access
  - Option A: Use LiveKit Cloud (https://cloud.livekit.io)
  - Option B: Self-hosted LiveKit server
  - Get: Server URL, API Key, API Secret

## ☑️ Installation Steps

### Step 1: Navigate to Project Directory

```bash
cd /path/to/cozmo
```

- [ ] Verified I'm in the correct directory

### Step 2: Install Dependencies

```bash
pip install -r requirements-voice-agent.txt
```

**Expected output:**
```
Successfully installed pipecat-ai-X.X.X livekit-X.X.X python-dotenv-X.X.X loguru-X.X.X
```

- [ ] All packages installed successfully
- [ ] No error messages

### Step 3: Create .env File

Create a file named `.env` in the project root:

```bash
# Copy-paste this template and fill in your values
cat > .env << 'EOF'
# Sarvam AI Configuration
SARVAM_API_KEY=your_sarvam_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here

# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Voice Agent Defaults (optional)
VOICE_AGENT_DEFAULT_ROOM=test-room
VOICE_AGENT_DEFAULT_IDENTITY=hindi-agent
VOICE_AGENT_OPENAI_MODEL=gpt-4o-mini
EOF
```

**Then edit the file** and replace placeholders with your actual keys.

- [ ] `.env` file created
- [ ] All API keys filled in (no placeholders left)
- [ ] LiveKit URL starts with `wss://`
- [ ] No extra quotes or spaces around keys

### Step 4: Verify Setup

```bash
python voice_agent/verify_setup.py
```

**Expected output:**
```
✓ pipecat-ai is installed
✓ livekit is installed
✓ python-dotenv is installed
✓ loguru is installed
✓ LIVEKIT_URL is set
✓ SARVAM_API_KEY is set
✓ OPENAI_API_KEY is set
✓ All checks passed!
```

- [ ] All checks passed
- [ ] No error messages about missing packages
- [ ] No error messages about missing environment variables

## ☑️ First Run

### Step 5: Start the Agent

```bash
python -m voice_agent.main
```

**Or using the shell script:**

```bash
./run_voice_agent.sh
```

**Expected output:**
```
[INFO] Loading voice agent configuration...
[INFO] Voice agent will join room 'test-room' as 'hindi-agent'
[INFO] Starting LiveKit Hindi voice agent...
[INFO] Building Sarvam STT service...
[INFO] Building Sarvam TTS service...
[INFO] Building OpenAI LLM service...
[INFO] Creating LiveKit transport...
[INFO] Starting pipeline runner...
```

- [ ] Agent started without errors
- [ ] Logs show successful initialization
- [ ] No "Missing API key" errors

### Step 6: Test the Agent

1. **Open LiveKit Playground or Web Client**
   - Go to your LiveKit dashboard
   - Navigate to the "Playground" or testing interface
   - Enter the **same room name** as your agent (e.g., "test-room")

- [ ] Opened LiveKit client
- [ ] Entered correct room name

2. **Join the Room**
   - Enable microphone permissions
   - Click "Join Room" or equivalent

- [ ] Successfully joined room
- [ ] Can see/hear audio tracks

3. **Speak in Hindi or Hinglish**
   - Say something like: "नमस्ते, कैसे हैं आप?" (Hello, how are you?)
   - Or: "Hello, can you help me?"

- [ ] Agent responds with audio
- [ ] Response is in Hindi or Hinglish
- [ ] Audio quality is clear

## ☑️ Troubleshooting

### Issue: Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pipecat'`

**Solution:**
```bash
pip install 'pipecat-ai[daily,openai,sarvam]'
```

- [ ] Resolved

### Issue: Configuration Errors

**Problem:** `RuntimeError: Missing required environment variable: SARVAM_API_KEY`

**Solution:**
1. Check `.env` file exists in project root
2. Verify API key is present (no quotes, no extra spaces)
3. Restart terminal/shell to reload environment

- [ ] Resolved

### Issue: Connection Errors

**Problem:** `Connection failed to LiveKit server`

**Solution:**
1. Verify LiveKit URL format: `wss://your-server.livekit.cloud`
2. Check API key and secret are correct
3. Test LiveKit server is running (visit in browser)

- [ ] Resolved

### Issue: Audio Not Working

**Problem:** Agent joins but doesn't respond to speech

**Solution:**
1. Check microphone permissions in browser
2. Ensure you're in the same room as the agent
3. Verify Sarvam API key is valid
4. Check agent logs for errors

- [ ] Resolved

## ☑️ Next Steps

### Basic Usage

- [ ] Run agent with custom room: `python -m voice_agent.main --room my-room`
- [ ] Run agent with custom identity: `python -m voice_agent.main --identity my-agent`
- [ ] Stop agent with Ctrl+C (graceful shutdown)

### Customization

- [ ] Read `EXAMPLES.md` for 12 customization patterns
- [ ] Modify system prompt in `voice_agent/pipeline.py`
- [ ] Change TTS voice (e.g., "meera" instead of "arvind")
- [ ] Adjust OpenAI model in `.env` file

### Documentation

- [ ] Read `QUICK_START.md` (30-second refresher)
- [ ] Read `VOICE_AGENT_GUIDE.md` (complete guide)
- [ ] Read `VOICE_AGENT_SUMMARY.md` (implementation details)

### Advanced

- [ ] Add function calling (see `EXAMPLES.md`)
- [ ] Implement conversation logging
- [ ] Set up metrics tracking
- [ ] Deploy to production (Docker example in guide)

## 📋 Quick Reference

### Start Agent
```bash
python -m voice_agent.main
```

### Stop Agent
```
Ctrl+C
```

### Verify Setup
```bash
python voice_agent/verify_setup.py
```

### Check Logs
Agent logs to console (stdout/stderr). Redirect to file:
```bash
python -m voice_agent.main 2>&1 | tee agent.log
```

### Environment Variables
All in `.env` file:
- `SARVAM_API_KEY` - Sarvam AI key
- `OPENAI_API_KEY` - OpenAI key
- `LIVEKIT_URL` - LiveKit server URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret

### Common Commands
```bash
# Run with defaults
python -m voice_agent.main

# Custom room
python -m voice_agent.main --room sales-demo

# Custom identity
python -m voice_agent.main --identity sales-agent

# Both
python -m voice_agent.main --room support --identity support-bot

# Using shell script
./run_voice_agent.sh --room test --identity agent
```

## ✅ Completion

### All Done!

- [ ] Agent running successfully
- [ ] Tested with real audio
- [ ] Received Hindi/Hinglish responses
- [ ] Reviewed documentation
- [ ] Ready to customize/deploy

**Congratulations! Your Hindi LiveKit voice agent is ready to use.** 🎉

---

**Need Help?**
- Troubleshooting: See `VOICE_AGENT_GUIDE.md`
- Examples: See `EXAMPLES.md`
- Quick reference: See `QUICK_START.md`

**Questions?**
- Check logs for error messages
- Run `python voice_agent/verify_setup.py`
- Review API key formats and permissions



