#!/bin/bash
# Optimized agent startup script with auto-disconnect

cd /Users/vinitwadgaonkar/cozmo

# Export all environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export LIVEKIT_URL=wss://vinit-oj6871wv.livekit.cloud
export LIVEKIT_API_KEY=APImtoTstBBLzZP
export LIVEKIT_API_SECRET=rFjTtlSGbGe1tGzhyEopt44BLQy8Yxx86Z07FGHwe2fB
export SARVAM_API_KEY=sk_lpduebms_YmNTF2VmiVXXHcwB20VDO2aW
export OPENAI_API_KEY="your_openai_key_here"
export GROQ_API_KEY="your_groq_key_here"
export DEEPGRAM_API_KEY=2cd5d51059f2974c28c5e3e098182820c5737846
export CARTESIA_API_KEY=sk_car_3sxzC3PMtbL9dMZUa6gca2

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

