"""
Speculative Brain (L1) - Fast, shallow answer generation.

Uses a fast OpenAI/Groq model to generate short, safe initial responses
with semantic tagging for downstream decision-making.

Supports multiple LLM providers: OpenAI, Groq, etc.
"""

import json
from typing import Tuple, Dict, Any, Optional, Union
from loguru import logger
from openai import AsyncOpenAI
import asyncio

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None


async def generate_speculative_reply_multi_provider(
    client: Union[AsyncOpenAI, Any],
    model: str,
    transcript: str,
    provider: str = "openai-l1",
    timeout_seconds: float = 5.0,
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a fast, speculative reply supporting multiple LLM providers.
    
    Supports:
    - OpenAI (gpt-4o-mini, gpt-4o)
    - Groq (llama-3.1-70b-versatile, llama-3.1-8b-instant)
    
    Produces:
    1. A short (1-2 sentence) Hindi/Hinglish answer
    2. A semantic tag with metadata about the turn
    
    Args:
        client: AsyncOpenAI or AsyncGroq client
        model: Model name
        transcript: User's speech transcript
        provider: Provider ID for logging (e.g., "groq-l1", "openai-l1")
        timeout_seconds: Timeout for API call
    
    Returns:
        Tuple of (answer_text, semantic_tag_dict)
    """
    logger.info(f"SPECULATIVE BRAIN (L1): Generating reply with {provider} / {model}")
    
    system_prompt = """You are a helpful Hindi voice assistant. 
    
Your task is to provide:
1. A SHORT answer in Hindi or Hinglish (1-2 sentences maximum)
2. A semantic tag as JSON

Format your response as:
ANSWER: [your 1-2 sentence answer]
TAG: {"intent": "question|command|chitchat|...", "urgency": "low|medium|high", "length_hint": "short|long"}

Keep answers concise and conversational. This is a spoken conversation."""

    # Try with timeout
    try:
        async def _generate():
            # Both OpenAI and Groq use same API structure
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript},
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return response.choices[0].message.content
        
        content = await asyncio.wait_for(_generate(), timeout=timeout_seconds)
        
        logger.debug(f"L1 raw response ({provider}): {content}")
        answer, tag = _parse_l1_response(content)
        
        logger.info(f"L1 Answer ({provider}): {answer}")
        logger.info(f"L1 Tag: {tag}")
        
        return answer, tag
        
    except asyncio.TimeoutError:
        logger.error(f"L1 timeout after {timeout_seconds}s for {provider}")
        return _fallback_response(transcript, f"{provider}_timeout")
        
    except Exception as e:
        logger.error(f"Error in speculative brain ({provider}): {e}")
        return _fallback_response(transcript, f"{provider}_{str(e)}")


async def generate_speculative_reply(
    client: AsyncOpenAI,
    model: str,
    transcript: str,
    timeout_seconds: float = 5.0,
    groq_client: Optional[Any] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a fast, speculative reply using L1 brain with retry logic.
    
    Produces:
    1. A short (1-2 sentence) Hindi/Hinglish answer
    2. A semantic tag with metadata about the turn
    
    Args:
        client: OpenAI async client
        model: Model name (e.g., "gpt-4o-mini")
        transcript: User's speech transcript
        timeout_seconds: Timeout for API call
        groq_client: Optional Groq client for alternate provider
    
    Returns:
        Tuple of (answer_text, semantic_tag_dict)
    """
    logger.info(f"SPECULATIVE BRAIN (L1): Generating reply with model {model}")
    
    system_prompt = """You are a helpful Hindi voice assistant. 
    
Your task is to provide:
1. A SHORT answer in Hindi or Hinglish (1-2 sentences maximum)
2. A semantic tag as JSON

Format your response as:
ANSWER: [your 1-2 sentence answer]
TAG: {"intent": "question|command|chitchat|...", "urgency": "low|medium|high", "length_hint": "short|long"}

Keep answers concise and conversational. This is a spoken conversation."""

    # Try with timeout
    try:
        async def _generate():
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript},
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return response.choices[0].message.content
        
        content = await asyncio.wait_for(_generate(), timeout=timeout_seconds)
        
        logger.debug(f"L1 raw response: {content}")
        answer, tag = _parse_l1_response(content)
        
        logger.info(f"L1 Answer: {answer}")
        logger.info(f"L1 Tag: {tag}")
        
        return answer, tag
        
    except asyncio.TimeoutError:
        logger.error(f"L1 timeout after {timeout_seconds}s")
        return _fallback_response(transcript, "timeout")
        
    except Exception as e:
        logger.error(f"Error in speculative brain: {e}")
        return _fallback_response(transcript, str(e))


def _fallback_response(transcript: str, error: str) -> Tuple[str, Dict[str, Any]]:
    """
    Provide fallback response when L1 fails.
    
    Args:
        transcript: User's input
        error: Error description
    
    Returns:
        Tuple of (fallback_answer, tag)
    """
    fallback_answers = [
        "Haan, main samajh gaya. Ek second.",
        "Ji, dekh raha hoon. Thoda intezaar karein.",
        "Main check kar raha hoon.",
    ]
    
    answer = fallback_answers[hash(transcript) % len(fallback_answers)]
    
    return answer, {
        "intent": "unknown",
        "urgency": "medium",
        "length_hint": "short",
        "error": error,
        "fallback": True,
    }


def _parse_l1_response(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse the L1 response into answer and semantic tag.
    
    Args:
        content: Raw response from LLM
    
    Returns:
        Tuple of (answer, tag_dict)
    """
    lines = content.strip().split("\n")
    
    answer = ""
    tag = {}
    
    for line in lines:
        if line.startswith("ANSWER:"):
            answer = line.replace("ANSWER:", "").strip()
        elif line.startswith("TAG:"):
            tag_str = line.replace("TAG:", "").strip()
            try:
                tag = json.loads(tag_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tag JSON: {tag_str}")
                tag = {"intent": "unknown", "urgency": "low", "length_hint": "short"}
    
    # Fallback if parsing failed
    if not answer:
        answer = content.strip()
    if not tag:
        tag = {"intent": "unknown", "urgency": "low", "length_hint": "short"}
    
    return answer, tag


async def generate_speculative_reply_streaming(
    client: AsyncOpenAI,
    model: str,
    transcript: str,
    on_token: callable = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate speculative reply with streaming support.
    
    Args:
        client: OpenAI async client
        model: Model name
        transcript: User's speech transcript
        on_token: Optional callback for each token
    
    Returns:
        Tuple of (answer_text, semantic_tag_dict)
    """
    logger.info(f"🧠 SPECULATIVE BRAIN (L1): Generating reply (streaming) with {model}")
    
    system_prompt = """You are a helpful Hindi voice assistant. 
    
Provide a SHORT answer in Hindi or Hinglish (1-2 sentences maximum).
Keep it conversational and natural. This is spoken conversation."""

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
            temperature=0.3,
            max_tokens=100,
            stream=True,
        )
        
        full_response = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                if on_token:
                    await on_token(token)
        
        logger.info(f"🧠 L1 Answer: {full_response}")
        
        # For streaming, we don't have structured tags
        # Generate a simple tag based on the response
        tag = {
            "intent": "unknown",
            "urgency": "medium",
            "length_hint": "short" if len(full_response) < 50 else "long",
        }
        
        return full_response, tag
        
    except Exception as e:
        logger.error(f"Error in speculative brain (streaming): {e}")
        return "Haan, main samajh gaya.", {
            "intent": "unknown",
            "urgency": "low",
            "length_hint": "short",
            "error": str(e),
        }



