import asyncio
import time
from abc import ABC, abstractmethod
from collections import deque
from fastapi import Request, Response
from fastapi.responses import JSONResponse

class Mock(ABC):

    method = "GET"
    path = None
    delay = 0.0
    enabled: bool = True

    def __init__(self, mock_name: str = None):
        self.mock_name = mock_name
        self.call_count = 0
        self._response_times: deque = deque()

    @abstractmethod
    async def get_response(self, request: Request):
        """Логика заглушки: возвращает dict, str, Response и т.д."""
        pass

    async def handle(self, request: Request) -> Response:
        if not self.enabled:
            return JSONResponse({"error": "Mock disabled"}, status_code=503)

        start = time.monotonic()
        self.call_count += 1

        # Задержка
        delay_sec = float(self.delay)
        if delay_sec > 0:
            await asyncio.sleep(delay_sec)

        response_data = await self.get_response(request)
        elapsed = time.monotonic() - start
        self._response_times.append((time.time(), elapsed))

        # Преобразование в Response
        if isinstance(response_data, Response):
            return response_data
        elif isinstance(response_data, dict):
            return JSONResponse(response_data)
        elif isinstance(response_data, str):
            return Response(content=response_data, media_type="text/plain")

    def get_metrics_last_minute(self):
        """Статистика за последние 60 секунд."""
        now = time.time()
        recent = [elapsed for ts, elapsed in self._response_times if ts >= now - 60]
        if not recent:
            return {"calls": 0, "p90": 0, "p95": 0, "p99": 0, "max": 0}
        recent.sort()
        n = len(recent)
        def p(percent):
            idx = int(n * percent / 100)
            return recent[min(idx, n-1)]
        return {
            "calls": n,
            "p90": p(90),
            "p95": p(95),
            "p99": p(99),
            "max": recent[-1],
        }