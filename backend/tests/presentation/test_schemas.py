from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from learning_engine.presentation.schemas import InterestExportEnvelope


def test_interest_export_envelope_serializes_complete_payload_with_camel_case_aliases() -> None:
    exported_at = datetime(2026, 6, 13, 13, 0, tzinfo=UTC)
    envelope = InterestExportEnvelope.model_validate(
        {
            "schemaVersion": 1,
            "exportedAt": exported_at.isoformat(),
            "interests": [
                {
                    "id": "active",
                    "name": "Active",
                    "sources": [{"id": "active-feed", "type": "feed", "url": "https://example.com/feed.xml"}],
                },
                {
                    "deletedAt": "2026-06-12T10:00:00Z",
                    "enabled": False,
                    "id": "archived",
                    "name": "Archived",
                    "sources": [
                        {
                            "deletedAt": "2026-06-12T10:00:00Z",
                            "enabled": False,
                            "id": "archived-feed",
                            "type": "feed",
                            "url": "https://example.com/archived.xml",
                        }
                    ],
                },
            ],
        }
    )

    exported = envelope.model_dump(mode="json", by_alias=True)

    assert exported["schemaVersion"] == 1
    assert exported["exportedAt"] == "2026-06-13T13:00:00Z"
    assert [interest["id"] for interest in exported["interests"]] == ["active", "archived"]
    assert exported["interests"][1]["deletedAt"] == "2026-06-12T10:00:00Z"
    assert exported["interests"][1]["enabled"] is False
    assert exported["interests"][1]["sources"][0]["deletedAt"] == "2026-06-12T10:00:00Z"
    assert exported["interests"][1]["sources"][0]["enabled"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"interests": []},
        {"schemaVersion": 2, "exportedAt": "2026-06-13T13:00:00Z", "interests": []},
        {"schemaVersion": 1, "exportedAt": "2026-06-13T13:00:00Z", "interests": [{"sources": [{"type": "feed"}]}]},
    ],
)
def test_interest_export_envelope_rejects_invalid_import_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        InterestExportEnvelope.model_validate(payload)
