#!/usr/bin/env python3
"""
Generate a LiveKit room token with agent dispatch for testing in the Playground.
This uses token-based dispatch - the agent will automatically join when you connect.
"""
import os
from livekit import api

# Your LiveKit credentials (set via environment variables)
import os
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "your_livekit_url_here")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "your_livekit_api_key_here")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "your_livekit_api_secret_here")

# Room name (use any name you want, or leave empty for auto-generated)
ROOM_NAME = "playground-test"

def generate_token(room_name: str = "playground-test", participant_name: str = "user", use_automatic_dispatch: bool = True):
    """Generate a LiveKit access token.
    
    Args:
        room_name: Name of the room to join
        participant_name: Name of the participant
        use_automatic_dispatch: If True, rely on automatic dispatch (no RoomAgentDispatch in token).
                                If False, use explicit dispatch with RoomAgentDispatch.
    """
    
    # For automatic dispatch (default): Don't include RoomAgentDispatch in token
    # The agent will be automatically dispatched when participant joins
    if use_automatic_dispatch:
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(participant_name) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )) \
            .to_jwt()
    else:
        # For explicit dispatch: Include RoomAgentDispatch in token
        # Note: This requires agent_name to be set in WorkerOptions
        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(participant_name) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )) \
            .with_room_config(
                api.RoomConfiguration(
                    agents=[
                        api.RoomAgentDispatch(
                            agent_name="",  # Empty = automatic dispatch agent
                            metadata='{"source": "playground"}'
                        )
                    ]
                )
            ) \
            .to_jwt()
    
    return token

if __name__ == "__main__":
    print("=" * 60)
    print("LiveKit Room Token Generator")
    print("=" * 60)
    print(f"\nURL: {LIVEKIT_URL}")
    print(f"Room: {ROOM_NAME}")
    print("\nUsing AUTOMATIC dispatch (agent will join automatically)")
    print("Generating token...\n")
    
    # Try both: automatic dispatch first, then explicit if needed
    # According to docs: automatic dispatch works when agent_name is NOT set in worker
    # Token-based dispatch works with RoomAgentDispatch
    print("\nOption 1: Automatic Dispatch (no RoomAgentDispatch)")
    token1 = generate_token(ROOM_NAME, use_automatic_dispatch=True)
    print(token1)
    print("\n" + "=" * 60)
    print("Option 2: Explicit Dispatch (with RoomAgentDispatch)")
    token2 = generate_token(ROOM_NAME, use_automatic_dispatch=False)
    print(token2)
    print("=" * 60)
    
    # Return explicit dispatch token (more reliable)
    token = token2
    
    print("=" * 60)
    print("TOKEN (copy this):")
    print("=" * 60)
    print(token)
    print("=" * 60)
    print("\nInstructions:")
    print("1. Copy the URL above")
    print("2. Copy the token above")
    print("3. Paste them in the LiveKit Playground")
    print("4. Click 'Connect'")
    print("5. Agent will automatically dispatch when you join")
    print("=" * 60)

