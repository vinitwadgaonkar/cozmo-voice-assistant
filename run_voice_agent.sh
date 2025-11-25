#!/bin/bash
# Convenience script to run the Hindi LiveKit voice agent

# Default values (can be overridden with environment variables)
ROOM="${VOICE_AGENT_DEFAULT_ROOM:-cozmo-hindi-test}"
IDENTITY="${VOICE_AGENT_DEFAULT_IDENTITY:-pipecat-agent-1}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --room)
            ROOM="$2"
            shift 2
            ;;
        --identity)
            IDENTITY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--room ROOM_NAME] [--identity IDENTITY]"
            echo ""
            echo "Options:"
            echo "  --room ROOM_NAME       LiveKit room name (default: cozmo-hindi-test)"
            echo "  --identity IDENTITY    Participant identity (default: pipecat-agent-1)"
            echo "  --help                 Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --room my-room --identity my-agent"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Run the voice agent
echo "Starting Hindi LiveKit voice agent..."
echo "Room: $ROOM"
echo "Identity: $IDENTITY"
echo ""

python -m voice_agent.main --room "$ROOM" --identity "$IDENTITY"

