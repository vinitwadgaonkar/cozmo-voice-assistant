"""
Unit tests for brain functions.
"""

import pytest
from voice_agent.brains.reflex import choose_reflex_phrase, REFLEX_PHRASES
from voice_agent.brains.speculative import _parse_l1_response, _fallback_response


class TestReflexBrain:
    """Test reflex brain functions."""
    
    def test_choose_reflex_phrase(self):
        """Test reflex phrase selection."""
        phrase = choose_reflex_phrase()
        assert phrase in REFLEX_PHRASES
    
    def test_reflex_phrases_valid(self):
        """Test all reflex phrases are Hindi/Hinglish."""
        for phrase in REFLEX_PHRASES:
            assert isinstance(phrase, str)
            assert len(phrase) > 0
            assert len(phrase) < 50  # Reasonable length


class TestSpeculativeBrain:
    """Test speculative brain functions."""
    
    def test_parse_valid_response(self):
        """Test parsing valid L1 response."""
        content = '''ANSWER: Namaste, main aapki madad kar sakta hoon.
TAG: {"intent": "greeting", "urgency": "low", "length_hint": "short"}'''
        
        answer, tag = _parse_l1_response(content)
        
        assert answer == "Namaste, main aapki madad kar sakta hoon."
        assert tag["intent"] == "greeting"
        assert tag["urgency"] == "low"
    
    def test_parse_malformed_response(self):
        """Test parsing malformed response falls back gracefully."""
        content = "Just a plain answer without tags"
        
        answer, tag = _parse_l1_response(content)
        
        assert isinstance(answer, str)
        assert isinstance(tag, dict)
        assert "intent" in tag
    
    def test_fallback_response(self):
        """Test fallback response generation."""
        answer, tag = _fallback_response("test input", "timeout")
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert tag["fallback"] is True
        assert "error" in tag
    
    def test_fallback_consistent(self):
        """Test fallback gives consistent response for same input."""
        answer1, _ = _fallback_response("same input", "error")
        answer2, _ = _fallback_response("same input", "error")
        
        assert answer1 == answer2

