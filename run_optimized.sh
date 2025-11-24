#!/bin/bash
# Optimized agent startup script with auto-disconnect

cd /Users/vinitwadgaonkar/cozmo

# Export all environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export LIVEKIT_URL="your_livekit_url_here"
export LIVEKIT_API_KEY="your_livekit_api_key_here"
export LIVEKIT_API_SECRET="your_livekit_api_secret_here"
export SARVAM_API_KEY="your_sarvam_api_key_here"
export OPENAI_API_KEY="your_openai_key_here"
export GROQ_API_KEY="your_groq_key_here"
export DEEPGRAM_API_KEY="your_deepgram_key_here"
export CARTESIA_API_KEY="your_cartesia_key_here"

# Kill any existing agents
pkill -9 -f "python server/main.py" 2>/dev/null
sleep 1

# Start optimized agent
echo "🚀 Starting optimized agent (sub-150ms target)..."
python server/main.py dev 2>&1 | tee agent_debug.log &

echo "✅ Agent started. PID: $!"
echo "📊 View logs: tail -f agent_debug.log"
echo "🧪 Run test: python auto_test_latency.py"
echo "🛑 Stop agent: pkill -9 -f 'python server/main.py'"

