import asyncio
import time


class AsyncRateLimiter:
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_update = now

            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._tokens = 0.0
            else:
                self._tokens -= 1.0

    async def wait_with_backoff(self, attempt: int):
        delay = min(2 ** attempt, 60)
        await asyncio.sleep(delay)
