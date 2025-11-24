import asyncio
from typing import AsyncGenerator, TypeVar

T = TypeVar("T")

async def tee_async(aiter: AsyncGenerator[T, None], n: int = 2):
    """
    Splits an async iterator into n async iterators.
    NOTE: This consumes memory if one consumer is slower than others.
    """
    queues = [asyncio.Queue() for _ in range(n)]
    
    async def filler():
        try:
            async for item in aiter:
                for q in queues:
                    await q.put(item)
        finally:
            for q in queues:
                await q.put(None) # Sentinel

    asyncio.create_task(filler())

    async def consumer(q):
        while True:
            item = await q.get()
            if item is None:
                break
            yield item

    return [consumer(q) for q in queues]

