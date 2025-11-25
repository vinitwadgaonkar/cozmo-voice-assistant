# Voice Agent Examples

This document shows common customization patterns for the Hindi LiveKit Voice Agent.

## Example 1: Custom System Prompt

Create a specialized agent with a custom personality:

```python
# In voice_agent/pipeline.py, modify run_voice_agent()

context = OpenAILLMContext(
    messages=[
        {
            "role": "system",
            "content": """You are Amit, a friendly customer service agent for TechCorp.
            You speak Hindi and English fluently. You help customers with:
            - Product information
            - Order tracking  
            - Technical support
            
            Always be polite, concise, and helpful.
            If you don't know something, offer to connect them with a human agent."""
        }
    ]
)
```

## Example 2: Different TTS Voice

Use a female voice instead of male:

```python
# In voice_agent/pipeline.py, modify build_services()

def build_services(cfg: VoiceAgentConfig):
    stt = SarvamSTTService(
        api_key=cfg.sarvam.api_key,
        language="hi-IN",
    )

    # Change from "arvind" (male) to "meera" (female)
    tts = SarvamTTSService(
        api_key=cfg.sarvam.api_key,
        voice_id="meera",  # ← Changed
        sample_rate=16000,
    )

    llm = OpenAILLMService(
        api_key=cfg.openai.api_key,
        model=cfg.openai.model,
    )

    return stt, llm, tts
```

## Example 3: Add Function Calling

Enable the agent to call your APIs:

```python
# In voice_agent/pipeline.py

from pipecat.processors.function_processor import FunctionProcessor

def get_weather(city: str) -> str:
    """Get weather for a city."""
    # Your API call here
    return f"The weather in {city} is sunny and 25°C"

def build_pipeline_with_functions(cfg: VoiceAgentConfig, room_name: str, identity: str):
    stt, llm, tts = build_services(cfg)
    transport = create_livekit_transport(cfg, room_name, identity)
    
    # Add function processor
    function_processor = FunctionProcessor(
        functions=[get_weather],
        llm=llm,
    )
    
    context = OpenAILLMContext(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Use the get_weather function when users ask about weather."
            }
        ],
        functions=[{
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        }]
    )
    
    context_aggregator = llm.create_context_aggregator(context)
    
    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        function_processor,  # ← Added
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])
    
    task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))
    return task
```

## Example 4: Multiple Language Support

Switch between Hindi and English dynamically:

```python
# Create a custom processor to detect language

from pipecat.frames import TextFrame
from pipecat.processors.frame_processor import FrameProcessor

class LanguageDetectorProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.current_language = "hi-IN"
    
    async def process_frame(self, frame):
        if isinstance(frame, TextFrame):
            text = frame.text
            # Simple heuristic: if text has mostly English words, switch to English
            english_words = sum(1 for word in text.split() if word.isascii())
            total_words = len(text.split())
            
            if total_words > 0:
                english_ratio = english_words / total_words
                self.current_language = "en-IN" if english_ratio > 0.7 else "hi-IN"
                
                # Update STT/TTS language (you'd need to pass references)
                logger.info(f"Detected language: {self.current_language}")
        
        await self.push_frame(frame)

# Add to pipeline between STT and LLM
```

## Example 5: Session Persistence

Save conversation history to a database:

```python
import json
from datetime import datetime

class ConversationLogger:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = []
    
    def log_message(self, role: str, content: str):
        self.messages.append({
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "content": content
        })
    
    def save(self):
        filename = f"conversations/{self.session_id}.json"
        with open(filename, "w") as f:
            json.dump(self.messages, f, indent=2)

# Use in pipeline
conversation_logger = ConversationLogger(session_id="user-123")

# In your event handlers:
@transport.event_handler("on_transcript")
async def on_transcript(transport, participant, transcript):
    conversation_logger.log_message("user", transcript)

@transport.event_handler("on_agent_response")  
async def on_agent_response(transport, text):
    conversation_logger.log_message("assistant", text)
    conversation_logger.save()
```

## Example 6: Multi-Agent Setup

Run multiple specialized agents in different rooms:

```bash
# Terminal 1: Customer support agent
python -m voice_agent.main \
  --room support \
  --identity support-agent

# Terminal 2: Sales agent  
python -m voice_agent.main \
  --room sales \
  --identity sales-agent

# Terminal 3: Technical agent
python -m voice_agent.main \
  --room tech \
  --identity tech-agent
```

Each agent can have different system prompts, voices, and behaviors.

## Example 7: Add Metrics & Monitoring

Track latency and usage:

```python
from datetime import datetime
import time

class MetricsTracker:
    def __init__(self):
        self.stt_latencies = []
        self.llm_latencies = []
        self.tts_latencies = []
    
    def track_stt(self, start_time: float):
        latency = time.time() - start_time
        self.stt_latencies.append(latency)
        logger.info(f"STT latency: {latency*1000:.0f}ms")
    
    def get_average_latencies(self):
        return {
            "stt_avg": sum(self.stt_latencies) / len(self.stt_latencies) if self.stt_latencies else 0,
            "llm_avg": sum(self.llm_latencies) / len(self.llm_latencies) if self.llm_latencies else 0,
            "tts_avg": sum(self.tts_latencies) / len(self.tts_latencies) if self.tts_latencies else 0,
        }

# Add to your pipeline and track in event handlers
```

## Example 8: Custom VAD Configuration

Fine-tune Voice Activity Detection:

```python
# In create_livekit_transport()

from pipecat.vad.silero import SileroVADAnalyzer

vad_analyzer = SileroVADAnalyzer(
    min_volume=0.6,           # Minimum volume threshold
    min_silence_duration=0.3, # Seconds of silence to detect speech end
    min_speech_duration=0.1,  # Minimum speech duration to trigger
)

params = LiveKitParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    audio_in_sample_rate=16000,
    audio_out_sample_rate=16000,
    vad_enabled=True,
    vad_analyzer=vad_analyzer,  # ← Custom VAD
    vad_audio_passthrough=True,
)
```

## Example 9: Handle Specific Intents

Process specific commands:

```python
from pipecat.processors.frame_processor import FrameProcessor
from pipecat.frames import TextFrame

class IntentProcessor(FrameProcessor):
    async def process_frame(self, frame):
        if isinstance(frame, TextFrame):
            text = frame.text.lower()
            
            # Check for specific intents
            if "help" in text or "madad" in text:
                # Inject custom response
                response = TextFrame("I'm here to help! You can ask me about products, orders, or support.")
                await self.push_frame(response)
                return
            
            elif "bye" in text or "alvida" in text:
                response = TextFrame("Goodbye! Have a great day!")
                await self.push_frame(response)
                # Signal end of conversation
                return
        
        # Pass through to next processor
        await self.push_frame(frame)

# Add to pipeline after STT
```

## Example 10: Environment-Specific Configuration

```python
# voice_agent/config.py

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment-specific .env file
env = os.getenv("ENV", "development")
load_dotenv(f".env.{env}")  # .env.production, .env.staging, etc.

@dataclass
class VoiceAgentConfig:
    # ... existing fields ...
    
    # Add environment-specific settings
    debug_mode: bool = False
    log_level: str = "INFO"
    max_session_duration: int = 3600  # seconds
    
    @classmethod
    def load(cls):
        cfg = load_config()  # Your existing function
        
        # Override for development
        if env == "development":
            cfg.debug_mode = True
            cfg.log_level = "DEBUG"
        
        return cfg
```

## Example 11: Rate Limiting

Prevent abuse with rate limiting:

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        now = datetime.utcnow()
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window
        ]
        
        # Check if under limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Record new request
        self.requests[user_id].append(now)
        return True

# Use in event handlers
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

@transport.event_handler("on_transcript")
async def on_transcript(transport, participant, transcript):
    if not rate_limiter.is_allowed(participant.identity):
        logger.warning(f"Rate limit exceeded for {participant.identity}")
        # Optionally send a warning message
        return
    
    # Process normally
    # ...
```

## Example 12: A/B Testing Different Models

Test multiple OpenAI models:

```python
import random

def create_llm_service(cfg: VoiceAgentConfig, user_id: str):
    # A/B test: 50% get gpt-4o-mini, 50% get gpt-3.5-turbo
    model = random.choice(["gpt-4o-mini", "gpt-3.5-turbo"])
    
    logger.info(f"User {user_id} assigned to model: {model}")
    
    return OpenAILLMService(
        api_key=cfg.openai.api_key,
        model=model,
    )

# Track metrics per model to compare performance
```

---

## Running Examples

To use these examples:

1. **Copy the relevant code** into your `voice_agent/pipeline.py`
2. **Install any additional dependencies** if needed
3. **Test with**: `python -m voice_agent.main`
4. **Monitor logs** to see the changes in action

## Need More Examples?

Check out:
- [Pipecat Examples](https://github.com/pipecat-ai/pipecat/tree/main/examples)
- [LiveKit Agent Examples](https://github.com/livekit/agents/tree/main/examples)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

Happy building! 🚀



