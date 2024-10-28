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

"""FastAPI routes for HashiCorp Vault state management."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from sms.adapters.inbound.fastapi_ import dummies
from sms.adapters.inbound.fastapi_.http_authorization import (
    TokenAuthContext,
    require_token,
)

secrets_router = APIRouter()


@secrets_router.get(
    "/",
    operation_id="get_secrets",
    summary="Returns a list of secrets in the vault",
    status_code=status.HTTP_200_OK,
    response_model=list[str],
)
async def get_secrets(
    secrets_handler: dummies.SecretsHandlerPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Returns a list of secrets in the vault"""
    try:
        return secrets_handler.get_secrets()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@secrets_router.delete(
    "/",
    operation_id="delete_secrets",
    summary="Delete one or more secrets from the vault",
    description=(
        "If secrets_to_delete is omitted, all secrets are deleted. If"
        + " `secrets_to_delete` is provided, only the secrets with the matching IDs are"
        + " deleted. If a provided secret does not exist, it is ignored."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_secrets(
    secrets_handler: dummies.SecretsHandlerPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
    secrets_to_delete: list[str] | None = Query(
        default=None,
        description="List of secrets to delete.",
    ),
):
    """Delete one or more secrets from the vault"""
    try:
        secrets_handler.delete_secrets(secrets=secrets_to_delete)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
