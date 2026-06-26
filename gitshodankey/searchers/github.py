import asyncio
import base64
import aiohttp
from .base import BaseSearcher
from ..utils.rate_limiter import AsyncRateLimiter


class GitHubSearcher(BaseSearcher):
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str, concurrency: int = 10):
        self.token = token
        self.semaphore = asyncio.Semaphore(concurrency)
        self.rate_limiter = AsyncRateLimiter(rate=1.0, burst=5)
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def search(self, keyword: str, language: str | None = None) -> list[tuple[str, str, str, str]]:
        results = []
        session = await self._get_session()
        query = keyword
        if language:
            query = f"{keyword} language:{language}"

        for page in range(1, 11):
            await self.rate_limiter.acquire()
            url = f"{self.BASE_URL}/search/code"
            params = {"q": query, "per_page": 100, "page": page}

            data = None
            attempt = 0
            while attempt < 5:
                try:
                    async with self.semaphore:
                        async with session.get(url, params=params) as resp:
                            if resp.status == 403:
                                await self.rate_limiter.wait_with_backoff(attempt)
                                attempt += 1
                                continue
                            if resp.status == 422:
                                # Query not supported, stop pagination
                                return results
                            if resp.status != 200:
                                return results
                            data = await resp.json()
                except aiohttp.ClientError:
                    await self.rate_limiter.wait_with_backoff(attempt)
                    attempt += 1
                    continue
                break

            if data is None:
                break
            items = data.get("items", [])
            if not items:
                break

            content_tasks = [
                self._get_file_content(session, item["url"])
                for item in items
            ]
            contents = await asyncio.gather(*content_tasks, return_exceptions=True)

            for item, content in zip(items, contents):
                if isinstance(content, Exception) or content is None:
                    continue
                results.append((
                    content,
                    item.get("html_url", ""),
                    item.get("repository", {}).get("full_name", ""),
                    item.get("path", ""),
                ))

            if len(items) < 100:
                break

        return results

    async def _get_file_content(self, session: aiohttp.ClientSession, url: str) -> str | None:
        await self.rate_limiter.acquire()
        attempt = 0
        while attempt < 3:
            try:
                async with self.semaphore:
                    async with session.get(url) as resp:
                        if resp.status == 403:
                            await self.rate_limiter.wait_with_backoff(attempt)
                            attempt += 1
                            continue
                        if resp.status != 200:
                            return None
                        data = await resp.json()
                        encoded = data.get("content", "")
                        return base64.b64decode(encoded).decode("utf-8", errors="replace")
            except (aiohttp.ClientError, Exception):
                attempt += 1
                continue
        return None

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
