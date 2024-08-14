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
"""Dummy and convenience classes for testing."""

from dataclasses import dataclass

from sms.models import Criteria, UpsertionDetails
from sms.ports.inbound.docs_handler import DocsHandlerPort
from sms.ports.inbound.objects_handler import ObjectsHandlerPort


@dataclass
class DocsApiCallArgs:
    """Encapsulates all the params used in a /documents/ API call of any kind."""

    method: str
    db_name: str
    collection: str
    criteria: Criteria | None = None
    upsertion_details: UpsertionDetails | None = None


class DummyDocsHandler(DocsHandlerPort):
    """Dummy DocsHandler implementation for unit testing."""

    calls: list[DocsApiCallArgs]

    def __init__(self):
        self.calls = []

    async def get(self, db_name: str, collection: str, criteria: Criteria):
        """Dummy get implementation. It records the call and returns an empty list.

        Optionally, it raises a PermissionError if the collection is named "permission_error".
        """
        call = DocsApiCallArgs(
            method="get", db_name=db_name, collection=collection, criteria=criteria
        )
        self.calls.append(call)
        if collection == "permission_error":
            raise PermissionError()
        return [{}]

    async def upsert(
        self,
        db_name: str,
        collection: str,
        upsertion_details: UpsertionDetails,
    ):
        """Dummy upsert implementation. It records the call.

        Optionally, it raises a PermissionError if the collection is named "permission_error".
        """
        call = DocsApiCallArgs(
            method="put",
            db_name=db_name,
            collection=collection,
            upsertion_details=upsertion_details,
        )
        self.calls.append(call)
        if collection == "permission_error":
            raise PermissionError()

    async def delete(self, db_name: str, collection: str, criteria: Criteria):
        """Dummy delete implementation. It records the call.

        Optionally, it raises a PermissionError if the collection is named "permission_error".
        """
        call = DocsApiCallArgs(
            method="delete", db_name=db_name, collection=collection, criteria=criteria
        )
        self.calls.append(call)
        if collection == "permission_error":
            raise PermissionError()
        if db_name == "*" and collection != "*":
            raise ValueError("Cannot use wildcard for db_name with specific collection")


def check_id_validity(id_: str) -> bool:
    """Check if an ID is valid."""
    return id_ != "invalid"


class DummyObjectsHandler(ObjectsHandlerPort):
    """Dummy ObjectsHandler implementation for unit testing."""

    buckets: dict[str, list[str]]  # bucket_id -> object_ids

    def __init__(self, buckets: dict[str, list[str]] | None = None):
        self.buckets = buckets if buckets else {}

    def _validate_bucket_id(self, bucket_id: str) -> None:
        """Check if a bucket ID is valid."""
        if not check_id_validity(bucket_id):
            raise self.InvalidBucketIdError(bucket_id=bucket_id)

    def _validate_object_id(self, object_id: str) -> None:
        """Check if an object ID is valid."""
        if not check_id_validity(object_id):
            raise self.InvalidObjectIdError(object_id=object_id)

    async def does_object_exist(self, bucket_id: str, object_id: str) -> bool:
        """Check if an object exists in the specified bucket.

        Returns a bool indicating whether or not the object exists in the given bucket.

        Raises:
        - `InvalidBucketIdError`: If the bucket ID is literally "invalid".
        - `InvalidObjectIdError`: If the object ID is literally "invalid".
        """
        self._validate_bucket_id(bucket_id)
        self._validate_object_id(object_id)
        return object_id in self.buckets.get(bucket_id, [])

    async def empty_bucket(self, bucket_id: str) -> None:
        """Delete all objects in the specified bucket.

        Raises `BucketNotFoundError` if the bucket does not exist.
        """
        self._validate_bucket_id(bucket_id)
        try:
            self.buckets[bucket_id].clear()
        except KeyError as err:
            raise self.BucketNotFoundError(bucket_id=bucket_id) from err

    async def list_objects(self, bucket_id: str) -> list[str]:
        """List all objects in the specified bucket.

        Raises:
        - `BucketNotFoundError`: If the bucket does not exist.
        - `InvalidBucketIdError`: If the bucket ID is literally "invalid".
        """
        self._validate_bucket_id(bucket_id)
        try:
            return self.buckets[bucket_id]
        except KeyError as err:
            raise self.BucketNotFoundError(bucket_id=bucket_id) from err
