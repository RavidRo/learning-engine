"""FastAPI routes for interests, source images, and updates."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, status
from pydantic import ValidationError

from learning_engine.application.collect_updates import (
    CollectUpdatesDependencies,
    SourceUpdatesCacheOptions,
    collect_updates,
)
from learning_engine.application.ports import SourceImageProvider
from learning_engine.application.resolve_source_image import (
    SourceImageConfigurationError,
    SourceImageProviderError,
    SourceImageProviderUnavailableError,
    resolve_source_image,
)
from learning_engine.application.responses import UpdatesResponse
from learning_engine.common.timeframe import Timeframe
from learning_engine.domain.interests import Interests
from learning_engine.presentation.schemas import (
    BatchSourceImageRequest,
    BatchSourceImageResponse,
    BatchSourceImageResult,
    InterestExportEnvelope,
    SourceImageRequest,
    SourceImageResponse,
)
from learning_engine.presentation.state import get_app_state

BATCH_SOURCE_IMAGE_MAX_CONCURRENCY = 10
BATCH_SOURCE_IMAGE_MAX_REQUESTS = 50


def _timeframe_from_days(days: int | None, now: datetime) -> Timeframe:
    if days is None:
        return Timeframe.until(now)
    return Timeframe.ending_at(now, timedelta(days=days))


async def _source_image_response(
    payload: SourceImageRequest,
    source_image_provider: SourceImageProvider,
) -> SourceImageResponse:
    try:
        image_url = await resolve_source_image(payload.source_type, payload.url, source_image_provider)
    except SourceImageConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SourceImageProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except SourceImageProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not resolve source image",
        ) from exc
    return SourceImageResponse(image_url=image_url)


async def _batch_source_image_result(
    payload: BatchSourceImageRequest,
    source_image_provider: SourceImageProvider,
) -> BatchSourceImageResult:
    try:
        response = await _source_image_response(payload, source_image_provider)
    except HTTPException as exc:
        return BatchSourceImageResult(
            source_id=payload.source_id,
            image_url=None,
            status=exc.status_code,
            error=str(exc.detail),
        )
    return BatchSourceImageResult(source_id=payload.source_id, image_url=response.image_url)


async def _batch_source_image_results(
    payload: list[BatchSourceImageRequest],
    source_image_provider: SourceImageProvider,
) -> list[BatchSourceImageResult]:
    if len(payload) > BATCH_SOURCE_IMAGE_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Batch source image requests are limited to {BATCH_SOURCE_IMAGE_MAX_REQUESTS} sources",
        )

    semaphore = asyncio.Semaphore(BATCH_SOURCE_IMAGE_MAX_CONCURRENCY)

    async def resolve_with_limit(source: BatchSourceImageRequest) -> BatchSourceImageResult:
        async with semaphore:
            return await _batch_source_image_result(source, source_image_provider)

    results = await asyncio.gather(*(resolve_with_limit(source) for source in payload))
    return list(results)


def interests_router(api: FastAPI) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/interests", response_model=Interests)
    def get_interests() -> Interests:
        return get_app_state(api).interest_repository.read_interests()

    @router.post("/interests")
    def save_interests(interests: Interests) -> dict[str, object]:
        repository = get_app_state(api).interest_repository
        repository.write_interests(interests)
        return {
            "ok": True,
            "saved": repository.read_interests().model_dump(mode="json", by_alias=True),
        }

    @router.get("/interests/export", response_model=InterestExportEnvelope)
    def export_interests() -> InterestExportEnvelope:
        return InterestExportEnvelope(
            schema_version=1,
            exported_at=datetime.now(UTC),
            interests=get_app_state(api).interest_repository.read_interests().interests,
        )

    @router.post("/interests/import")
    async def import_interests(request: Request) -> dict[str, object]:
        try:
            payload = await request.json()
            imported = InterestExportEnvelope.model_validate(payload)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid interest export file",
            ) from exc
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid interest export JSON",
            ) from exc

        repository = get_app_state(api).interest_repository
        repository.write_interests(Interests(interests=imported.interests))
        return {
            "ok": True,
            "saved": repository.read_interests().model_dump(mode="json", by_alias=True),
        }

    @router.post("/source-image", response_model=SourceImageResponse)
    async def source_image(payload: SourceImageRequest) -> SourceImageResponse:
        app_state = get_app_state(api)
        return await _source_image_response(payload, app_state.source_image_provider)

    @router.post("/source-images", response_model=BatchSourceImageResponse)
    async def source_images(payload: list[BatchSourceImageRequest]) -> BatchSourceImageResponse:
        app_state = get_app_state(api)
        results = await _batch_source_image_results(payload, app_state.source_image_provider)
        return BatchSourceImageResponse(images=results)

    @router.get("/updates", response_model=UpdatesResponse)
    async def updates(
        days: Annotated[int | None, Query(ge=1)] = None,
    ) -> UpdatesResponse:
        timeframe = _timeframe_from_days(days, datetime.now(UTC))
        cache_scope = "all" if days is None else f"days:{days}"
        app_state = get_app_state(api)
        source_updates_cache_options = SourceUpdatesCacheOptions(
            cache=app_state.source_updates_cache,
            scope=cache_scope,
        )
        return await collect_updates(
            app_state.interest_repository.read_interests(),
            timeframe=timeframe,
            dependencies=CollectUpdatesDependencies(
                source_update_collector=app_state.source_update_collector,
                source_image_provider=app_state.source_image_provider,
            ),
            source_updates_cache=source_updates_cache_options,
        )

    return router
