import asyncio

async def async_func(x):
    # type: (int) -> int
    await asyncio.sleep(1)
    return x

class AsyncContainer:
    async def method(self, x: int) -> str:
        async with asyncio.Lock():
            return str(x)

    @classmethod
    async def from_data(cls, data: Any) -> "AsyncContainer":
        return cls()

    @staticmethod
    async def run_static(v: int) -> None:
        async for i in range(v):
            pass

def sync_wrapper():
    async def inner_async():
        return 1
    return inner_async
