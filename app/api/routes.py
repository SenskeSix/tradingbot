from __future__ import annotations

import uuid
from datetime import datetime
import os

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import deps
from app.api import schemas
from app.api.auth import verify_internal_token
from app.config import Settings
from app.db import models
from app.metrics import alerts_received
from app.services.reporting import daily_pnl_report
from app.utils.crypto import verify_hmac
from app.workers.tasks import enqueue_trade_task

router = APIRouter()


async def _verify_signature(request: Request, settings: Settings) -> bytes:
    raw_body = await request.body()
    sig_header = request.headers.get("X-Signature") or request.query_params.get("sig")
    if sig_header:
        if not verify_hmac(raw_body, settings.webhook_secret, sig_header):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid signature")
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header != f"Bearer {settings.webhook_secret}":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing signature")
    return raw_body


@router.post("/webhook/tradingview", response_model=schemas.AlertResponse)
async def tradingview_webhook(
    request: Request,
    db: Session = Depends(deps.get_db_dep),
    settings: Settings = Depends(deps.get_settings_dep),
):
    raw_body = await _verify_signature(request, settings)

    try:
        payload = schemas.AlertIn.model_validate_json(raw_body)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc

    alert = models.Alert(
        id=payload.id,
        symbol=payload.symbol,
        side=payload.side,
        price=payload.price,
        confidence=payload.confidence,
        timeframe=payload.timeframe,
        received_at=datetime.utcnow(),
    )

    db.add(alert)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Duplicate alert, still return queued to keep TV happy but don't re-enqueue
        return schemas.AlertResponse(status="duplicate", alert_id=payload.id)

    alerts_received.inc()
    enqueue_trade_task.delay(str(payload.id))
    return schemas.AlertResponse(status="queued", alert_id=payload.id)


@router.get("/healthz", response_model=schemas.HealthResponse)
async def healthz(
    db: Session = Depends(deps.get_db_dep),
    settings: Settings = Depends(deps.get_settings_dep),
):
    build_sha = os.getenv("GIT_SHA", "dev")

    try:
        db.execute(select(1))
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "error"

    redis_status = "ok"
    client = aioredis.from_url(settings.redis_url)
    try:
        await client.ping()
    except Exception:  # noqa: BLE001
        redis_status = "error"
    finally:
        await client.close()

    return schemas.HealthResponse(status="ok", build_sha=build_sha, db=db_status, redis=redis_status)


@router.get("/reports/daily", response_model=list[schemas.ReportResponse], dependencies=[Depends(verify_internal_token)])
async def daily_report(
    db: Session = Depends(deps.get_db_dep),
):
    target_date = datetime.utcnow().date()
    report = daily_pnl_report(db, target_date)
    return [schemas.ReportResponse(**row) for row in report]
