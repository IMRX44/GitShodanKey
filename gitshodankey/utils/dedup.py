class Deduplicator:
    def __init__(self):
        self._seen: set[str] = set()

    def is_duplicate(self, key: str) -> bool:
        return key in self._seen

    def add(self, key: str):
        self._seen.add(key)

    def size(self) -> int:
        return len(self._seen)
