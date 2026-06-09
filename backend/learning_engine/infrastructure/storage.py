"""PostgreSQL-backed interest persistence."""

from typing import cast

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
    deleted_at: str | None = None

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
    type: str
    url: str
    image_url: str | None = None
    enabled: bool
    deleted_at: str | None = None

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
        for stored_interest in session.exec(select(StoredInterest)).all():
            session.delete(stored_interest)
        session.flush()
        for interest in payload.interests:
            session.add(self._stored_interest_from_domain(interest))

    def _stored_interest_from_domain(self, interest: Interest) -> StoredInterest:
        return StoredInterest(
            interest_id=self._interest_id_or_raise(interest),
            name=interest.name,
            description=interest.description,
            priority=interest.priority,
            enabled=interest.enabled,
            deleted_at=interest.deleted_at,
            sources=[self._stored_source_from_domain(source) for source in interest.sources],
        )

    def _stored_source_from_domain(self, source: InterestSource) -> StoredInterestSource:
        return StoredInterestSource(
            source_id=self._source_id_or_raise(source),
            label=source.label,
            type=source.type,
            url=source.url,
            image_url=source.image_url,
            enabled=source.enabled,
            deleted_at=source.deleted_at,
            ignore_keywords=[StoredSourceIgnoreKeyword(keyword=keyword) for keyword in source.ignore_keywords],
        )

    def _interest_from_stored(self, stored_interest: StoredInterest) -> Interest:
        return Interest(
            id=stored_interest.interest_id,
            name=stored_interest.name,
            description=stored_interest.description,
            priority=cast(Priority, stored_interest.priority),
            enabled=stored_interest.enabled,
            deleted_at=stored_interest.deleted_at,
            sources=[
                self._source_from_stored(stored_source)
                for stored_source in sorted(stored_interest.sources, key=lambda source: source.label)
            ],
        )

    def _source_from_stored(self, stored_source: StoredInterestSource) -> InterestSource:
        return InterestSource(
            id=stored_source.source_id,
            label=stored_source.label,
            type=cast(SourceType, stored_source.type),
            url=stored_source.url,
            image_url=stored_source.image_url,
            enabled=stored_source.enabled,
            deleted_at=stored_source.deleted_at,
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


def create_interest_store(database_url: str) -> InterestStore:
    return InterestStore(create_engine(database_url, pool_pre_ping=True))


DEFAULT_STORE = create_interest_store(DATABASE_URL)
