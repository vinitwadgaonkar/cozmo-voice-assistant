"""
Provider routing logic based on latency predictions.

Makes decisions about which brain to use, when to trigger reflexes,
and when to run shadow traffic.
"""

import random
from typing import Optional
from loguru import logger

from .metrics import LatencyOracle


def should_trigger_reflex(
    oracle: LatencyOracle,
    target_latency_ms: int,
    primary_provider_id: str,
) -> bool:
    """
    Decide whether to trigger the reflex brain.
    
    If the predicted total latency for the primary provider exceeds
    the target, we should emit a reflex phrase to keep the conversation
    feeling responsive.
    
    Args:
        oracle: Latency oracle with historical data
        target_latency_ms: Target response time (e.g., 150ms)
        primary_provider_id: The provider we plan to use for L1
    
    Returns:
        True if reflex should be triggered
    """
    predicted_ms = oracle.predict_total_ms(primary_provider_id)
    should_reflex = predicted_ms > target_latency_ms
    
    if should_reflex:
        logger.info(
            f"🎯 REFLEX TRIGGERED: Predicted {predicted_ms:.0f}ms > target {target_latency_ms}ms"
        )
    else:
        logger.debug(
            f"No reflex needed: Predicted {predicted_ms:.0f}ms <= target {target_latency_ms}ms"
        )
    
    return should_reflex


def choose_llm_for_turn(
    oracle: LatencyOracle,
    groq_available: bool = False,
    fast_threshold_ms: float = 150.0,
    quality_threshold: float = 0.8,
) -> str:
    """
    Choose which LLM provider to use for the speculative (L1) brain.
    
    Supports:
    - "groq-l1" - Ultra-fast Groq model (llama-3.1-70b)
    - "openai-l1" - Fast OpenAI model (gpt-4o-mini)
    - "openai-l2" - Fallback OpenAI model
    
    Selection criteria (in order):
    1. Provider must be available (no recent errors)
    2. Quality score above threshold
    3. Lowest predicted latency
    
    Args:
        oracle: Latency oracle with historical data
        groq_available: Whether Groq is configured
        fast_threshold_ms: Threshold for "fast enough"
        quality_threshold: Minimum quality score required
    
    Returns:
        Provider ID string like "groq-l1" or "openai-l1"
    """
    candidates = []
    
    # Build list of available providers
    if groq_available:
        groq_stats = oracle.get_stats("groq-l1")
        if groq_stats.is_available and groq_stats.quality_score >= quality_threshold:
            predicted_latency = oracle.predict_first_token_ms("groq-l1")
            candidates.append(("groq-l1", predicted_latency, groq_stats.quality_score))
    
    # Always consider OpenAI as fallback
    openai_stats = oracle.get_stats("openai-l1")
    if openai_stats.is_available and openai_stats.quality_score >= quality_threshold:
        predicted_latency = oracle.predict_first_token_ms("openai-l1")
        candidates.append(("openai-l1", predicted_latency, openai_stats.quality_score))
    
    # Fallback to L2 model if L1 is down
    if not candidates:
        logger.warning("No L1 providers available, falling back to openai-l2")
        return "openai-l2"
    
    # Sort by latency (lower is better), then by quality (higher is better)
    candidates.sort(key=lambda x: (x[1], -x[2]))
    
    chosen = candidates[0]
    provider_id, predicted_ms, quality = chosen
    
    logger.info(
        f"Choosing {provider_id} for L1 brain: "
        f"predicted_latency={predicted_ms:.0f}ms, quality={quality:.2f}"
    )
    
    return provider_id


def should_run_shadow_traffic(probability: float = 0.1) -> bool:
    """
    Decide whether to run shadow traffic for this turn.
    
    Shadow traffic runs alternate models in the background to measure
    their performance without affecting the user experience.
    
    Args:
        probability: Probability of running shadow traffic (0.0 to 1.0)
    
    Returns:
        True if shadow traffic should run
    """
    should_run = random.random() < probability
    if should_run:
        logger.info("🔬 SHADOW TRAFFIC: Will run alternate model in background")
    return should_run


def choose_shadow_provider(primary_provider: str) -> Optional[str]:
    """
    Choose an alternate provider for shadow traffic.
    
    Args:
        primary_provider: The provider being used for the actual response
    
    Returns:
        Shadow provider ID, or None if no suitable alternative
    """
    # Map primary providers to their shadow alternatives
    shadow_map = {
        "openai-l1": "openai-l2-shadow",
        "openai-l2": "openai-l1-shadow",
    }
    
    shadow = shadow_map.get(primary_provider)
    if shadow:
        logger.debug(f"Shadow provider for {primary_provider}: {shadow}")
    return shadow


def get_l2_provider(l1_provider: str) -> str:
    """
    Get the L2 (deep brain) provider for a given L1 provider.
    
    Args:
        l1_provider: The L1 provider ID
    
    Returns:
        L2 provider ID
    """
    # For now, L2 is always openai-l2
    # Later this could be more sophisticated
    return "openai-l2"


def should_skip_deep_brain(semantic_tag: dict, oracle: LatencyOracle) -> bool:
    """
    Decide whether to skip the deep brain for this turn.
    
    Args:
        semantic_tag: Semantic tag from L1
        oracle: Latency oracle for checking system load
    
    Returns:
        True if deep brain should be skipped
    """
    urgency = semantic_tag.get("urgency", "medium")
    intent = semantic_tag.get("intent", "unknown")
    
    # Skip for high-urgency requests
    if urgency == "high":
        logger.debug("Skipping L2: high urgency")
        return True
    
    # Skip for trivial chitchat
    if intent == "chitchat" and semantic_tag.get("length_hint") == "short":
        logger.debug("Skipping L2: trivial chitchat")
        return True
    
    return False


def should_skip_reflex(semantic_tag: dict = None) -> bool:
    """
    Decide whether to skip reflex for trivial queries.
    
    Args:
        semantic_tag: Optional semantic tag from previous analysis
    
    Returns:
        True if reflex should be skipped
    """
    if not semantic_tag:
        return False
    
    # Skip reflex for very simple queries
    intent = semantic_tag.get("intent", "unknown")
    if intent in ["greeting", "farewell", "acknowledgment"]:
        logger.debug("Skipping reflex: trivial query")
        return True
    
    return False


def log_routing_decision(
    turn_id: str,
    l1_provider: str,
    l2_provider: str,
    reflex_triggered: bool,
    shadow_running: bool,
) -> None:
    """
    Log a summary of routing decisions for this turn.
    
    Args:
        turn_id: Unique turn identifier
        l1_provider: Chosen L1 provider
        l2_provider: Chosen L2 provider
        reflex_triggered: Whether reflex was triggered
        shadow_running: Whether shadow traffic is running
    """
    logger.info("=" * 60)
    logger.info(f"ROUTING DECISION - Turn {turn_id}")
    logger.info(f"  Reflex Brain (L0): {'✓ ACTIVE' if reflex_triggered else '✗ skipped'}")
    logger.info(f"  Speculative Brain (L1): {l1_provider}")
    logger.info(f"  Deep Brain (L2): {l2_provider}")
    logger.info(f"  Shadow Traffic: {'✓ RUNNING' if shadow_running else '✗ disabled'}")
    logger.info("=" * 60)



