#!/usr/bin/env python3
"""
Comprehensive automated test for Hindi Voice Agent.
Tests connectivity, logs analysis, and provides diagnostics.
"""

import asyncio
import time
import sys
import os
from loguru import logger
from livekit import api, rtc
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "your_livekit_url_here")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "your_livekit_api_key_here")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "your_livekit_api_secret_here")
LOG_FILE = Path("agent_debug.log")

def check_logs():
    """Check agent logs for issues."""
    logger.info("📋 Checking agent logs...")
    
    if not LOG_FILE.exists():
        logger.warning("⚠️  Log file not found")
        return False
    
    log_content = LOG_FILE.read_text()
    
    # Check for entrypoint calls
    has_entrypoint = "ENTRYPOINT CALLED" in log_content or "🎯" in log_content
    has_errors = "Error" in log_content or "Exception" in log_content or "Traceback" in log_content
    has_registered = "registered worker" in log_content
    
    logger.info(f"   - Worker registered: {'✅' if has_registered else '❌'}")
    logger.info(f"   - Entrypoint called: {'✅' if has_entrypoint else '❌'}")
    logger.info(f"   - Errors found: {'⚠️' if has_errors else '✅'}")
    
    if has_errors:
        logger.warning("   Checking for specific errors...")
        errors = []
        for line in log_content.split('\n'):
            if any(keyword in line for keyword in ["Error", "Exception", "Traceback", "Failed"]):
                errors.append(line.strip())
        if errors:
            logger.warning(f"   Found {len(errors)} error lines")
            for err in errors[-5:]:  # Show last 5 errors
                logger.warning(f"     {err[:100]}")
    
    return has_registered

async def test_connection():
    """Test LiveKit connection and agent dispatch."""
    logger.info("🧪 Testing LiveKit Connection")
    
    room_name = f"auto-test-{int(time.time())}"
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
                agents=[api.RoomAgentDispatch(agent_name="", metadata='{"source": "auto-test"}')]
            )
        ) \
        .to_jwt()
    
    logger.info(f"📝 Room: {room_name}")
    
    room = rtc.Room()
    try:
        await room.connect(LIVEKIT_URL, token)
        logger.info("✅ Connected to room")
        
        # Wait for agent
        logger.info("⏳ Waiting for agent (10s)...")
        agent_joined = False
        start_time = time.time()
        
        while time.time() - start_time < 10:
            for participant in room.remote_participants.values():
                if "agent" in participant.name.lower() or "hindi" in participant.name.lower():
                    logger.info(f"✅ Agent joined: {participant.name}")
                    agent_joined = True
                    
                    # Check tracks
                    audio_tracks = [t for t in participant.track_publications.values() 
                                  if t.kind == rtc.TrackKind.KIND_AUDIO]
                    logger.info(f"   Audio tracks: {len(audio_tracks)}")
                    
                    break
            if agent_joined:
                break
            await asyncio.sleep(0.5)
        
        return agent_joined
        
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    finally:
        await room.disconnect()

async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("🤖 Automated Agent Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Check logs
    logger.info("\n📋 Test 1: Log Analysis")
    log_ok = check_logs()
    
    # Test 2: Connection test
    logger.info("\n🔌 Test 2: LiveKit Connection")
    conn_ok = await test_connection()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Summary")
    logger.info("=" * 60)
    logger.info(f"   Logs:        {'✅ PASS' if log_ok else '❌ FAIL'}")
    logger.info(f"   Connection:  {'✅ PASS' if conn_ok else '❌ FAIL'}")
    logger.info(f"   Overall:     {'✅ PASS' if (log_ok and conn_ok) else '❌ FAIL'}")
    logger.info("=" * 60)
    
    if not conn_ok:
        logger.error("\n💡 Troubleshooting:")
        logger.error("   1. Check if agent worker is running: ps aux | grep 'python server/main.py'")
        logger.error("   2. Check agent logs: tail -f agent_debug.log")
        logger.error("   3. Verify environment variables are set")
        logger.error("   4. Check LiveKit dashboard for agent status")
    
    return log_ok and conn_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

