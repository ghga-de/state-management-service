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
"""FastAPI routes for S3 state management."""

from typing import Annotated

from fastapi import APIRouter, HTTPException

from sms.adapters.inbound.fastapi_ import dummies
from sms.adapters.inbound.fastapi_.http_authorization import (
    TokenAuthContext,
    require_token,
)
from sms.ports.inbound.objects_handler import ObjectsHandlerPort

s3_router = APIRouter()


@s3_router.get(
    "/{bucket_id}/{object_id}",
    operation_id="check_objects_exists",
    summary="See if an object exists in the specified bucket.",
    status_code=200,
    response_model=bool,
)
async def does_object_exist(
    bucket_id: str,
    object_id: str,
    objects_handler: dummies.ObjectsHandlerPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Return a list of the objects currently existing in the S3 object storage."""
    try:
        return await objects_handler.does_object_exist(
            bucket_id=bucket_id, object_id=object_id
        )
    except ObjectsHandlerPort.InvalidIdError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except ObjectsHandlerPort.OperationError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@s3_router.get(
    "/{bucket_id}",
    operation_id="get_objects",
    summary="List all objects in the specified bucket.",
    status_code=200,
    response_model=list[str],
)
async def list_objects(
    bucket_id: str,
    objects_handler: dummies.ObjectsHandlerPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Return a list of the objects currently existing in the S3 object storage."""
    try:
        return await objects_handler.list_objects(bucket_id=bucket_id)
    except ObjectsHandlerPort.BucketNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ObjectsHandlerPort.InvalidBucketIdError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except ObjectsHandlerPort.OperationError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err


@s3_router.delete(
    "/{bucket_id}",
    operation_id="empty_bucket",
    summary="Delete all objects in the specified bucket.",
    status_code=204,
)
async def delete_objects(
    bucket_id: str,
    objects_handler: dummies.ObjectsHandlerPortDummy,
    _token: Annotated[TokenAuthContext, require_token],
):
    """Delete all objects in the specified bucket."""
    try:
        await objects_handler.empty_bucket(bucket_id=bucket_id)
    except ObjectsHandlerPort.InvalidBucketIdError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except ObjectsHandlerPort.BucketNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
    except ObjectsHandlerPort.OperationError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err