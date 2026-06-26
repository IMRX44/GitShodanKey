from abc import ABC, abstractmethod


class BaseSearcher(ABC):
    @abstractmethod
    async def search(self, keyword: str, language: str | None) -> list[tuple[str, str, str, str]]:
        """Returns list of (content, source_url, repo, file_path)"""
        pass

    @abstractmethod
    async def close(self):
        pass
