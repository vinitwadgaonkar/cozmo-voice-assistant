"""Configuration management for the voice agent."""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()  # load from .env if present


@dataclass
class LiveKitConfig:
    """LiveKit connection and authentication configuration."""
    url: str
    api_key: str
    api_secret: str
    default_room: str
    default_identity: str


@dataclass
class SarvamConfig:
    """Sarvam AI API configuration."""
    api_key: str


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model_l1: str = "gpt-4o-mini"  # Fast model for speculative brain
    model_l2: str = "gpt-4o-mini"  # Model for deep brain (can be same or different)


@dataclass
class AgentBehaviorConfig:
    """Agent behavior and routing configuration."""
    reflex_latency_ms: int = 150  # Trigger reflex if predicted latency exceeds this
    shadow_traffic_probability: float = 0.1  # 10% of turns run shadow traffic
    enable_deep_brain: bool = True  # Whether to run L2 at all


@dataclass
class VoiceAgentConfig:
    """Complete voice agent configuration."""
    livekit: LiveKitConfig
    sarvam: SarvamConfig
    openai: OpenAIConfig
    behavior: AgentBehaviorConfig


def load_config() -> VoiceAgentConfig:
    """
    Load all configuration from environment variables.
    Fail fast with clear errors if anything required is missing.
    
    Returns:
        VoiceAgentConfig: Complete configuration object
        
    Raises:
        RuntimeError: If any required environment variable is missing
    """
    def _get_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value

    livekit = LiveKitConfig(
        url=_get_env("LIVEKIT_URL"),
        api_key=_get_env("LIVEKIT_API_KEY"),
        api_secret=_get_env("LIVEKIT_API_SECRET"),
        default_room=os.getenv("VOICE_AGENT_DEFAULT_ROOM", "cozmo-hindi-test"),
        default_identity=os.getenv("VOICE_AGENT_DEFAULT_IDENTITY", "pipecat-agent-1"),
    )

    sarvam = SarvamConfig(api_key=_get_env("SARVAM_API_KEY"))

    openai = OpenAIConfig(
        api_key=_get_env("OPENAI_API_KEY"),
        model_l1=os.getenv("VOICE_AGENT_OPENAI_MODEL_L1", "gpt-4o-mini"),
        model_l2=os.getenv("VOICE_AGENT_OPENAI_MODEL_L2", "gpt-4o-mini"),
    )

    behavior = AgentBehaviorConfig(
        reflex_latency_ms=int(os.getenv("VOICE_AGENT_REFLEX_LATENCY_MS", "150")),
        shadow_traffic_probability=float(os.getenv("VOICE_AGENT_SHADOW_PROBABILITY", "0.1")),
        enable_deep_brain=os.getenv("VOICE_AGENT_ENABLE_DEEP_BRAIN", "true").lower() == "true",
    )

    return VoiceAgentConfig(livekit=livekit, sarvam=sarvam, openai=openai, behavior=behavior)

