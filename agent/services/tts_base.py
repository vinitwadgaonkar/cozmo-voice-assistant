import abc
from typing import AsyncGenerator

class TTSProvider(abc.ABC):
    @abc.abstractmethod
    async def stream_audio(self, text_stream: AsyncGenerator[str, None], turn_id: str) -> AsyncGenerator[bytes, None]:
        """
        Takes a stream of text tokens and yields audio chunks (PCM 16k).
        """
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

