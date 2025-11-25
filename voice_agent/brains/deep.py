"""
Deep Brain (L2) - Slower, corrective/richer responses.

Runs asynchronously after the speculative answer to provide
extensions, corrections, or additional context.
"""

from typing import Optional
from loguru import logger
from openai import AsyncOpenAI


async def generate_deep_reply(
    client: AsyncOpenAI,
    model: str,
    transcript: str,
    speculative_answer: str,
    semantic_tag: dict = None,
) -> Optional[str]:
    """
    Generate a deep, considered reply using L2 brain.
    
    This runs asynchronously after the L1 answer has been spoken.
    It can:
    - Extend the answer with more detail
    - Provide a correction if L1 was wrong
    - Add context or follow-up information
    - Return None if L1 answer was sufficient
    
    Args:
        client: OpenAI async client
        model: Model name (e.g., "gpt-4o" or same as L1)
        transcript: Original user transcript
        speculative_answer: The L1 answer that was already spoken
        semantic_tag: Optional semantic tag from L1
    
    Returns:
        Follow-up text to speak, or None if no follow-up needed
    """
    logger.info(f"🧠 DEEP BRAIN (L2): Analyzing with model {model}")
    
    system_prompt = """You are a thoughtful Hindi voice assistant providing follow-up.

You already gave a quick answer. Now, review it and decide:
1. If it was complete and correct, respond with: "SUFFICIENT"
2. If you can add useful detail, start with: "Accha, ek aur detail..." then add 1-2 sentences
3. If you need to correct something, start with: "Accha, ek correction..." then correct it

Keep follow-ups brief. This is spoken conversation."""

    user_prompt = f"""User said: {transcript}

Your quick answer was: {speculative_answer}

Should you add anything or correct?"""

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=150,
        )
        
        content = response.choices[0].message.content.strip()
        logger.debug(f"L2 raw response: {content}")
        
        # Check if follow-up is needed
        if content.upper().startswith("SUFFICIENT"):
            logger.info("🧠 L2: No follow-up needed (answer was sufficient)")
            return None
        
        logger.info(f"🧠 L2 Follow-up: {content}")
        return content
        
    except Exception as e:
        logger.error(f"Error in deep brain: {e}")
        return None


async def run_deep_brain_async(
    client: AsyncOpenAI,
    model: str,
    transcript: str,
    speculative_answer: str,
    semantic_tag: dict,
    send_text: callable,
) -> None:
    """
    Run the deep brain asynchronously and send follow-up if needed.
    
    This is meant to be launched as an asyncio task that runs in
    the background while the L1 answer is being spoken.
    
    Args:
        client: OpenAI async client
        model: Model name
        transcript: Original user transcript
        speculative_answer: The L1 answer
        semantic_tag: Semantic tag from L1
        send_text: Async function to send text to TTS
    """
    logger.info("🧠 DEEP BRAIN (L2): Starting async analysis...")
    
    try:
        follow_up = await generate_deep_reply(
            client=client,
            model=model,
            transcript=transcript,
            speculative_answer=speculative_answer,
            semantic_tag=semantic_tag,
        )
        
        if follow_up:
            logger.info(f"🧠 DEEP BRAIN (L2): Sending follow-up: {follow_up}")
            await send_text(follow_up)
        else:
            logger.info("🧠 DEEP BRAIN (L2): No follow-up needed")
            
    except Exception as e:
        logger.error(f"Error in async deep brain: {e}")


def should_run_deep_brain(semantic_tag: dict) -> bool:
    """
    Decide whether to run the deep brain for this turn.
    
    For the POC, we always run it, but this could be more sophisticated
    based on the semantic tag (e.g., skip for simple chitchat).
    
    Args:
        semantic_tag: Semantic tag from L1
    
    Returns:
        True if deep brain should run
    """
    # For now, always run L2 to demonstrate the architecture
    # In production, you might skip it for:
    # - Very simple queries (intent="chitchat", length_hint="short")
    # - Time-sensitive responses (urgency="high")
    
    intent = semantic_tag.get("intent", "unknown")
    urgency = semantic_tag.get("urgency", "medium")
    
    if urgency == "high":
        logger.info("🧠 L2: Skipping due to high urgency")
        return False
    
    return True



