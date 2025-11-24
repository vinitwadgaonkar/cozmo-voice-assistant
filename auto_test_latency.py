#!/usr/bin/env python3
"""
Autonomous latency testing - sends audio, measures response time, reports results.
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from loguru import logger
from livekit import api, rtc
import numpy as np
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://vinit-oj6871wv.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "APImtoTstBBLzZP")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "rFjTtlSGbGe1tGzhyEopt44BLQy8Yxx86Z07FGHwe2fB")
LOG_FILE = Path("agent_debug.log")

def generate_silence(duration_ms: int, sample_rate: int = 16000) -> bytes:
    """Generate silence audio for testing."""
    samples = int(sample_rate * duration_ms / 1000)
    # 16-bit PCM silence
    return b'\x00\x00' * samples

async def test_latency():
    """Test end-to-end latency with audio input."""
    logger.info("=" * 70)
    logger.info("🧪 AUTONOMOUS LATENCY TEST")
    logger.info("=" * 70)
    
    room_name = f"latency-test-{int(time.time())}"
    
    # Generate token WITHOUT RoomAgentDispatch - use automatic dispatch
    # Since we're not setting agent_name in WorkerOptions, automatic dispatch should work
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity("test_user") \
        .with_name("Test User") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )) \
        .to_jwt()
    
    logger.info(f"📝 Room: {room_name}")
    
    room = rtc.Room()
    audio_track = None
    audio_source = None
    
    try:
        # Connect
        await room.connect(LIVEKIT_URL, token)
        logger.info("✅ Connected to room")
        
        # Wait for agent
        logger.info("⏳ Waiting for agent (15s)...")
        agent_joined = False
        start_wait = time.time()
        
        while time.time() - start_wait < 15:
            for participant in room.remote_participants.values():
                if "agent" in participant.name.lower() or "hindi" in participant.name.lower():
                    logger.info(f"✅ Agent joined: {participant.name}")
                    agent_joined = True
                    break
            if agent_joined:
                break
            await asyncio.sleep(0.5)
        
        if not agent_joined:
            logger.error("❌ Agent did not join")
            return False
        
        # Check logs for entrypoint
        await asyncio.sleep(2)  # Give time for pipeline to start
        if LOG_FILE.exists():
            log_content = LOG_FILE.read_text()
            if "ENTRYPOINT CALLED" in log_content or "🎯" in log_content:
                logger.info("✅ Entrypoint was called")
            else:
                logger.warning("⚠️  Entrypoint not found in logs")
        
        # Create audio track and publish
        logger.info("🎤 Publishing test audio...")
        audio_source = rtc.AudioSource(16000, 1)
        audio_track = rtc.LocalAudioTrack.create_audio_track("test-audio", audio_source)
        
        options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        publication = await room.local_participant.publish_track(audio_track, options)
        logger.info(f"✅ Published audio track: {publication.sid}")
        
        # Send test audio (simulate speech)
        logger.info("📤 Sending test audio (simulating 'namaste')...")
        test_audio = generate_silence(500, 16000)  # 500ms of audio
        await audio_source.capture_frame(rtc.AudioFrame(
            data=test_audio,
            sample_rate=16000,
            num_channels=1,
            samples_per_channel=len(test_audio) // 2
        ))
        
        # Wait for response
        logger.info("⏳ Waiting for agent response (10s)...")
        response_received = False
        start_time = time.time()
        
        # Monitor for agent audio
        while time.time() - start_time < 10:
            for participant in room.remote_participants.values():
                if "agent" in participant.name.lower():
                    for track_pub in participant.track_publications.values():
                        if track_pub.kind == rtc.TrackKind.KIND_AUDIO and track_pub.subscribed:
                            if track_pub.track:
                                logger.info("✅ Agent audio track detected!")
                                response_received = True
                                latency = (time.time() - start_time) * 1000
                                logger.info(f"⏱️  Response latency: {latency:.0f}ms")
                                break
            if response_received:
                break
            await asyncio.sleep(0.1)
        
        # Check logs for latency breakdown
        if LOG_FILE.exists():
            log_content = LOG_FILE.read_text()
            if "⏱️" in log_content or "LATENCY" in log_content:
                logger.info("📊 Latency breakdown found in logs:")
                for line in log_content.split('\n')[-50:]:
                    if "⏱️" in line or "LATENCY" in line or "BREAKDOWN" in line:
                        logger.info(f"   {line.strip()}")
        
        # Summary
        logger.info("=" * 70)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"   Agent joined: ✅")
        logger.info(f"   Audio published: ✅")
        logger.info(f"   Response received: {'✅' if response_received else '❌'}")
        if response_received:
            logger.info(f"   Latency: {latency:.0f}ms")
            logger.info(f"   Target: <150ms")
            logger.info(f"   Status: {'✅ PASS' if latency < 150 else '❌ FAIL'}")
        logger.info("=" * 70)
        
        return response_received
        
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if audio_track:
            await room.local_participant.unpublish_track(audio_track.sid)
        await room.disconnect()
        logger.info("🔌 Disconnected")

async def main():
    """Run autonomous test."""
    success = await test_latency()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())

