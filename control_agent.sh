#!/bin/bash
# Simple agent control script

ACTION=$1

case $ACTION in
    stop)
        echo "🛑 Stopping all agents..."
        pkill -9 -f "python server/main.py" 2>/dev/null
        sleep 1
        if pgrep -f "python server/main.py" > /dev/null; then
            echo "❌ Some agents still running"
        else
            echo "✅ All agents stopped"
        fi
        ;;
    start)
        echo "🚀 Starting agent..."
        cd /Users/vinitwadgaonkar/cozmo
        export PYTHONPATH=$PYTHONPATH:$(pwd)
        export LIVEKIT_URL=wss://vinit-oj6871wv.livekit.cloud
        export LIVEKIT_API_KEY=APImtoTstBBLzZP
        export LIVEKIT_API_SECRET=rFjTtlSGbGe1tGzhyEopt44BLQy8Yxx86Z07FGHwe2fB
        export SARVAM_API_KEY=sk_lpduebms_YmNTF2VmiVXXHcwB20VDO2aW
        export OPENAI_API_KEY="your_openai_key_here"
        export GROQ_API_KEY="your_groq_key_here"
        export DEEPGRAM_API_KEY=2cd5d51059f2974c28c5e3e098182820c5737846
        export CARTESIA_API_KEY=sk_car_3sxzC3PMtbL9dMZUa6gca2
        
        python server/main.py dev 2>&1 | tee agent_debug.log &
        sleep 2
        if pgrep -f "python server/main.py" > /dev/null; then
            echo "✅ Agent started (PID: $(pgrep -f 'python server/main.py'))"
        else
            echo "❌ Agent failed to start"
        fi
        ;;
    status)
        if pgrep -f "python server/main.py" > /dev/null; then
            echo "✅ Agent is running (PID: $(pgrep -f 'python server/main.py'))"
        else
            echo "❌ Agent is not running"
        fi
        ;;
    logs)
        tail -f agent_debug.log | grep -E '🎤|📝|🤖|💬|🔊|⏱️|📊|ENTRYPOINT|Error|Exception' -i
        ;;
    *)
        echo "Usage: $0 {stop|start|status|logs}"
        echo ""
        echo "Commands:"
        echo "  stop   - Stop all agents"
        echo "  start  - Start the agent"
        echo "  status - Check if agent is running"
        echo "  logs   - Watch logs in real-time"
        exit 1
        ;;
esac

