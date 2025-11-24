import asyncio
from typing import Literal, Optional
from loguru import logger
from agent.config.settings import settings
from agent.core.latency_tracker import tracker

class TurnManager:
    def __init__(self):
        self.mode = settings.LATENCY_MODE
        self.current_turn_id: Optional[str] = None
        self.is_speaking = False
        self.interrupt_event = asyncio.Event()

    def start_turn(self, turn_id: str):
        logger.info(f"Starting turn {turn_id} in {self.mode} mode")
        self.current_turn_id = turn_id
        self.interrupt_event.clear()
        self.is_speaking = False

    def should_interrupt(self) -> bool:
        """Determine if we should interrupt based on mode and state"""
        if self.mode == "aggro":
            return True # Always interrupt in aggro
        return False # Safe mode doesn't interrupt easily (simplified)

    def handle_interruption(self):
        """Call this when user speaks while bot is speaking"""
        if self.is_speaking and self.should_interrupt():
            logger.info("Interrupting current playback")
            self.interrupt_event.set()
            self.is_speaking = False
            return True
        return False

    def can_process_partial(self) -> bool:
        return self.mode == "aggro"

    async def wait_for_safe_turn(self):
        if self.mode == "safe":
            # In safe mode, we might wait for silence or finalization
            pass

turn_manager = TurnManager()

