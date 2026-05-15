"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from learning_engine.collector import collect_updates
from learning_engine.config import HOST, PORT, PUBLIC_DIR
from learning_engine.models import InterestsPayload, UpdatesResponse
from learning_engine.storage import ensure_data_file, read_interests, write_interests


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_api: FastAPI) -> AsyncIterator[None]:
        ensure_data_file()
        yield

    api = FastAPI(
        title="Learning Engine",
        summary="Local-first API for personal interests and daily briefing source collection.",
        version="0.3.0",
        lifespan=lifespan,
    )

    @api.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse(url="/index.html")

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/api/interests", response_model=InterestsPayload)
    def get_interests() -> InterestsPayload:
        return read_interests()

    @api.post("/api/interests")
    def save_interests(payload: InterestsPayload) -> dict[str, object]:
        write_interests(payload)
        return {
            "ok": True,
            "saved": read_interests().model_dump(mode="json", by_alias=True),
        }

    @api.get("/api/updates", response_model=UpdatesResponse)
    def updates(
        days: Annotated[int | None, Query(ge=1)] = None,
    ) -> UpdatesResponse:
        try:
            return collect_updates(read_interests(), days=days)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    api.mount(
        "/",
        StaticFiles(directory=PUBLIC_DIR, html=True, check_dir=False),
        name="public",
    )
    return api


app = create_app()


def run() -> None:
    uvicorn.run("learning_engine.app:app", host=HOST, port=PORT, reload=False)
