"""
CLI entrypoint for the three-brain Hindi LiveKit voice agent.

Runs a production-minded voice agent with:
- Reflex Brain (L0): Immediate backchannels
- Speculative Brain (L1): Fast answers
- Deep Brain (L2): Richer follow-ups
- Latency Oracle: Metrics-based routing
- Shadow Traffic: Background A/B testing
"""

import argparse
import asyncio
from loguru import logger

from .config import load_config
from .pipeline import run_voice_agent


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Three-brain Hindi LiveKit voice agent (POC)"
    )
    parser.add_argument(
        "--room",
        default=None,
        help="LiveKit room name (overrides VOICE_AGENT_DEFAULT_ROOM)",
    )
    parser.add_argument(
        "--identity",
        default=None,
        help="Participant identity (overrides VOICE_AGENT_DEFAULT_IDENTITY)",
    )
    return parser.parse_args()


def main():
    """Main entrypoint for the voice agent."""
    logger.info("Loading voice agent configuration...")
    
    try:
        cfg = load_config()
    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please ensure all required environment variables are set in .env file")
        return 1

    args = parse_args()

    room = args.room or cfg.livekit.default_room
    identity = args.identity or cfg.livekit.default_identity

    logger.info(f"Voice agent will join room '{room}' as '{identity}'")

    try:
        asyncio.run(run_voice_agent(cfg, room, identity))
    except KeyboardInterrupt:
        logger.info("Shutting down voice agent (KeyboardInterrupt).")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

