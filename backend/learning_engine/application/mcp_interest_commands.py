"""Command-style interest management operations for MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError, field_validator

from learning_engine.application.ports import InterestRepository
from learning_engine.domain.interests import Interest, InterestSource, InterestsPayload, Priority
from learning_engine.domain.source_types import SourceType, normalize_source_type

IdFactory = Callable[[], str]
CommandResponse = dict[str, Any]
WriteAction = Literal["pause", "resume", "delete"]

MAX_GENERATED_ID_ATTEMPTS = 10


class McpInterestCommandError(Exception):
    """Base error raised by MCP interest commands."""


class McpInterestNotFoundError(McpInterestCommandError):
    """Raised when a command references a missing or deleted record."""


class McpInterestValidationError(McpInterestCommandError):
    """Raised when a command would create invalid interest state."""


class SourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    label: str = "Source"
    type: SourceType
    url: str
    image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
    )
    ignore_keywords: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ignoreKeywords", "ignore_keywords"),
        serialization_alias="ignoreKeywords",
    )
    enabled: bool = True

    @field_validator("type", mode="before")
    @classmethod
    def normalize_source_type(cls, value: object) -> SourceType:
        return normalize_source_type(value)


class InterestCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    priority: Priority = "medium"
    enabled: bool = True
    sources: list[SourceInput] = Field(min_length=1)


class InterestUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    priority: Priority | None = None
    enabled: bool | None = None


class SourceUpdateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    label: str | None = None
    type: SourceType | None = None
    url: str | None = None
    image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("imageUrl", "image_url"),
        serialization_alias="imageUrl",
    )
    ignore_keywords: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices("ignoreKeywords", "ignore_keywords"),
        serialization_alias="ignoreKeywords",
    )
    enabled: bool | None = None

    @field_validator("type", mode="before")
    @classmethod
    def normalize_source_type(cls, value: object) -> SourceType | None:
        if value is None:
            return None
        return normalize_source_type(value)


def list_interests(repository: InterestRepository, *, include_deleted: bool = False) -> CommandResponse:
    payload = repository.read_interests()
    interests = [
        _interest_response(interest, include_deleted=include_deleted)
        for interest in payload.interests
        if include_deleted or interest.deleted_at is None
    ]
    return {"interests": interests}


def _default_id_factory() -> str:
    return uuid4().hex


def create_interest(
    repository: InterestRepository,
    command: InterestCreateInput,
    *,
    id_factory: IdFactory = _default_id_factory,
) -> CommandResponse:
    payload = repository.read_interests()
    used_ids = _all_ids(payload)
    interest_id = _generate_id("interest", used_ids, id_factory)
    sources = [_source_from_input(source, _generate_id("source", used_ids, id_factory)) for source in command.sources]
    interest = Interest(
        id=interest_id,
        name=command.name,
        description=command.description,
        priority=command.priority,
        enabled=command.enabled,
        sources=sources,
    )
    updated = InterestsPayload(interests=[*payload.interests, interest])
    _write_validated(repository, updated)
    return {"interest": _interest_response(interest, include_deleted=True)}


def update_interest(
    repository: InterestRepository,
    interest_id: str,
    command: InterestUpdateInput,
) -> CommandResponse:
    payload = repository.read_interests()
    interests = list(payload.interests)
    index, interest = _find_active_interest(interests, interest_id)
    updated_interest = interest.model_copy(
        update={key: value for key, value in command.model_dump(exclude_unset=True).items() if value is not None}
    )
    interests[index] = updated_interest
    _write_validated(repository, InterestsPayload(interests=interests))
    return {"interest": _interest_response(updated_interest, include_deleted=True)}


def pause_interest(repository: InterestRepository, interest_id: str) -> CommandResponse:
    return _set_interest_state(repository, interest_id, "pause")


def resume_interest(repository: InterestRepository, interest_id: str) -> CommandResponse:
    return _set_interest_state(repository, interest_id, "resume")


def delete_interest(repository: InterestRepository, interest_id: str) -> CommandResponse:
    return _set_interest_state(repository, interest_id, "delete")


def add_source(
    repository: InterestRepository,
    interest_id: str,
    command: SourceInput,
    *,
    id_factory: IdFactory = _default_id_factory,
) -> CommandResponse:
    payload = repository.read_interests()
    interests = list(payload.interests)
    index, interest = _find_active_interest(interests, interest_id)
    source = _source_from_input(command, _generate_id("source", _all_ids(payload), id_factory))
    updated_interest = interest.model_copy(update={"sources": [*interest.sources, source]})
    interests[index] = updated_interest
    _write_validated(repository, InterestsPayload(interests=interests))
    return {"source": _source_response(source, include_deleted=True)}


def update_source(
    repository: InterestRepository,
    interest_id: str,
    source_id: str,
    command: SourceUpdateInput,
) -> CommandResponse:
    payload = repository.read_interests()
    interests = list(payload.interests)
    interest_index, interest = _find_active_interest(interests, interest_id)
    sources = list(interest.sources)
    source_index, source = _find_active_source(sources, source_id, interest_id)
    updated_source = source.model_copy(
        update={key: value for key, value in command.model_dump(exclude_unset=True).items() if value is not None}
    )
    sources[source_index] = updated_source
    interests[interest_index] = interest.model_copy(update={"sources": sources})
    _write_validated(repository, InterestsPayload(interests=interests))
    return {"source": _source_response(updated_source, include_deleted=True)}


def pause_source(repository: InterestRepository, interest_id: str, source_id: str) -> CommandResponse:
    return _set_source_state(repository, interest_id, source_id, "pause")


def resume_source(repository: InterestRepository, interest_id: str, source_id: str) -> CommandResponse:
    return _set_source_state(repository, interest_id, source_id, "resume")


def delete_source(repository: InterestRepository, interest_id: str, source_id: str) -> CommandResponse:
    return _set_source_state(repository, interest_id, source_id, "delete")


def _set_interest_state(repository: InterestRepository, interest_id: str, action: WriteAction) -> CommandResponse:
    payload = repository.read_interests()
    interests = list(payload.interests)
    index, interest = _find_active_interest(interests, interest_id)
    update = _state_update(action)
    updated_interest = interest.model_copy(update=update)
    interests[index] = updated_interest
    _write_validated(repository, InterestsPayload(interests=interests))
    return {"interest": _interest_response(updated_interest, include_deleted=True)}


def _set_source_state(
    repository: InterestRepository,
    interest_id: str,
    source_id: str,
    action: WriteAction,
) -> CommandResponse:
    payload = repository.read_interests()
    interests = list(payload.interests)
    interest_index, interest = _find_active_interest(interests, interest_id)
    sources = list(interest.sources)
    source_index, source = _find_active_source(sources, source_id, interest_id)
    updated_source = source.model_copy(update=_state_update(action))
    sources[source_index] = updated_source
    interests[interest_index] = interest.model_copy(update={"sources": sources})
    _write_validated(repository, InterestsPayload(interests=interests))
    return {"source": _source_response(updated_source, include_deleted=True)}


def _state_update(action: WriteAction) -> CommandResponse:
    if action == "pause":
        return {"enabled": False}
    if action == "resume":
        return {"enabled": True}
    return {"deleted_at": _deleted_timestamp()}


def _write_validated(repository: InterestRepository, payload: InterestsPayload) -> None:
    try:
        validated = InterestsPayload.model_validate(payload.model_dump(mode="json", by_alias=True))
    except ValidationError as exc:
        raise McpInterestValidationError(str(exc)) from exc
    repository.write_interests(validated)


def _source_from_input(source: SourceInput, source_id: str) -> InterestSource:
    return InterestSource(
        id=source_id,
        label=source.label,
        type=source.type,
        url=source.url,
        image_url=source.image_url,
        ignore_keywords=source.ignore_keywords,
        enabled=source.enabled,
    )


def _find_active_interest(interests: list[Interest], interest_id: str) -> tuple[int, Interest]:
    for index, interest in enumerate(interests):
        if interest.id == interest_id and interest.deleted_at is None:
            return index, interest
    raise McpInterestNotFoundError(f"Interest not found: {interest_id}")


def _find_active_source(
    sources: list[InterestSource],
    source_id: str,
    interest_id: str,
) -> tuple[int, InterestSource]:
    for index, source in enumerate(sources):
        if source.id == source_id and source.deleted_at is None:
            return index, source
    raise McpInterestNotFoundError(f"Source not found for interest {interest_id}: {source_id}")


def _generate_id(prefix: str, used_ids: set[str], id_factory: IdFactory) -> str:
    for _ in range(MAX_GENERATED_ID_ATTEMPTS):
        generated = f"{prefix}-{id_factory()}"
        if generated not in used_ids:
            used_ids.add(generated)
            return generated
    raise McpInterestValidationError(f"Could not generate a unique {prefix} id")


def _all_ids(payload: InterestsPayload) -> set[str]:
    ids = {interest.id for interest in payload.interests if interest.id is not None}
    ids.update(source.id for interest in payload.interests for source in interest.sources if source.id is not None)
    return ids


def _deleted_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _interest_response(interest: Interest, *, include_deleted: bool) -> CommandResponse:
    response = interest.model_dump(mode="json", by_alias=True, exclude={"sources"})
    if not include_deleted:
        response.pop("deletedAt", None)
    response["sources"] = [
        _source_response(source, include_deleted=include_deleted)
        for source in interest.sources
        if include_deleted or source.deleted_at is None
    ]
    return response


def _source_response(source: InterestSource, *, include_deleted: bool) -> CommandResponse:
    response = source.model_dump(mode="json", by_alias=True)
    if include_deleted:
        return response
    response.pop("deletedAt", None)
    return response
