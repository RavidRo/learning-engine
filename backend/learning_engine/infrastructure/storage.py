"""PostgreSQL-backed interest persistence."""

from datetime import UTC, datetime
from typing import cast

from sqlalchemy import Column, DateTime
from sqlalchemy.engine import Engine
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from learning_engine.config import DATABASE_URL
from learning_engine.domain.interests import Interest, InterestSource, InterestsPayload, Priority
from learning_engine.domain.source_types import SourceType


class StoredInterest(SQLModel, table=True):
    """Relational persistence row for an interest."""

    __tablename__ = "interests"

    interest_id: str = Field(primary_key=True)
    name: str
    description: str
    priority: str
    enabled: bool
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    sources: list["StoredInterestSource"] = Relationship(
        back_populates="interest",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StoredInterestSource(SQLModel, table=True):
    """Relational persistence row for a source attached to an interest."""

    __tablename__ = "interest_sources"

    source_id: str = Field(primary_key=True)
    interest_id: str = Field(foreign_key="interests.interest_id", index=True)
    label: str
    source_type: str
    url: str
    image_url: str | None = None
    enabled: bool
    deleted_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    interest: StoredInterest = Relationship(back_populates="sources")
    ignore_keywords: list["StoredSourceIgnoreKeyword"] = Relationship(
        back_populates="source",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StoredSourceIgnoreKeyword(SQLModel, table=True):
    """Relational persistence row for a source ignore keyword."""

    __tablename__ = "source_ignore_keywords"

    keyword_id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(foreign_key="interest_sources.source_id", index=True)
    keyword: str

    source: StoredInterestSource = Relationship(back_populates="ignore_keywords")


class InterestStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def ensure_data_store(self) -> None:
        SQLModel.metadata.create_all(self.engine)

    def read_interests(self) -> InterestsPayload:
        self.ensure_data_store()
        with Session(self.engine) as session:
            stored_interests = session.exec(select(StoredInterest)).all()
            return InterestsPayload(
                interests=[
                    self._interest_from_stored(stored_interest)
                    for stored_interest in sorted(stored_interests, key=lambda interest: interest.name)
                ]
            )

    def write_interests(self, payload: InterestsPayload) -> None:
        self.ensure_data_store()
        with Session(self.engine) as session:
            self._write_interests(session, payload)
            session.commit()

    def _write_interests(self, session: Session, payload: InterestsPayload) -> None:
        stored_interests = self._stored_interests_from_domain(payload.interests)
        for stored_interest in session.exec(select(StoredInterest)).all():
            session.delete(stored_interest)
        session.flush()
        session.add_all(stored_interests)

    def _stored_interests_from_domain(self, interests: list[Interest]) -> list[StoredInterest]:
        interest_ids: set[str] = set()
        source_ids: set[str] = set()
        stored_interests: list[StoredInterest] = []
        for interest in interests:
            interest_id = self._interest_id_or_raise(interest)
            self._raise_on_duplicate_id(interest_id, interest_ids, "interest")
            stored_sources: list[StoredInterestSource] = []
            for source in interest.sources:
                source_id = self._source_id_or_raise(source)
                self._raise_on_duplicate_id(source_id, source_ids, "source")
                stored_sources.append(self._stored_source_from_domain(source, source_id))
            stored_interests.append(self._stored_interest_from_domain(interest, interest_id, stored_sources))
        return stored_interests

    def _stored_interest_from_domain(
        self,
        interest: Interest,
        interest_id: str,
        stored_sources: list[StoredInterestSource],
    ) -> StoredInterest:
        return StoredInterest(
            interest_id=interest_id,
            name=interest.name,
            description=interest.description,
            priority=interest.priority,
            enabled=interest.enabled,
            deleted_at=self._datetime_from_domain(interest.deleted_at),
            sources=stored_sources,
        )

    def _stored_source_from_domain(self, source: InterestSource, source_id: str) -> StoredInterestSource:
        return StoredInterestSource(
            source_id=source_id,
            label=source.label,
            source_type=source.type,
            url=source.url,
            image_url=source.image_url,
            enabled=source.enabled,
            deleted_at=self._datetime_from_domain(source.deleted_at),
            ignore_keywords=[StoredSourceIgnoreKeyword(keyword=keyword) for keyword in source.ignore_keywords],
        )

    def _interest_from_stored(self, stored_interest: StoredInterest) -> Interest:
        return Interest(
            id=stored_interest.interest_id,
            name=stored_interest.name,
            description=stored_interest.description,
            priority=cast(Priority, stored_interest.priority),
            enabled=stored_interest.enabled,
            deleted_at=self._datetime_to_domain(stored_interest.deleted_at),
            sources=[
                self._source_from_stored(stored_source)
                for stored_source in sorted(stored_interest.sources, key=lambda source: source.label)
            ],
        )

    def _source_from_stored(self, stored_source: StoredInterestSource) -> InterestSource:
        return InterestSource(
            id=stored_source.source_id,
            label=stored_source.label,
            type=cast(SourceType, stored_source.source_type),
            url=stored_source.url,
            image_url=stored_source.image_url,
            enabled=stored_source.enabled,
            deleted_at=self._datetime_to_domain(stored_source.deleted_at),
            ignore_keywords=sorted(stored_keyword.keyword for stored_keyword in stored_source.ignore_keywords),
        )

    def _interest_id_or_raise(self, interest: Interest) -> str:
        if interest.id is None:
            raise ValueError("Interest id is required for database persistence")
        return interest.id

    def _source_id_or_raise(self, source: InterestSource) -> str:
        if source.id is None:
            raise ValueError("Source id is required for database persistence")
        return source.id

    def _raise_on_duplicate_id(self, id_value: str, seen_ids: set[str], label: str) -> None:
        if id_value in seen_ids:
            raise ValueError(f"Duplicate {label} id is not allowed: {id_value}")
        seen_ids.add(id_value)

    def _datetime_from_domain(self, value: str | None) -> datetime | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Deleted timestamp must include timezone information")
        return parsed

    def _datetime_to_domain(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _database_url_for_sqlalchemy(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def create_interest_store(database_url: str) -> InterestStore:
    return InterestStore(create_engine(_database_url_for_sqlalchemy(database_url), pool_pre_ping=True))


DEFAULT_STORE = create_interest_store(DATABASE_URL)
