import importlib.util
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from common.metric_collector import MetricsPusher

metrics_pusher = MetricsPusher()

# 2. Определяем lifespan-функцию
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Этот код выполняется ПРИ ЗАПУСКЕ приложения
    print("[Lifespan] Startup: Creating background task for metrics...")
    # Создаем фоновую задачу. Важно сохранить ссылку на задачу, если нужно управлять ей.
    task = asyncio.create_task(metrics_pusher.periodic_push(60))

    yield  # <-- Здесь происходит передача управления приложению

    # Этот код выполняется ПРИ ОСТАНОВКЕ приложения
    print("[Lifespan] Shutdown: Cancelling background metrics task...")
    task.cancel()  # Отменяем фоновую задачу при выключении
    try:
        await task
    except asyncio.CancelledError:
        print("[Lifespan] Background metrics task cancelled successfully.")


def create_app(mocks_dir) -> FastAPI:
    """
    Сканирует папку mocks_dir. Любая подпапка, содержащая файл <имя_папки>.py,
    который экспортирует переменную 'mock' с атрибутом enabled=True,
    загружается.
    """
    app = FastAPI(title=f"Mock Server - {Path(mocks_dir).name}", lifespan=lifespan)
    mocks_path = Path(mocks_dir)

    for item in mocks_path.iterdir():
        if not item.is_dir():
            continue

        spec = importlib.util.spec_from_file_location(item.name, f"{item}/{item.name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        mock = module.mock
        if not getattr(mock, "enabled", False):
            print(f"Мок {getattr(mock, 'mock_name', item.name)} выключен (enabled=False)")
            continue

        # Если у мока есть метод и путь – регистрируем как HTTP
        if hasattr(mock, "method") and hasattr(mock, "path"):
            if mock.mock_name is None:
                mock.mock_name = f"{mocks_path.name}.{mock.__class__.__name__}"

            app.add_api_route(mock.path, mock.handle, methods=[mock.method], name=mock.mock_name)
            metrics_pusher.register(mock)
            print(f"HTTP {mock.method} {mock.path} -> {mock.mock_name} (enabled)")
        else:
            # Не-HTTP мок (Kafka, gRPC и т.д.) – просто загружаем, но не регистрируем в FastAPI
            print(f"Не-HTTP мок загружен: {getattr(mock, 'mock_name', item.name)} (enabled)")
    return app
