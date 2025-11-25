"""
Reflex Brain (L0) - Hard real-time UX layer.

Emits short Hindi/Hinglish backchannels immediately when latency
budget is tight, to keep the conversation feeling responsive.
"""

import random
from typing import Callable, Awaitable
from loguru import logger


# Pre-defined Hindi/Hinglish reflex phrases
REFLEX_PHRASES = [
    "haan ji, ek second",
    "jee, dekh raha hoon",
    "ek minute, main check karta hoon",
    "haan, batata hoon",
    "theek hai, ek second",
    "ji haan, dekhte hain",
]


def choose_reflex_phrase() -> str:
    """
    Choose a random reflex phrase.
    
    Returns:
        A Hindi/Hinglish backchannel phrase
    """
    return random.choice(REFLEX_PHRASES)


async def maybe_emit_reflex(
    should_reflex: bool,
    send_text: Callable[[str], Awaitable[None]],
) -> None:
    """
    Conditionally emit a reflex phrase.
    
    If should_reflex is True, immediately sends a backchannel phrase
    to TTS to keep the conversation feeling responsive while the
    speculative brain is thinking.
    
    Args:
        should_reflex: Whether to emit the reflex
        send_text: Async function to send text to TTS
    """
    if not should_reflex:
        logger.debug("Reflex brain: Skipped (not needed)")
        return
    
    phrase = choose_reflex_phrase()
    logger.info(f"🎯 REFLEX BRAIN (L0): Emitting '{phrase}'")
    
    await send_text(phrase)


async def emit_reflex(
    send_text: Callable[[str], Awaitable[None]],
    custom_phrase: str = None,
) -> None:
    """
    Unconditionally emit a reflex phrase.
    
    Args:
        send_text: Async function to send text to TTS
        custom_phrase: Optional custom phrase to use instead of random
    """
    phrase = custom_phrase or choose_reflex_phrase()
    logger.info(f"🎯 REFLEX BRAIN (L0): Emitting '{phrase}'")
    
    await send_text(phrase)



