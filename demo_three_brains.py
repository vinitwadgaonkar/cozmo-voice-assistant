#!/usr/bin/env python3
"""
Demo script for three-brain architecture.

Tests the reflex, speculative, and deep brains without requiring
full LiveKit/Pipecat setup. Shows how the architecture works.

Usage:
    python demo_three_brains.py
"""

import asyncio
import os
from loguru import logger
from dotenv import load_dotenv

# Load environment
load_dotenv()

from voice_agent.metrics import LatencyOracle, LatencyTimer
from voice_agent.router import (
    should_trigger_reflex,
    choose_llm_for_turn,
    should_run_shadow_traffic,
    log_routing_decision,
)
from voice_agent.brains.reflex import choose_reflex_phrase
from voice_agent.brains.speculative import generate_speculative_reply
from voice_agent.brains.deep import generate_deep_reply

from openai import AsyncOpenAI


async def simulate_turn(
    turn_id: str,
    transcript: str,
    oracle: LatencyOracle,
    openai_client: AsyncOpenAI,
    target_latency_ms: int = 150,
):
    """Simulate one conversation turn through the three-brain system."""
    
    logger.info("=" * 70)
    logger.info(f"🎤 TURN: {turn_id}")
    logger.info(f"User said: {transcript}")
    logger.info("=" * 70)
    
    # Step 1: Make routing decisions
    l1_provider = choose_llm_for_turn(oracle)
    l2_provider = "openai-l2"
    should_reflex = should_trigger_reflex(oracle, target_latency_ms, l1_provider)
    should_shadow = should_run_shadow_traffic(probability=0.3)  # 30% for demo
    
    log_routing_decision(turn_id, l1_provider, l2_provider, should_reflex, should_shadow)
    
    # Step 2: Emit reflex if needed
    if should_reflex:
        reflex_phrase = choose_reflex_phrase()
        logger.info(f"🎯 REFLEX BRAIN (L0): '{reflex_phrase}'")
        logger.info(f"   [User hears this immediately]")
    
    # Step 3: Generate speculative answer (L1)
    logger.info(f"\n🧠 SPECULATIVE BRAIN (L1): Thinking...")
    timer_l1 = LatencyTimer("L1")
    with timer_l1:
        timer_l1.mark_first_token()
        answer_l1, semantic_tag = await generate_speculative_reply(
            client=openai_client,
            model="gpt-4o-mini",
            transcript=transcript,
        )
    
    oracle.record(l1_provider, timer_l1.first_token_ms, timer_l1.total_ms)
    logger.info(f"   Answer: {answer_l1}")
    logger.info(f"   Tag: {semantic_tag}")
    logger.info(f"   ⏱️  Latency: {timer_l1.total_ms:.0f}ms")
    logger.info(f"   [User hears this at {timer_l1.total_ms:.0f}ms]")
    
    # Step 4: Launch deep brain (L2) - simulate async
    logger.info(f"\n🧠 DEEP BRAIN (L2): Analyzing...")
    timer_l2 = LatencyTimer("L2")
    with timer_l2:
        timer_l2.mark_first_token()
        follow_up = await generate_deep_reply(
            client=openai_client,
            model="gpt-4o-mini",
            transcript=transcript,
            speculative_answer=answer_l1,
            semantic_tag=semantic_tag,
        )
    
    oracle.record(l2_provider, timer_l2.first_token_ms, timer_l2.total_ms)
    
    if follow_up:
        logger.info(f"   Follow-up: {follow_up}")
        logger.info(f"   ⏱️  Latency: {timer_l2.total_ms:.0f}ms")
        logger.info(f"   [User hears this at {timer_l1.total_ms + timer_l2.total_ms:.0f}ms]")
    else:
        logger.info(f"   (No follow-up needed)")
    
    # Step 5: Run shadow traffic
    if should_shadow:
        logger.info(f"\n🔬 SHADOW TRAFFIC: Testing alternate model...")
        timer_shadow = LatencyTimer("Shadow")
        with timer_shadow:
            timer_shadow.mark_first_token()
            answer_shadow, _ = await generate_speculative_reply(
                client=openai_client,
                model="gpt-4o-mini",  # In real system, would use alternate
                transcript=transcript,
            )
        
        oracle.record("openai-l2-shadow", timer_shadow.first_token_ms, timer_shadow.total_ms)
        logger.info(f"   Shadow answer: {answer_shadow[:80]}...")
        logger.info(f"   ⏱️  Shadow latency: {timer_shadow.total_ms:.0f}ms")
        logger.info(f"   [Metrics recorded, user never hears this]")
    
    logger.info(f"\n✅ Turn {turn_id} complete\n")


async def main():
    """Run demo with sample conversations."""
    
    # Check if OpenAI key is set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set in environment!")
        logger.error("Please set it in .env file or export it")
        return 1
    
    logger.info("=" * 70)
    logger.info("THREE-BRAIN ARCHITECTURE DEMO")
    logger.info("=" * 70)
    logger.info("")
    logger.info("This demo shows how the three-brain system works:")
    logger.info("  L0 (Reflex): Instant backchannels")
    logger.info("  L1 (Speculative): Fast answers")
    logger.info("  L2 (Deep): Rich follow-ups")
    logger.info("  Oracle: Tracks latencies and makes routing decisions")
    logger.info("  Shadow: Tests alternate models in background")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    
    # Initialize
    oracle = LatencyOracle()
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Sample conversations
    conversations = [
        "Namaste, aap kaise hain?",
        "Delhi mein traffic kaisa hai aaj?",
        "Mausam kaisa rahega kal?",
        "Mere paas ek technical question hai",
        "Main ek appointment book karna chahta hoon",
    ]
    
    for i, transcript in enumerate(conversations, 1):
        await simulate_turn(
            turn_id=f"turn-{i}",
            transcript=transcript,
            oracle=oracle,
            openai_client=openai_client,
            target_latency_ms=150,
        )
        
        # Brief pause between turns
        await asyncio.sleep(0.5)
    
    # Final summary
    logger.info("=" * 70)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 70)
    logger.info("")
    oracle.log_summary()
    logger.info("")
    logger.info("✅ Demo complete!")
    logger.info("")
    logger.info("What you saw:")
    logger.info("  1. Reflex brain triggered when predicted latency was high")
    logger.info("  2. Speculative brain gave fast initial answers")
    logger.info("  3. Deep brain added follow-ups or corrections")
    logger.info("  4. Shadow traffic tested alternate models in background")
    logger.info("  5. Latency oracle tracked all metrics")
    logger.info("")
    logger.info("In production, this runs with LiveKit audio transport.")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))



