#!/bin/bash
# Example test run script showing actual usage

echo "=================================="
echo "Cozmo Voice Agent - Test Run"
echo "=================================="
echo ""

# Set up environment
export OPENAI_API_KEY="sk-test-key-redacted"
export SARVAM_API_KEY="sarvam-test-key-redacted"
export LIVEKIT_URL="wss://demo.livekit.cloud"
export LIVEKIT_API_KEY="test-api-key"
export LIVEKIT_API_SECRET="test-secret"
export VOICE_AGENT_DEFAULT_ROOM="hindi-demo-test"

echo "1. Verifying setup..."
python voice_agent/verify_setup.py

echo ""
echo "2. Running unit tests..."
pytest tests/ -v --tb=short

echo ""
echo "3. Testing with demo conversations..."
python demo_three_brains.py

echo ""
echo "4. Starting voice agent (Ctrl+C to stop)..."
python -m voice_agent.main --room hindi-demo-test --identity pipecat-agent-1

