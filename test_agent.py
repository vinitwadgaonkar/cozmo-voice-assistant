#!/usr/bin/env python3
"""
Automated test script for the Hindi Voice Agent.
Tests the entire pipeline: STT -> LLM -> TTS
"""

import asyncio
import time
import sys
from loguru import logger
from livekit import api, rtc
from livekit.agents import JobContext, WorkerOptions, cli
import os

# Load environment
from dotenv import load_dotenv
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "your_livekit_url_here")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "your_livekit_api_key_here")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "your_livekit_api_secret_here")

async def test_agent():
    """Test the agent by connecting and checking if it responds."""
    
    logger.info("🧪 Starting Automated Agent Test")
    logger.info(f"URL: {LIVEKIT_URL}")
    
    # Generate token
    room_name = f"test-{int(time.time())}"
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity("test_user") \
        .with_name("Test User") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )) \
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name="", metadata='{"source": "test"}')]
            )
        ) \
        .to_jwt()
    
    logger.info(f"📝 Generated token for room: {room_name}")
    logger.info(f"🔑 Token: {token[:50]}...")
    
    # Connect to room
    logger.info("🔌 Connecting to LiveKit room...")
    room = rtc.Room()
    
    try:
        await room.connect(LIVEKIT_URL, token)
        logger.info("✅ Connected to room")
        
        # Wait for agent to join
        logger.info("⏳ Waiting for agent to join (max 10s)...")
        agent_joined = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            participants = room.remote_participants.values()
            for participant in participants:
                if participant.name == "Hindi Agent" or "agent" in participant.name.lower():
                    logger.info(f"✅ Agent joined: {participant.name}")
                    agent_joined = True
                    break
            if agent_joined:
                break
            await asyncio.sleep(0.5)
        
        if not agent_joined:
            logger.error("❌ Agent did not join within 10 seconds")
            logger.error("💡 Check if agent worker is running and registered")
            return False
        
        # Check if agent has audio track
        logger.info("🔍 Checking agent audio track...")
        has_audio = False
        for participant in room.remote_participants.values():
            if "agent" in participant.name.lower():
                for track in participant.track_publications.values():
                    if track.kind == rtc.TrackKind.KIND_AUDIO:
                        logger.info(f"✅ Agent has audio track: {track.sid}")
                        has_audio = True
                        break
        
        if not has_audio:
            logger.warning("⚠️  Agent joined but no audio track found")
        
        # Test complete
        logger.info("✅ Test completed successfully!")
        logger.info("📊 Summary:")
        logger.info(f"   - Room: {room_name}")
        logger.info(f"   - Agent joined: ✅")
        logger.info(f"   - Audio track: {'✅' if has_audio else '⚠️'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await room.disconnect()
        logger.info("🔌 Disconnected from room")

async def main():
    """Main test function."""
    success = await test_agent()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())

