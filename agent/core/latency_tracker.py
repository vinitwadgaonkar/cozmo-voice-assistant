import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from loguru import logger
from pathlib import Path

@dataclass
class TurnMetrics:
    turn_id: str
    t_user_eos: float = 0.0
    t_stt_partial: float = 0.0
    t_stt_final: float = 0.0
    t_llm_first_token: float = 0.0
    t_llm_last_token: float = 0.0
    t_tts_first_audio: float = 0.0
    t_playback_start: float = 0.0
    provider_winner: Optional[str] = None

    @property
    def turn_latency_ms(self) -> float:
        if self.t_playback_start > 0 and self.t_user_eos > 0:
            return (self.t_playback_start - self.t_user_eos) * 1000
        return 0.0

    def to_csv_row(self) -> str:
        return f"{self.turn_id},{self.t_user_eos},{self.t_stt_partial},{self.t_stt_final},{self.t_llm_first_token},{self.t_llm_last_token},{self.t_tts_first_audio},{self.t_playback_start},{self.turn_latency_ms},{self.provider_winner}"

class LatencyTracker:
    def __init__(self, log_file: str = "latency_log.csv"):
        self.metrics: Dict[str, TurnMetrics] = {}
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            with open(self.log_file, "w") as f:
                f.write("turn_id,t_user_eos,t_stt_partial,t_stt_final,t_llm_first_token,t_llm_last_token,t_tts_first_audio,t_playback_start,turn_latency_ms,provider_winner\n")

    def start_turn(self, turn_id: str, t_user_eos: float):
        self.metrics[turn_id] = TurnMetrics(turn_id=turn_id, t_user_eos=t_user_eos)
        logger.debug(f"Started tracking turn {turn_id} at {t_user_eos}")

    def mark(self, turn_id: str, event: str, timestamp: Optional[float] = None):
        if turn_id not in self.metrics:
            return
        
        t = timestamp or time.time()
        setattr(self.metrics[turn_id], event, t)
        logger.debug(f"Marked {event} for {turn_id} at {t}")

    def set_winner(self, turn_id: str, winner: str):
        if turn_id in self.metrics:
            self.metrics[turn_id].provider_winner = winner

    def end_turn(self, turn_id: str):
        if turn_id not in self.metrics:
            return
        
        metric = self.metrics[turn_id]
        
        # Log to file
        with open(self.log_file, "a") as f:
            f.write(metric.to_csv_row() + "\n")
            
        # Print ASCII Bar
        self._print_ascii_bar(metric)
        
        # Cleanup to save memory, or keep if we want stats API
        # del self.metrics[turn_id] 

    def _print_ascii_bar(self, m: TurnMetrics):
        if m.turn_latency_ms == 0:
            return
            
        # Simple normalization: 1 char = 10ms
        scale = 10
        bar_len = int(m.turn_latency_ms / scale)
        bar = "█" * bar_len
        print(f"\n[Turn {m.turn_id}] Latency: {m.turn_latency_ms:.1f}ms | Winner: {m.provider_winner}")
        print(f"Timeline: {bar}\n")

# Global instance
tracker = LatencyTracker()

