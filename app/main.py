from __future__ import annotations

import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest

from app.api import routes
from app.config import get_settings
from app.metrics import request_latency
from app.utils.logging import configure_logging

configure_logging()
logger = logging.getLogger("app")


def create_app() -> FastAPI:
    app = FastAPI(title="TradingBot API", version="0.1.0")

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        with request_latency.labels(request.method, request.url.path).time():
            response = await call_next(request)
        return response

    app.include_router(routes.router)

    @app.get("/metrics")
    async def metrics() -> Response:
        return PlainTextResponse(generate_latest().decode())

    @app.on_event("startup")
    async def _startup():
        settings = get_settings()
        logger.info("starting tradingbot", extra={"mode": settings.trading_mode})

    return app


app = create_app()
