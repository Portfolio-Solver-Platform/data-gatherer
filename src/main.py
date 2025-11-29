import asyncio
import logging
from typing import Callable
from fastapi import FastAPI

from src.dispatcher import DispatcherMetrics, InitialRequest, SolveRequest, SolveResponse, UpdateOutput, initial_dispatcher, result_collector
from .config import Config
from .routers import health, version, api
import prometheus_fastapi_instrumentator
from contextlib import asynccontextmanager
from src.user_defined_functions import on_startup, on_update

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def psp_ai(on_start: Callable[[InitialRequest], list[SolveRequest]], on_update: Callable[[SolveResponse], UpdateOutput]) -> FastAPI:

    metrics = DispatcherMetrics()
    logger = logging.getLogger(__name__)


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting background tasks...")
        task1 = asyncio.create_task(initial_dispatcher(on_start, metrics))
        task2 = asyncio.create_task(result_collector(on_update, metrics))

        def handle_task_error(task):
            try:
                task.result()
            except Exception as e:
                logger.error(f"Background task failed: {e}", exc_info=True)

        task1.add_done_callback(handle_task_error)
        task2.add_done_callback(handle_task_error)

        yield

        logger.info("Shutting down background tasks...")
        task1.cancel()
        task2.cancel()


    app = FastAPI(
        debug=Config.App.DEBUG,
        root_path=Config.Api.ROOT_PATH,
        title=Config.Api.TITLE,
        description=Config.Api.DESCRIPTION,
        version=Config.App.VERSION,
        lifespan=lifespan,
    )


    app.include_router(health.router, tags=["Health"])
    app.include_router(version.router, tags=["Info"])
    app.include_router(api.router, tags=["Api"], prefix=f"/{Config.Api.VERSION}")

    # Monitoring
    prometheus_fastapi_instrumentator.Instrumentator().instrument(app).expose(app)

    # Exclude /metrics from docs schema
    for route in app.routes:
        if route.path == "/metrics":
            route.include_in_schema = False
            break
        
    return app


app = psp_ai(on_startup, on_update)