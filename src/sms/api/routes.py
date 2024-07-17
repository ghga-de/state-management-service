# Copyright 2021 - 2024 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""FastAPI routes."""

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Request, status
from fastapi.exceptions import HTTPException

from sms.api import dummies
from sms.api.http_authorization import TokenAuthContext, require_token

router = APIRouter()


# TODO: Remove config dummy if it's not needed
# TODO: See about adding an endpoint to get the accessible collections
@router.get(
    "/health",
    summary="health",
    tags=["StateManagementService", "sms-"],
    status_code=200,
)
async def health():
    """Used to test if this service is alive"""
    return {"status": "OK"}


@router.get(
    "/docs/{db_name}/{collection}",
    tags=["StateManagementService", "sms-mongodb"],
    summary="Returns all or some documents from the specified collection.",
    status_code=status.HTTP_200_OK,
)
async def get_docs(
    db_name: str,
    collection: str,
    request: Request,
    docs_dao: dummies.DocsDaoPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
) -> list[Mapping[str, Any]]:
    """Returns all or some documents from the specified collection."""
    query_params: Mapping[str, str] = dict(request.query_params)

    try:
        results = await docs_dao.get(
            db_name=db_name,
            collection=collection,
            criteria=query_params,
        )
        return results
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err


@router.put(
    "/docs/{db_name}/{collection}",
    tags=["StateManagementService", "sms-mongodb"],
    summary=(
        "Upserts the document(s) provided in the request body in the"
        + "specified collection."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
async def upsert_docs(
    db_name: str,
    collection: str,
    documents: Mapping[str, Any] | list[Mapping[str, Any]],
    docs_dao: dummies.DocsDaoPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Upserts the document(s) provided in the request body in the specified collection."""
    try:
        await docs_dao.upsert(
            db_name=db_name,
            collection=collection,
            documents=documents,
        )
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err


@router.delete(
    "/docs/{db_name}/{collection}",
    tags=["StateManagementService", "sms-mongodb"],
    summary="Deletes all or some documents in the collection.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_docs(
    db_name: str,
    collection: str,
    request: Request,
    docs_dao: dummies.DocsDaoPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Upserts the document(s) provided in the request body in the specified collection."""
    query_params: Mapping[str, str] = dict(request.query_params)

    try:
        await docs_dao.delete(
            db_name=db_name,
            collection=collection,
            criteria=query_params,
        )
    except PermissionError as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(err),
        ) from err
