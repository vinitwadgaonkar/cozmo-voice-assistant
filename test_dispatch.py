#!/usr/bin/env python3
"""
Test script to explicitly dispatch an agent to a room using LiveKit API.
This can help test if the agent works when explicitly dispatched.
"""
import asyncio
from livekit import api
from server.config import settings

async def test_explicit_dispatch():
    """Explicitly dispatch the agent to a test room."""
    lkapi = api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET
    )
    
    room_name = "test-room-123"
    
    try:
        # Create explicit dispatch
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="",  # Empty for automatic dispatch agent
                room=room_name,
                metadata='{"test": "true"}'
            )
        )
        print(f"✅ Created dispatch: {dispatch}")
        
        # List dispatches
        dispatches = await lkapi.agent_dispatch.list_dispatch(room_name=room_name)
        print(f"📋 There are {len(dispatches)} dispatches in {room_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(test_explicit_dispatch())

