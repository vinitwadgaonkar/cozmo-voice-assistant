from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    # Keys
    OPENAI_API_KEY: str
    SARVAM_API_KEY: str
    CARTESIA_API_KEY: str

    # Modes
    TTS_MODE: Literal["race", "cartesia", "sarvam"] = "race"
    LATENCY_MODE: Literal["aggro", "safe"] = "aggro"

    # Voices
    CARTESIA_VOICE_ID: str = "sonic-hindi"
    SARVAM_VOICE_ID: str = "bulbul-hindi"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

