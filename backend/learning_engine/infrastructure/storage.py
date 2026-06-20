"""PostgreSQL-backed interest persistence."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.engine import Engine
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from learning_engine.application.auth import UserContext
from learning_engine.config import DATABASE_URL
from learning_engine.domain.collections import (
    FIXED_COLLECTIONS,
    CollectionId,
    CollectionNotFoundError,
    Collections,
    SavedCollectionUpdate,
    SavedUpdateSnapshot,
    UpdateCollection,
    collection_name,
)
from learning_engine.domain.interests import (
    Interest,
    Interests,
    InterestSource,
    Priority,
)
from learning_engine.domain.source_types import SourceType
from learning_engine.domain.updates import SourceInterest


class StoredInterest(SQLModel, table=True):
    """Relational persistence row for an interest."""

    __tablename__ = "interests"

    interest_id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
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
    interest_id: str = Field(sa_column=Column(ForeignKey("interests.interest_id"), index=True, nullable=False))
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
    source_id: str = Field(sa_column=Column(ForeignKey("interest_sources.source_id"), index=True, nullable=False))
    keyword: str

    source: StoredInterestSource = Relationship(back_populates="ignore_keywords")


class StoredCollection(SQLModel, table=True):
    """Relational persistence row for a fixed update collection."""

    __tablename__ = "collections"

    user_id: str = Field(primary_key=True)
    collection_id: str = Field(primary_key=True)
    name: str

    saved_updates: list["StoredSavedCollectionUpdate"] = Relationship(
        back_populates="collection",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StoredSavedCollectionUpdate(SQLModel, table=True):
    """Relational persistence row for an update saved to a collection."""

    __tablename__ = "saved_collection_updates"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "collection_id"], ["collections.user_id", "collections.collection_id"]),
        UniqueConstraint("user_id", "collection_id", "update_key", name="uq_saved_update_user_collection_key"),
    )

    saved_update_id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    collection_id: str = Field(index=True)
    update_key: str = Field(index=True)
    saved_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    title: str | None = None
    url: str
    summary: str | None = None
    image_url: str | None = None
    published: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    published_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    interest_id: str | None = None
    interest_name: str
    source_id: str | None = None
    source_label: str
    source_image_url: str | None = None
    source_url: str
    source_type: str

    collection: StoredCollection = Relationship(back_populates="saved_updates")


class InterestStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._schema_initialized = False

    def ensure_data_store(self) -> None:
        if self._schema_initialized:
            return
        SQLModel.metadata.create_all(self.engine)
        self._schema_initialized = True

    def list_collections(self, user_context: UserContext) -> Collections:
        self.ensure_data_store()
        with Session(self.engine) as session:
            self._ensure_fixed_collections(session, user_context)
            session.commit()
            stored_collections = session.exec(
                select(StoredCollection)
                .where(StoredCollection.user_id == user_context.user_id)
                .options(selectinload(cast(Any, StoredCollection.saved_updates)))
            ).all()
            collections_by_id = {stored.collection_id: stored for stored in stored_collections}
            return Collections(
                collections=[
                    self._collection_from_stored(collections_by_id[collection_id])
                    for collection_id in FIXED_COLLECTIONS
                    if collection_id in collections_by_id
                ]
            )

    def save_update_to_collection(
        self,
        user_context: UserContext,
        collection_id: CollectionId,
        update_key: str,
        update: SavedUpdateSnapshot,
        saved_at: datetime,
    ) -> SavedCollectionUpdate:
        self.ensure_data_store()
        with Session(self.engine) as session:
            self._ensure_fixed_collections(session, user_context)
            self._raise_on_missing_collection(session, user_context, collection_id)
            existing = self._stored_saved_update(session, user_context, collection_id, update_key)
            if existing is not None:
                return self._saved_update_from_stored(existing)
            stored_update = self._stored_saved_update_from_domain(
                user_context, collection_id, update_key, update, saved_at
            )
            session.add(stored_update)
            session.commit()
            session.refresh(stored_update)
            return self._saved_update_from_stored(stored_update)

    def remove_update_from_collection(
        self,
        user_context: UserContext,
        collection_id: CollectionId,
        update_key: str,
    ) -> None:
        self.ensure_data_store()
        with Session(self.engine) as session:
            self._ensure_fixed_collections(session, user_context)
            self._raise_on_missing_collection(session, user_context, collection_id)
            stored_update = self._stored_saved_update(session, user_context, collection_id, update_key)
            if stored_update is not None:
                session.delete(stored_update)
                session.commit()

    def read_interests(self, user_context: UserContext) -> Interests:
        self.ensure_data_store()
        with Session(self.engine) as session:
            stored_interests = session.exec(
                select(StoredInterest)
                .where(StoredInterest.user_id == user_context.user_id)
                .options(
                    selectinload(cast(Any, StoredInterest.sources)).selectinload(
                        cast(Any, StoredInterestSource.ignore_keywords)
                    )
                )
            ).all()
            return Interests(
                interests=[
                    self._interest_from_stored(stored_interest)
                    for stored_interest in sorted(stored_interests, key=lambda interest: interest.name)
                ]
            )

    def write_interests(self, user_context: UserContext, interests: Interests) -> None:
        self.ensure_data_store()
        with Session(self.engine) as session:
            self._write_interests(session, user_context, interests)
            session.commit()

    def _ensure_fixed_collections(self, session: Session, user_context: UserContext) -> None:
        existing_collection_ids = {
            collection.collection_id
            for collection in session.exec(
                select(StoredCollection).where(StoredCollection.user_id == user_context.user_id)
            ).all()
        }
        for collection_id in FIXED_COLLECTIONS:
            if collection_id not in existing_collection_ids:
                session.add(
                    StoredCollection(
                        user_id=user_context.user_id,
                        collection_id=collection_id,
                        name=collection_name(collection_id),
                    )
                )

    def _write_interests(self, session: Session, user_context: UserContext, interests: Interests) -> None:
        stored_interests = self._stored_interests_from_domain(user_context, interests.interests)
        for stored_interest in session.exec(
            select(StoredInterest).where(StoredInterest.user_id == user_context.user_id)
        ).all():
            session.delete(stored_interest)
        session.flush()
        session.add_all(stored_interests)

    def _stored_interests_from_domain(
        self,
        user_context: UserContext,
        interests: list[Interest],
    ) -> list[StoredInterest]:
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
            stored_interests.append(
                self._stored_interest_from_domain(user_context, interest, interest_id, stored_sources)
            )
        return stored_interests

    def _stored_interest_from_domain(
        self,
        user_context: UserContext,
        interest: Interest,
        interest_id: str,
        stored_sources: list[StoredInterestSource],
    ) -> StoredInterest:
        return StoredInterest(
            user_id=user_context.user_id,
            interest_id=interest_id,
            name=interest.name,
            description=interest.description,
            priority=interest.priority,
            enabled=interest.enabled,
            deleted_at=self._datetime_from_domain(interest.deleted_at),
            sources=stored_sources,
        )

    def _stored_source_from_domain(
        self,
        source: InterestSource,
        source_id: str,
    ) -> StoredInterestSource:
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

    def _collection_from_stored(self, stored_collection: StoredCollection) -> UpdateCollection:
        collection_id = cast(CollectionId, stored_collection.collection_id)
        return UpdateCollection(
            id=collection_id,
            name=stored_collection.name,
            saved_updates=[
                self._saved_update_from_stored(stored_update)
                for stored_update in sorted(
                    stored_collection.saved_updates,
                    key=lambda saved_update: saved_update.saved_at,
                    reverse=True,
                )
            ],
        )

    def _stored_saved_update(
        self,
        session: Session,
        user_context: UserContext,
        collection_id: CollectionId,
        update_key: str,
    ) -> StoredSavedCollectionUpdate | None:
        return session.exec(
            select(StoredSavedCollectionUpdate).where(
                StoredSavedCollectionUpdate.collection_id == collection_id,
                StoredSavedCollectionUpdate.user_id == user_context.user_id,
                StoredSavedCollectionUpdate.update_key == update_key,
            )
        ).first()

    def _raise_on_missing_collection(
        self,
        session: Session,
        user_context: UserContext,
        collection_id: CollectionId,
    ) -> None:
        stored_collection = session.get(StoredCollection, (user_context.user_id, collection_id))
        if stored_collection is None:
            raise CollectionNotFoundError(f"Collection not found: {collection_id}")

    def _stored_saved_update_from_domain(
        self,
        user_context: UserContext,
        collection_id: CollectionId,
        update_key: str,
        update: SavedUpdateSnapshot,
        saved_at: datetime,
    ) -> StoredSavedCollectionUpdate:
        return StoredSavedCollectionUpdate(
            user_id=user_context.user_id,
            collection_id=collection_id,
            update_key=update_key,
            saved_at=self._datetime_from_datetime(saved_at),
            title=update.title,
            url=update.url or "",
            summary=update.summary,
            image_url=update.image_url,
            published=self._datetime_from_datetime(update.published),
            published_at=self._datetime_from_datetime(update.published_at),
            interest_id=update.source_interest.interest_id,
            interest_name=update.source_interest.interest_name,
            source_id=update.source_interest.source_id,
            source_label=update.source_interest.source_label,
            source_image_url=update.source_interest.source_image_url,
            source_url=update.source_interest.source_url,
            source_type=update.source_interest.source_type,
        )

    def _saved_update_from_stored(self, stored_update: StoredSavedCollectionUpdate) -> SavedCollectionUpdate:
        return SavedCollectionUpdate(
            update_key=stored_update.update_key,
            saved_at=self._required_datetime_to_datetime(stored_update.saved_at),
            update=SavedUpdateSnapshot(
                title=stored_update.title,
                url=stored_update.url,
                summary=stored_update.summary,
                image_url=stored_update.image_url,
                published=self._datetime_to_datetime(stored_update.published),
                published_at=self._datetime_to_datetime(stored_update.published_at),
                source_interest=SourceInterest(
                    interest_id=stored_update.interest_id,
                    interest_name=stored_update.interest_name,
                    source_id=stored_update.source_id,
                    source_label=stored_update.source_label,
                    source_image_url=stored_update.source_image_url,
                    source_url=stored_update.source_url,
                    source_type=cast(SourceType, stored_update.source_type),
                ),
            ),
        )

    def _interest_id_or_raise(self, interest: Interest) -> str:
        if interest.id is None:
            return self._generated_id("interest")
        return interest.id

    def _source_id_or_raise(self, source: InterestSource) -> str:
        if source.id is None:
            return self._generated_id("source")
        return source.id

    def _generated_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex}"

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

    def _datetime_from_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Saved update timestamp must include timezone information")
        return value

    def _datetime_to_datetime(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _required_datetime_to_datetime(self, value: datetime) -> datetime:
        return self._datetime_to_datetime(value) or value


def _database_url_for_sqlalchemy(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def create_interest_store(database_url: str) -> InterestStore:
    return InterestStore(create_engine(_database_url_for_sqlalchemy(database_url), pool_pre_ping=True))


DEFAULT_STORE = create_interest_store(DATABASE_URL)
