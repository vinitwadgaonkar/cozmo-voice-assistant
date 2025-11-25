"""
Unit tests for latency oracle and metrics tracking.
"""

import pytest
from voice_agent.metrics import LatencyOracle, LatencyStats, LatencyTimer


class TestLatencyStats:
    """Test LatencyStats dataclass."""
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        stats = LatencyStats(count=90, error_count=10)
        assert stats.error_rate == 0.1  # 10%
    
    def test_error_rate_no_requests(self):
        """Test error rate with no requests."""
        stats = LatencyStats()
        assert stats.error_rate == 0.0
    
    def test_is_available_no_errors(self):
        """Test availability with no errors."""
        stats = LatencyStats()
        assert stats.is_available is True
    
    def test_is_available_recent_error(self):
        """Test availability with recent error."""
        import time
        stats = LatencyStats()
        stats.last_error_time = time.time()  # Now
        assert stats.is_available is False
    
    def test_is_available_old_error(self):
        """Test availability with old error."""
        import time
        stats = LatencyStats()
        stats.last_error_time = time.time() - 120  # 2 minutes ago
        assert stats.is_available is True


class TestLatencyOracle:
    """Test LatencyOracle functionality."""
    
    def test_initial_prediction_returns_default(self):
        """Test prediction with no data returns default."""
        oracle = LatencyOracle()
        predicted = oracle.predict_first_token_ms("new-provider")
        assert predicted == 200.0  # Default
    
    def test_record_and_predict(self):
        """Test recording data and predicting."""
        oracle = LatencyOracle()
        oracle.record("test-provider", first_token_ms=100, total_ms=300)
        
        predicted_first = oracle.predict_first_token_ms("test-provider")
        predicted_total = oracle.predict_total_ms("test-provider")
        
        assert predicted_first == 100.0
        assert predicted_total == 300.0
    
    def test_ema_smoothing(self):
        """Test exponential moving average smoothing."""
        oracle = LatencyOracle(ema_alpha=0.3)
        
        # First measurement
        oracle.record("test", first_token_ms=100, total_ms=300)
        assert oracle.predict_first_token_ms("test") == 100.0
        
        # Second measurement (should be smoothed)
        oracle.record("test", first_token_ms=200, total_ms=400)
        predicted = oracle.predict_first_token_ms("test")
        
        # Expected: 0.3 * 200 + 0.7 * 100 = 130
        assert abs(predicted - 130.0) < 0.1
    
    def test_record_error(self):
        """Test error recording."""
        oracle = LatencyOracle()
        oracle.record_error("test-provider", "timeout")
        
        stats = oracle.get_stats("test-provider")
        assert stats.error_count == 1
        assert stats.timeout_count == 1
    
    def test_record_quality(self):
        """Test quality score recording."""
        oracle = LatencyOracle()
        oracle.record_quality("test-provider", 0.9)
        
        stats = oracle.get_stats("test-provider")
        assert stats.quality_score == 0.9


class TestLatencyTimer:
    """Test LatencyTimer context manager."""
    
    def test_timer_basic(self):
        """Test basic timer functionality."""
        import time
        
        timer = LatencyTimer("test")
        with timer:
            time.sleep(0.01)  # 10ms
        
        assert timer.total_ms >= 10.0
        assert timer.total_ms < 50.0  # Some margin
    
    def test_first_token_marking(self):
        """Test first token time marking."""
        import time
        
        timer = LatencyTimer("test")
        with timer:
            time.sleep(0.01)
            timer.mark_first_token()
            time.sleep(0.01)
        
        assert timer.first_token_ms >= 10.0
        assert timer.first_token_ms < timer.total_ms

