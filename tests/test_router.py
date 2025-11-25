"""
Unit tests for routing logic.
"""

import pytest
from voice_agent.router import (
    should_trigger_reflex,
    should_run_shadow_traffic,
    should_skip_deep_brain,
    should_skip_reflex,
)
from voice_agent.metrics import LatencyOracle


class TestReflexTrigger:
    """Test reflex brain triggering logic."""
    
    def test_trigger_when_high_latency(self):
        """Test reflex triggers when predicted latency is high."""
        oracle = LatencyOracle()
        oracle.record("test-provider", first_token_ms=100, total_ms=200)
        
        should_trigger = should_trigger_reflex(
            oracle,
            target_latency_ms=150,
            primary_provider_id="test-provider"
        )
        
        assert should_trigger is True
    
    def test_no_trigger_when_low_latency(self):
        """Test reflex doesn't trigger when predicted latency is low."""
        oracle = LatencyOracle()
        oracle.record("test-provider", first_token_ms=50, total_ms=100)
        
        should_trigger = should_trigger_reflex(
            oracle,
            target_latency_ms=150,
            primary_provider_id="test-provider"
        )
        
        assert should_trigger is False


class TestShadowTraffic:
    """Test shadow traffic decision logic."""
    
    def test_shadow_probability(self):
        """Test shadow traffic runs at correct probability."""
        runs = sum(1 for _ in range(1000) if should_run_shadow_traffic(0.1))
        
        # Should be around 100 out of 1000 (10%)
        assert 50 < runs < 150  # Some variance


class TestDeepBrainSkipping:
    """Test deep brain skipping logic."""
    
    def test_skip_for_high_urgency(self):
        """Test skip for high-urgency requests."""
        oracle = LatencyOracle()
        tag = {"urgency": "high", "intent": "question"}
        
        should_skip = should_skip_deep_brain(tag, oracle)
        assert should_skip is True
    
    def test_skip_for_trivial_chitchat(self):
        """Test skip for trivial chitchat."""
        oracle = LatencyOracle()
        tag = {"urgency": "low", "intent": "chitchat", "length_hint": "short"}
        
        should_skip = should_skip_deep_brain(tag, oracle)
        assert should_skip is True
    
    def test_no_skip_for_questions(self):
        """Test don't skip for regular questions."""
        oracle = LatencyOracle()
        tag = {"urgency": "medium", "intent": "question"}
        
        should_skip = should_skip_deep_brain(tag, oracle)
        assert should_skip is False


class TestReflexSkipping:
    """Test reflex skipping logic."""
    
    def test_skip_for_greetings(self):
        """Test skip reflex for greetings."""
        tag = {"intent": "greeting"}
        should_skip = should_skip_reflex(tag)
        assert should_skip is True
    
    def test_no_skip_for_questions(self):
        """Test don't skip reflex for questions."""
        tag = {"intent": "question"}
        should_skip = should_skip_reflex(tag)
        assert should_skip is False

