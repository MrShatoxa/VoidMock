import asyncio
import time
import random
from abc import ABC, abstractmethod
from pathlib import Path
import json
import inspect
from collections import deque
from fastapi import Request, Response
from fastapi.responses import JSONResponse

class Mock(ABC):

    method = "GET"
    path = None
    delay = 0
    enabled: bool = True
    rate_limit = 0 # например 10 - максимум 10 вызовов за период
    rate_limit_period = 1 # период в секундах (по умолчанию 1 секунда)

    def __init__(self):
        self.call_count = 0
        self._response_times: deque = deque()
        self._call_timestamps: deque = deque()

    @abstractmethod
    async def get_response(self, request: Request):
        """Логика заглушки: возвращает dict, str, Response и т.д."""
        pass

    async def handle(self, request: Request) -> Response:

        if self.rate_limit:
            now = time.monotonic()
            while self._call_timestamps and self._call_timestamps[0] < now - self.rate_limit_period:
                self._call_timestamps.popleft() # Удаляем записи старше периода
            if len(self._call_timestamps) >= self.rate_limit:
                return JSONResponse(
                    {"error": "Rate limit exceeded", "limit": self.rate_limit, "period": self.rate_limit_period},
                    status_code=429
                )
            self._call_timestamps.append(now)

        if not self.enabled:
            return JSONResponse({"error": "Mock disabled"}, status_code=503)

        self.call_count += 1

        # Задержка
        if isinstance(self.delay, (tuple, list)) and len(self.delay) == 2:
            target_total = random.uniform(self.delay[0], self.delay[1])
        else:
            target_total = float(self.delay)

        start = time.monotonic()

        response_data = await self.get_response(request)
        elapsed_logic = time.monotonic() - start
        remaining = target_total - elapsed_logic
        if remaining > 0:
            await asyncio.sleep(remaining)

        elapsed_total = time.monotonic() - start
        self._response_times.append((time.time(), elapsed_total))

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

    def load_data_file(self, filename: str) -> dict | list | str:
        """Загружает данные из файла в папке data/ относительно текущего мока."""
        data_file = Path(self._mock_base_dir) / "data" / filename
        with open(data_file, "r", encoding="utf-8") as f:
            if filename.endswith(".json"):
                return json.load(f)
            return f.read()

    def get_data_files_list(self, extension: str = None):
        """Возвращает список имён файлов в папке data.
        Если указано расширение (например, '.json'), фильтрует по нему."""
        data_dir = Path(self._mock_base_dir) / "data"
        if not data_dir.exists():
            return []
        if extension:
            ext = extension if extension.startswith('.') else f'.{extension}'
            return [f.name for f in data_dir.iterdir() if f.is_file() and f.suffix == ext]
        return [f.name for f in data_dir.iterdir() if f.is_file()]