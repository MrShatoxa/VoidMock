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
            name = mock.mock_name.replace(".", "_")
            lines.append(f"mock_calls_total{{mock=\"{name}\"}} {m['calls']}")
            lines.append(f"mock_p90_seconds{{mock=\"{name}\"}} {m['p90']:.6f}")
            lines.append(f"mock_p95_seconds{{mock=\"{name}\"}} {m['p95']:.6f}")
            lines.append(f"mock_p99_seconds{{mock=\"{name}\"}} {m['p99']:.6f}")
            lines.append(f"mock_max_seconds{{mock=\"{name}\"}} {m['max']:.6f}")

            enabled_val = 1 if getattr(mock, "enabled", False) else 0
            lines.append(
                f'mock_config{{mock="{name}", '
                f'delay="{mock.delay}", '
                f'rate_limit="{mock.rate_limit}", '
                f'rate_limit_period="{mock.rate_limit_period}"}} {enabled_val}'
            )

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