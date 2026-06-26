import asyncio
import aiohttp
from .base import BaseSearcher
from ..utils.rate_limiter import AsyncRateLimiter


class GitLabSearcher(BaseSearcher):
    BASE_URL = "https://gitlab.com/api/v4"

    def __init__(self, token: str, concurrency: int = 10):
        self.token = token
        self.semaphore = asyncio.Semaphore(concurrency)
        self.rate_limiter = AsyncRateLimiter(rate=0.5, burst=3)
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            headers = {"PRIVATE-TOKEN": self.token}
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def search(self, keyword: str, language: str | None = None) -> list[tuple[str, str, str, str]]:
        results = []
        session = await self._get_session()

        for page in range(1, 11):
            await self.rate_limiter.acquire()
            url = f"{self.BASE_URL}/search"
            params = {"scope": "blobs", "search": keyword, "per_page": 100, "page": page}

            attempt = 0
            data = None
            while attempt < 5:
                try:
                    async with self.semaphore:
                        async with session.get(url, params=params) as resp:
                            if resp.status == 429:
                                await self.rate_limiter.wait_with_backoff(attempt)
                                attempt += 1
                                continue
                            if resp.status != 200:
                                return results
                            data = await resp.json()
                except aiohttp.ClientError:
                    await self.rate_limiter.wait_with_backoff(attempt)
                    attempt += 1
                    continue
                break

            if not data:
                break

            for item in data:
                content = item.get("data", "")
                project_id = item.get("project_id", "")
                file_path = item.get("path", "")
                ref = item.get("ref", "main")
                source_url = f"https://gitlab.com/projects/{project_id}/blob/{ref}/{file_path}"
                repo = str(project_id)
                results.append((content, source_url, repo, file_path))

            if len(data) < 100:
                break

        return results

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
