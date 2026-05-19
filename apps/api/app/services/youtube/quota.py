from __future__ import annotations

from datetime import date

from redis.asyncio import Redis

BUDGETS: dict[str, int] = {
    "search.list": 2000,
    "videos.list": 4000,
    "subscriptions.list": 500,
    "playlistItems.list": 1500,
}

COSTS: dict[str, int] = {
    "search.list": 100,
    "videos.list": 1,
    "subscriptions.list": 1,
    "playlistItems.list": 1,
}


class QuotaBudgetExhausted(Exception):
    def __init__(self, op: str, used: int, budget: int) -> None:
        super().__init__(f"Quota budget exhausted for {op}: {used}/{budget}")
        self.op = op
        self.used = used
        self.budget = budget


class QuotaTracker:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, op: str) -> str:
        return f"quota:daily:{date.today().isoformat()}:{op}"

    async def check_and_increment(self, op: str, calls: int = 1) -> int:
        cost = COSTS.get(op, 1) * calls
        budget = BUDGETS.get(op, 0)
        key = self._key(op)

        current = await self._redis.incrby(key, cost)
        if current == cost:
            await self._redis.expire(key, 90000)  # 25h TTL

        if current > budget:
            await self._redis.decrby(key, cost)
            raise QuotaBudgetExhausted(op, current - cost, budget)

        return current

    async def get_usage(self, op: str) -> int:
        val = await self._redis.get(self._key(op))
        return int(val) if val else 0

    async def get_all_usage(self) -> dict[str, dict[str, int]]:
        result = {}
        for op, budget in BUDGETS.items():
            used = await self.get_usage(op)
            result[op] = {"used": used, "budget": budget, "remaining": budget - used}
        return result
