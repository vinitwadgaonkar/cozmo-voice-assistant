from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    LIVEKIT_TOKEN: str = ""

    SARVAM_API_KEY: str
    OPENAI_API_KEY: str
    GROQ_API_KEY: str = ""
    DEEPGRAM_API_KEY: str = ""
    CARTESIA_API_KEY: str = ""

    SARVAM_STT_URL: str = "wss://api.sarvam.ai/v1/stt/streaming"
    SARVAM_TTS_URL: str = "wss://api.sarvam.ai/v1/tts/streaming"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
