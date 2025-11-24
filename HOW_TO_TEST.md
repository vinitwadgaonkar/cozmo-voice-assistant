# How to Test Your Hindi Voice Agent

## The Error You Saw is Normal

The `ERR_UNKNOWN_URL_SCHEME` error is expected - WebSocket URLs (`wss://`) cannot be opened in a browser. They're used by applications to connect programmatically.

## How to Actually Test Your Agent

### Method 1: LiveKit Cloud Dashboard (Easiest)

1. Go to: https://cloud.livekit.io
2. Log in to your account
3. Navigate to your project (the one with URL `vinit-oj6871wv.livekit.cloud`)
4. Click on "Rooms" or use the "Test" feature
5. Create a new room or join an existing one
6. The agent should automatically connect when you join
7. Enable your microphone and speak in Hindi

### Method 2: LiveKit Playground

1. Go to: https://agents-playground.livekit.io/
2. Enter your LiveKit URL: `wss://your-livekit-url.livekit.cloud`
3. Enter your API Key: (get from LiveKit dashboard)
4. Enter your API Secret: (get from LiveKit dashboard)
5. Click "Connect"
6. The agent will join and you can test the voice interaction

### Method 3: Check Agent Status

To verify your agent is running and ready:

```bash
# Check if the server process is running
ps aux | grep "server/main.py"

# Or check the logs if you have them
# The agent should show it's waiting for connections
```

## What Should Happen

1. When you join a room, the agent automatically connects
2. You speak in Hindi
3. The agent transcribes (Sarvam STT)
4. The agent responds in Hindi (OpenAI LLM)
5. The agent speaks back (Sarvam TTS with "anushka" voice)

## Troubleshooting

If the agent doesn't connect:
- Make sure the server is running (`python server/main.py dev`)
- Check that all environment variables are set correctly
- Verify your LiveKit API credentials in the dashboard
- Check server logs for any connection errors

