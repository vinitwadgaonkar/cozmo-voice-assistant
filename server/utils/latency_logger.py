"""Latency logger processor for tracking user speech, agent responses, and latency."""

import time
from typing import Optional
from loguru import logger

from pipecat.frames.frames import (
    Frame,
    StartFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    LLMMessagesFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    TTSAudioRawFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class LatencyLogger(FrameProcessor):
    """Logs user speech, agent responses, and latency metrics."""
    
    def __init__(self):
        super().__init__()
        self._user_speech_start: Optional[float] = None
        self._user_speech_end: Optional[float] = None
        self._stt_start: Optional[float] = None
        self._stt_end: Optional[float] = None
        self._llm_start: Optional[float] = None
        self._llm_end: Optional[float] = None
        self._tts_start: Optional[float] = None
        self._tts_end: Optional[float] = None
        self._first_audio_time: Optional[float] = None
        self._last_transcript: Optional[str] = None
        self._last_llm_response: Optional[str] = None
        
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        current_time = time.time()
        
        if isinstance(frame, StartFrame):
            await super().process_frame(frame, direction)
            await self.push_frame(frame, direction)
            return

        # Log all frame types for debugging (can remove later)
        frame_type = type(frame).__name__
        if any(keyword in frame_type for keyword in ['Transcription', 'LLM', 'TTS', 'Speaking', 'User', 'Bot']):
            logger.debug(f"📦 Frame: {frame_type}")
        
        # User speech events
        if isinstance(frame, UserStartedSpeakingFrame):
            self._user_speech_start = current_time
            logger.info("🎤 USER STARTED SPEAKING")
            
        elif isinstance(frame, UserStoppedSpeakingFrame):
            self._user_speech_end = current_time
            if self._user_speech_start:
                duration = (self._user_speech_end - self._user_speech_start) * 1000
                logger.info(f"🎤 USER STOPPED SPEAKING (duration: {duration:.0f}ms)")
        
        
        # STT events
        elif isinstance(frame, TranscriptionFrame):
            self._stt_end = current_time
            transcript = frame.text
            self._last_transcript = transcript
            
            if self._user_speech_end:
                stt_latency = (self._stt_end - self._user_speech_end) * 1000
                logger.info(f"📝 STT TRANSCRIPT: \"{transcript}\" (latency: {stt_latency:.0f}ms)")
            else:
                logger.info(f"📝 STT TRANSCRIPT: \"{transcript}\"")
                
        elif isinstance(frame, InterimTranscriptionFrame):
            transcript = frame.text
            self._stt_end = current_time  # Track interim as STT completion for latency
            if self._user_speech_end:
                interim_latency = (self._stt_end - self._user_speech_end) * 1000
                logger.info(f"📝 STT INTERIM: \"{transcript}\" (latency: {interim_latency:.0f}ms) - Should trigger LLM early!")
            else:
                logger.info(f"📝 STT INTERIM: \"{transcript}\" - Should trigger LLM early!")
        
        # LLM events
        elif isinstance(frame, LLMFullResponseStartFrame):
            self._llm_start = current_time
            if self._stt_end:
                llm_ttfb = (self._llm_start - self._stt_end) * 1000
                logger.info(f"🤖 LLM STARTED GENERATING (TTFB: {llm_ttfb:.0f}ms)")
            else:
                logger.info("🤖 LLM STARTED GENERATING")
                
        elif isinstance(frame, LLMFullResponseEndFrame):
            self._llm_end = current_time
            if self._llm_start:
                llm_duration = (self._llm_end - self._llm_start) * 1000
                logger.info(f"🤖 LLM FINISHED GENERATING (duration: {llm_duration:.0f}ms)")
        
        elif isinstance(frame, LLMMessagesFrame):
            # Extract the last assistant message
            messages = frame.messages
            if messages and messages[-1].get("role") == "assistant":
                response = messages[-1].get("content", "")
                if response and response != self._last_llm_response:
                    self._last_llm_response = response
                    # Track when first LLM token arrives (for streaming)
                    if not self._llm_start:
                        self._llm_start = current_time
                        if self._stt_end:
                            llm_ttfb = (self._llm_start - self._stt_end) * 1000
                            logger.info(f"💬 LLM FIRST TOKEN (TTFB: {llm_ttfb:.0f}ms): \"{response[:50]}...\"")
                    logger.info(f"💬 LLM RESPONSE: \"{response}\"")
        
        # TTS events
        elif isinstance(frame, TTSStartedFrame):
            self._tts_start = current_time
            if self._llm_end:
                tts_ttfb = (self._tts_start - self._llm_end) * 1000
                logger.info(f"🔊 TTS STARTED (TTFB: {tts_ttfb:.0f}ms)")
            elif self._llm_start:
                # LLM streaming - use first token time
                tts_ttfb = (self._tts_start - self._llm_start) * 1000
                logger.info(f"🔊 TTS STARTED (after LLM first token: {tts_ttfb:.0f}ms)")
            else:
                logger.info("🔊 TTS STARTED")
            
            # Calculate total latency as soon as TTS starts
            if self._user_speech_end:
                total_latency = (self._tts_start - self._user_speech_end) * 1000
                logger.info(f"⏱️  TOTAL LATENCY (user stop → first audio): {total_latency:.0f}ms")
                
                # Component breakdown
                if self._stt_end and self._llm_end:
                    stt_time = (self._stt_end - self._user_speech_end) * 1000
                    llm_time = (self._llm_end - self._stt_end) * 1000
                    tts_time = (self._tts_start - self._llm_end) * 1000
                    logger.info(f"📊 BREAKDOWN: STT={stt_time:.0f}ms | LLM={llm_time:.0f}ms | TTS={tts_time:.0f}ms")
                elif self._stt_end and self._llm_start:
                    # LLM streaming case
                    stt_time = (self._stt_end - self._user_speech_end) * 1000
                    llm_to_tts = (self._tts_start - self._llm_start) * 1000
                    logger.info(f"📊 BREAKDOWN: STT={stt_time:.0f}ms | LLM→TTS={llm_to_tts:.0f}ms (streaming)")
                
        # Track first audio frame for more accurate latency
        elif isinstance(frame, TTSAudioRawFrame):
            if not self._first_audio_time:
                self._first_audio_time = current_time
                if self._user_speech_end:
                    audio_latency = (self._first_audio_time - self._user_speech_end) * 1000
                    logger.info(f"🎵 FIRST AUDIO FRAME (latency: {audio_latency:.0f}ms from user stop)")
                    
                    # Detailed breakdown calculation
                    breakdown_parts = []
                    if self._stt_end:
                        stt_latency = (self._stt_end - self._user_speech_end) * 1000
                        breakdown_parts.append(f"STT={stt_latency:.0f}ms")
                    if self._llm_start:
                        llm_start_latency = (self._llm_start - (self._stt_end or self._user_speech_end)) * 1000
                        breakdown_parts.append(f"LLM_start={llm_start_latency:.0f}ms")
                    if self._tts_start:
                        tts_start_latency = (self._tts_start - (self._llm_start or self._stt_end or self._user_speech_end)) * 1000
                        breakdown_parts.append(f"TTS_start={tts_start_latency:.0f}ms")
                    audio_start_latency = (self._first_audio_time - (self._tts_start or self._llm_start or self._stt_end or self._user_speech_end)) * 1000
                    breakdown_parts.append(f"Audio_stream={audio_start_latency:.0f}ms")
                    
                    if breakdown_parts:
                        logger.info(f"📊 DETAILED BREAKDOWN: {' → '.join(breakdown_parts)}")
                    
                    # Target comparison
                    if audio_latency < 200:
                        logger.info(f"✅ TARGET ACHIEVED: {audio_latency:.0f}ms < 200ms")
                    else:
                        logger.warning(f"⚠️  TARGET MISSED: {audio_latency:.0f}ms > 200ms")
                
        elif isinstance(frame, TTSStoppedFrame):
            self._tts_end = current_time
            if self._tts_start:
                tts_duration = (self._tts_end - self._tts_start) * 1000
                logger.info(f"🔊 TTS FINISHED (duration: {tts_duration:.0f}ms)")
        
        elif isinstance(frame, BotStartedSpeakingFrame):
            logger.info("🔊 BOT STARTED SPEAKING")
            
        elif isinstance(frame, BotStoppedSpeakingFrame):
            logger.info("🔊 BOT STOPPED SPEAKING")
            # Reset for next turn
            self._reset()
        
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        
    def _reset(self):
        """Reset all timestamps for next turn."""
        self._user_speech_start = None
        self._user_speech_end = None
        self._stt_start = None
        self._stt_end = None
        self._llm_start = None
        self._llm_end = None
        self._tts_start = None
        self._tts_end = None
        self._first_audio_time = None
        self._last_transcript = None
        self._last_llm_response = None

