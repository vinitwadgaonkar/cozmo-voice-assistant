"""
Latency oracle and metrics tracking.

Tracks per-provider latency statistics and predicts future performance
to enable smart routing decisions.
"""

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict
import time
from loguru import logger


@dataclass
class LatencyStats:
    """Statistics for a single provider/model."""
    count: int = 0
    avg_first_token_ms: float = 0.0
    avg_total_ms: float = 0.0
    
    def __repr__(self) -> str:
        return f"LatencyStats(n={self.count}, first_token={self.avg_first_token_ms:.0f}ms, total={self.avg_total_ms:.0f}ms)"


class LatencyOracle:
    """
    Tracks latency metrics per provider and predicts future latencies.
    
    Uses exponential moving average (EMA) with alpha=0.3 for smooth predictions.
    """
    
    def __init__(self, ema_alpha: float = 0.3):
        self.stats: Dict[str, LatencyStats] = defaultdict(LatencyStats)
        self.ema_alpha = ema_alpha
    
    def record(self, provider_id: str, first_token_ms: float, total_ms: float) -> None:
        """
        Record latency measurements for a provider.
        
        Args:
            provider_id: Identifier like "openai-l1", "openai-l2", "groq-fast"
            first_token_ms: Time to first token in milliseconds
            total_ms: Total completion time in milliseconds
        """
        stats = self.stats[provider_id]
        
        if stats.count == 0:
            # First measurement, just use it directly
            stats.avg_first_token_ms = first_token_ms
            stats.avg_total_ms = total_ms
        else:
            # Exponential moving average
            alpha = self.ema_alpha
            stats.avg_first_token_ms = (alpha * first_token_ms) + ((1 - alpha) * stats.avg_first_token_ms)
            stats.avg_total_ms = (alpha * total_ms) + ((1 - alpha) * stats.avg_total_ms)
        
        stats.count += 1
        
        logger.debug(
            f"Recorded latency for {provider_id}: "
            f"first_token={first_token_ms:.0f}ms, total={total_ms:.0f}ms | "
            f"Updated stats: {stats}"
        )
    
    def predict_first_token_ms(self, provider_id: str) -> float:
        """
        Predict time to first token for a provider.
        
        Returns:
            Predicted latency in milliseconds, or a default if no data exists.
        """
        stats = self.stats.get(provider_id)
        if not stats or stats.count == 0:
            # No data yet, return a conservative default
            default = 200.0  # 200ms default
            logger.debug(f"No stats for {provider_id}, using default {default}ms")
            return default
        
        return stats.avg_first_token_ms
    
    def predict_total_ms(self, provider_id: str) -> float:
        """
        Predict total completion time for a provider.
        
        Returns:
            Predicted latency in milliseconds, or a default if no data exists.
        """
        stats = self.stats.get(provider_id)
        if not stats or stats.count == 0:
            # No data yet, return a conservative default
            default = 800.0  # 800ms default
            logger.debug(f"No stats for {provider_id}, using default {default}ms")
            return default
        
        return stats.avg_total_ms
    
    def get_stats(self, provider_id: str) -> LatencyStats:
        """Get current statistics for a provider."""
        return self.stats.get(provider_id, LatencyStats())
    
    def get_all_stats(self) -> Dict[str, LatencyStats]:
        """Get all tracked statistics."""
        return dict(self.stats)
    
    def log_summary(self) -> None:
        """Log a summary of all tracked providers."""
        if not self.stats:
            logger.info("Latency Oracle: No data recorded yet")
            return
        
        logger.info("=" * 60)
        logger.info("Latency Oracle Summary")
        logger.info("=" * 60)
        for provider_id, stats in sorted(self.stats.items()):
            logger.info(f"{provider_id:20} | {stats}")
        logger.info("=" * 60)


class LatencyTimer:
    """Helper context manager for timing operations."""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: float = 0.0
        self.first_token_time: float = 0.0
        self.end_time: float = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.first_token_time == 0.0:
            # If first token was never marked, use end time
            self.first_token_time = self.end_time
    
    def mark_first_token(self) -> None:
        """Mark when the first token arrives."""
        if self.first_token_time == 0.0:
            self.first_token_time = time.time()
    
    @property
    def first_token_ms(self) -> float:
        """Time to first token in milliseconds."""
        if self.first_token_time == 0.0:
            return 0.0
        return (self.first_token_time - self.start_time) * 1000.0
    
    @property
    def total_ms(self) -> float:
        """Total time in milliseconds."""
        if self.end_time == 0.0:
            return 0.0
        return (self.end_time - self.start_time) * 1000.0

