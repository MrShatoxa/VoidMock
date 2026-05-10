import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)

class MetricsPusher:
    def __init__(self, push_gateway_url: str = "http://localhost:8428/api/v1/import/prometheus"):
        self.url = push_gateway_url
        self.mocks = []

    def register(self, mock):
        self.mocks.append(mock)

    async def push(self):
        lines = []
        for mock in self.mocks:
            m = mock.get_metrics_last_minute()
            parts = mock.mock_name.split(".", 1)
            lines.append(f'mock_calls_total{{system="{parts[0]}", mock="{parts[1]}"}} {mock.call_count}')
            lines.append(f'mock_tpm{{system="{parts[0]}", mock="{parts[1]}"}} {m["calls"]}')
            lines.append(f'mock_p90_seconds{{system="{parts[0]}", mock="{parts[1]}"}} {m["p90"]:.6f}')
            lines.append(f'mock_p95_seconds{{system="{parts[0]}", mock="{parts[1]}"}} {m["p95"]:.6f}')
            lines.append(f'mock_p99_seconds{{system="{parts[0]}", mock="{parts[1]}"}} {m["p99"]:.6f}')
            lines.append(f'mock_max_seconds{{system="{parts[0]}", mock="{parts[1]}"}} {m["max"]:.6f}')

            enabled_val = 1 if getattr(mock, "enabled", False) else 0
            lines.append(f'mock_config{{system="{parts[0]}", mock="{parts[1]}", delay="{mock.delay}", rate_limit="{mock.rate_limit}", rate_limit_period="{mock.rate_limit_period}"}} {enabled_val}')

        if not lines:
            return
        payload = "\n".join(lines) + "\n"
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(self.url, data=payload)
                if resp.status not in [200, 204]:
                    logger.warning(f"VM push failed: {resp.status}")
        except Exception as e:
            logger.error(f"Metrics push error: {e}")

    async def periodic_push(self, interval: int = 60):
        while True:
            await asyncio.sleep(interval)
            await self.push()