from __future__ import annotations

import pytest
from pydantic import ValidationError

from learning_engine.application.mcp_interest_commands import (
    InterestCreateInput,
    InterestUpdateInput,
    McpInterestNotFoundError,
    McpInterestValidationError,
    SourceInput,
    SourceUpdateInput,
    add_source,
    create_interest,
    delete_interest,
    delete_source,
    list_interests,
    pause_interest,
    pause_source,
    resume_interest,
    resume_source,
    update_interest,
    update_source,
)
from learning_engine.domain.interests import InterestsPayload


class StubInterestRepository:
    def __init__(self, payload: InterestsPayload) -> None:
        self._payload = payload
        self.saved_payloads: list[InterestsPayload] = []

    def ensure_data_store(self) -> None:
        return None

    def read_interests(self) -> InterestsPayload:
        return self.saved_payloads[-1] if self.saved_payloads else self._payload

    def write_interests(self, payload: InterestsPayload) -> None:
        self.saved_payloads.append(payload)


def test_list_interests_excludes_deleted_records_by_default() -> None:
    repository = StubInterestRepository(_payload())

    response = list_interests(repository)

    assert response["interests"] == [
        {
            "id": "typescript",
            "name": "TypeScript",
            "description": "",
            "priority": "high",
            "enabled": True,
            "sources": [
                {
                    "id": "ts-feed",
                    "label": "TypeScript Feed",
                    "type": "feed",
                    "url": "https://example.com/ts.xml",
                    "imageUrl": None,
                    "ignoreKeywords": ["jobs"],
                    "enabled": True,
                }
            ],
        }
    ]


def test_list_interests_can_include_deleted_records() -> None:
    repository = StubInterestRepository(_payload())

    response = list_interests(repository, include_deleted=True)

    interests = response["interests"]
    assert isinstance(interests, list)
    assert [interest["id"] for interest in interests] == ["typescript", "deleted-interest"]
    assert interests[0]["sources"][1]["deletedAt"] == "2026-01-01T00:00:00.000Z"
    assert interests[1]["deletedAt"] == "2026-01-02T00:00:00.000Z"


def test_create_interest_generates_ids_and_preserves_existing_records() -> None:
    repository = StubInterestRepository(_payload())
    ids = iter(["new-interest", "new-source"])

    response = create_interest(
        repository,
        InterestCreateInput(
            name="  Python  ",
            description="  Core Python  ",
            priority="medium",
            sources=[SourceInput(label=" Docs ", type="page", url=" https://docs.python.org ")],
        ),
        id_factory=lambda: next(ids),
    )

    saved = repository.saved_payloads[-1]
    assert [interest.id for interest in saved.interests] == ["typescript", "deleted-interest", "interest-new-interest"]
    created = saved.interests[-1]
    assert created.name == "Python"
    assert created.description == "Core Python"
    assert created.sources[0].id == "source-new-source"
    assert created.sources[0].label == "Docs"
    assert created.sources[0].url == "https://docs.python.org"
    assert response["interest"]["id"] == "interest-new-interest"


def test_create_interest_retries_duplicate_generated_ids() -> None:
    repository = StubInterestRepository(
        InterestsPayload.model_validate(
            {
                "interests": [
                    {
                        "id": "interest-typescript",
                        "name": "TypeScript",
                        "sources": [{"id": "source-ts-feed", "type": "feed", "url": "https://example.com/feed.xml"}],
                    }
                ]
            }
        )
    )
    ids = iter(["typescript", "new-interest", "ts-feed", "new-source"])

    create_interest(
        repository,
        InterestCreateInput(
            name="Python",
            sources=[SourceInput(label="Docs", type="page", url="https://docs.python.org")],
        ),
        id_factory=lambda: next(ids),
    )

    created = repository.saved_payloads[-1].interests[-1]
    assert created.id == "interest-new-interest"
    assert created.sources[0].id == "source-new-source"


def test_create_interest_raises_validation_error_when_unique_id_cannot_be_generated() -> None:
    repository = StubInterestRepository(_payload_with_id("interest-duplicate"))

    with pytest.raises(McpInterestValidationError, match="unique interest id"):
        create_interest(
            repository,
            InterestCreateInput(
                name="Python",
                sources=[SourceInput(label="Docs", type="page", url="https://docs.python.org")],
            ),
            id_factory=lambda: "duplicate",
        )

    assert repository.saved_payloads == []


def test_update_pause_resume_and_delete_interest_by_id() -> None:
    repository = StubInterestRepository(_payload())

    updated = update_interest(
        repository,
        "typescript",
        InterestUpdateInput(name="TS", description="Typed JavaScript", priority="low", enabled=False),
    )
    paused = pause_interest(repository, "typescript")
    resumed = resume_interest(repository, "typescript")
    deleted = delete_interest(repository, "typescript")

    assert updated["interest"]["name"] == "TS"
    assert paused["interest"]["enabled"] is False
    assert resumed["interest"]["enabled"] is True
    saved = repository.saved_payloads[-1].interests[0]
    assert saved.deleted_at is not None
    assert deleted["interest"]["deletedAt"] == saved.deleted_at
    assert repository.saved_payloads[-1].interests[1].id == "deleted-interest"


def test_interest_write_missing_id_does_not_write() -> None:
    repository = StubInterestRepository(_payload())

    with pytest.raises(McpInterestNotFoundError, match="Interest not found"):
        update_interest(repository, "missing", InterestUpdateInput(name="Nope"))

    assert repository.saved_payloads == []


def test_invalid_command_input_does_not_write() -> None:
    repository = StubInterestRepository(_payload())

    with pytest.raises(ValidationError):
        InterestCreateInput.model_validate({"name": "Invalid", "priority": "urgent", "sources": []})

    assert repository.saved_payloads == []


def test_add_update_pause_resume_and_delete_source_by_id() -> None:
    repository = StubInterestRepository(_payload())

    added = add_source(
        repository,
        "typescript",
        SourceInput(label="Handbook", type="page", url="https://example.com/handbook"),
        id_factory=lambda: "handbook",
    )
    updated = update_source(
        repository,
        "typescript",
        "source-handbook",
        SourceUpdateInput(label="TS Handbook", ignore_keywords=["draft", " jobs "], enabled=False),
    )
    paused = pause_source(repository, "typescript", "source-handbook")
    resumed = resume_source(repository, "typescript", "source-handbook")
    deleted = delete_source(repository, "typescript", "source-handbook")

    assert added["source"]["id"] == "source-handbook"
    assert updated["source"]["label"] == "TS Handbook"
    assert repository.saved_payloads[-1].interests[0].sources[0].id == "ts-feed"
    assert paused["source"]["enabled"] is False
    assert resumed["source"]["enabled"] is True
    saved_source = repository.saved_payloads[-1].interests[0].sources[-1]
    assert saved_source.deleted_at is not None
    assert deleted["source"]["deletedAt"] == saved_source.deleted_at


def test_source_write_missing_id_does_not_write() -> None:
    repository = StubInterestRepository(_payload())

    with pytest.raises(McpInterestNotFoundError, match="Source not found"):
        update_source(repository, "typescript", "missing", SourceUpdateInput(label="Nope"))

    assert repository.saved_payloads == []


def _payload() -> InterestsPayload:
    return InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "id": "typescript",
                    "name": "TypeScript",
                    "priority": "high",
                    "sources": [
                        {
                            "id": "ts-feed",
                            "label": "TypeScript Feed",
                            "type": "feed",
                            "url": "https://example.com/ts.xml",
                            "ignoreKeywords": ["jobs"],
                        },
                        {
                            "id": "deleted-source",
                            "label": "Old Source",
                            "type": "page",
                            "url": "https://example.com/old",
                            "deletedAt": "2026-01-01T00:00:00.000Z",
                        },
                    ],
                },
                {
                    "id": "deleted-interest",
                    "name": "Deleted",
                    "deletedAt": "2026-01-02T00:00:00.000Z",
                    "sources": [
                        {
                            "id": "deleted-interest-source",
                            "label": "Deleted Source",
                            "type": "page",
                            "url": "https://example.com/deleted",
                        }
                    ],
                },
            ]
        }
    )


def _payload_with_id(interest_id: str) -> InterestsPayload:
    return InterestsPayload.model_validate(
        {
            "interests": [
                {
                    "id": interest_id,
                    "name": "Duplicate",
                    "sources": [{"id": "source-duplicate", "type": "feed", "url": "https://example.com/feed.xml"}],
                }
            ]
        }
    )
