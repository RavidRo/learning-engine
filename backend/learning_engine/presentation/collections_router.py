"""FastAPI routes for update collections."""

from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status

from learning_engine.application.auth import UserContext
from learning_engine.application.collections import (
    list_collections,
    remove_update_from_collection,
    save_update_to_collection,
)
from learning_engine.domain.collections import CollectionNotFoundError, Collections
from learning_engine.presentation.auth import user_context_dependency
from learning_engine.presentation.schemas import (
    RemoveCollectionUpdateResponse,
    SaveCollectionUpdateRequest,
    SaveCollectionUpdateResponse,
)
from learning_engine.presentation.state import get_app_state


def collections_router(api: FastAPI) -> APIRouter:
    router = APIRouter(prefix="/api/collections")
    require_user_context = user_context_dependency(api)
    current_user_context = Annotated[UserContext, Depends(require_user_context)]

    @router.get("", response_model=Collections)
    def get_collections(user_context: current_user_context) -> Collections:
        return list_collections(get_app_state(api).collection_repository, user_context)

    @router.post("/{collection_id}/updates", response_model=SaveCollectionUpdateResponse)
    def save_collection_update(
        collection_id: str,
        payload: SaveCollectionUpdateRequest,
        user_context: current_user_context,
    ) -> SaveCollectionUpdateResponse:
        try:
            saved_update = save_update_to_collection(
                get_app_state(api).collection_repository,
                user_context,
                collection_id,
                payload,
            )
        except CollectionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return SaveCollectionUpdateResponse(saved_update=saved_update)

    @router.delete(
        "/{collection_id}/updates/{update_key}",
        response_model=RemoveCollectionUpdateResponse,
    )
    def remove_collection_update(
        collection_id: str,
        update_key: str,
        user_context: current_user_context,
    ) -> RemoveCollectionUpdateResponse:
        try:
            remove_update_from_collection(
                get_app_state(api).collection_repository,
                user_context,
                collection_id,
                update_key,
            )
        except CollectionNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        return RemoveCollectionUpdateResponse(ok=True)

    return router
