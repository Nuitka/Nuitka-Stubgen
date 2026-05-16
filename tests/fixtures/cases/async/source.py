async def fetch(url: str) -> str:
    return ""


async def fetch_many(*urls: str) -> list[str]:
    return []


class AsyncClient:
    async def get(self, url: str) -> str:
        return ""

    async def post(self, url: str, data: dict[str, str]) -> str:
        return ""

    @staticmethod
    async def ping() -> bool:
        return True
