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
"""Unit tests for the objects handler class"""

from contextlib import nullcontext
from unittest.mock import AsyncMock

import pytest
from hexkit.protocols.objstorage import ObjectStorageProtocol
from hexkit.providers.s3 import S3ObjectStorage

from sms.core.objects_handler import ObjectsHandler
from tests.fixtures.config import DEFAULT_TEST_CONFIG

pytestmark = pytest.mark.asyncio()


def check_id_validity(id_: str):
    """Mock version of the bucket/object ID validation functions.

    Just employs a simple length check.
    Returns True if it is valid, False if invalid.
    """
    return not (len(id_) < 3 or len(id_) > 63)


def validate_bucket_id(bucket_id: str):
    """Mock version of the bucket ID validation function"""
    if not check_id_validity(bucket_id):
        raise ObjectStorageProtocol.BucketIdValidationError(bucket_id, reason=None)


def validate_object_id(object_id: str):
    """Mock version of the object ID validation function"""
    if not check_id_validity(object_id):
        raise ObjectStorageProtocol.ObjectIdValidationError(object_id, reason=None)


def get_storage_mock():
    """Initialize a mock object storage instance with a bucket and an object."""
    mock = AsyncMock(spec=S3ObjectStorage)
    mock.buckets = {"bucket": ["object1"]}

    async def does_object_exist(bucket_id: str, object_id: str):
        validate_bucket_id(bucket_id)
        validate_object_id(object_id)
        return object_id in mock.buckets.get(bucket_id, [])

    async def delete_object(bucket_id: str, object_id: str):
        validate_bucket_id(bucket_id)
        validate_object_id(object_id)

        try:
            bucket = mock.buckets[bucket_id]
        except KeyError as err:
            raise ObjectStorageProtocol.BucketNotFoundError(bucket_id) from err

        object_index = bucket.index(object_id)
        del bucket[object_index]

    async def list_all_object_ids(bucket_id: str):
        validate_bucket_id(bucket_id)
        try:
            return mock.buckets[bucket_id]
        except KeyError as err:
            raise ObjectStorageProtocol.BucketNotFoundError(bucket_id) from err

    mock.does_object_exist.side_effect = does_object_exist
    mock.delete_object.side_effect = delete_object
    mock.list_all_object_ids.side_effect = list_all_object_ids
    return mock


@pytest.mark.parametrize(
    "bucket_id, object_id, expected_result",
    [
        ("bucket", "object1", True),
        ("bucket", "non_existent_object", False),
        ("non_existent_bucket", "object1", False),
        ("a", "object1", False),
        ("bucket", "a", False),
    ],
    ids=[
        "happy_path",
        "nonexistent_object",
        "nonexistent_bucket",
        "invalid_bucket",
        "invalid_object",
    ],
)
async def test_does_object_exist(
    bucket_id: str,
    object_id: str,
    expected_result: bool,
):
    """Test for seeing if object exists.

    Errors should only be raised for invalid bucket/object IDs. If the bucket does not
    exist, the result should be False.
    """
    storage = get_storage_mock()
    objects_handler = ObjectsHandler(config=DEFAULT_TEST_CONFIG, object_storage=storage)

    error: type[Exception] | None = None
    if not check_id_validity(bucket_id):
        error = objects_handler.InvalidBucketIdError
    elif not check_id_validity(object_id):
        error = objects_handler.InvalidObjectIdError
    with pytest.raises(error) if error else nullcontext():
        result = await objects_handler.does_object_exist(bucket_id, object_id)
        assert result == expected_result


async def test_empty_bucket():
    """Test emptying a bucket.

    Test for happy path, invalid bucket ID, non-existent bucket, and empty bucket.
    """
    storage = get_storage_mock()
    objects_handler = ObjectsHandler(config=DEFAULT_TEST_CONFIG, object_storage=storage)

    # happy path
    await objects_handler.empty_bucket("bucket")
    assert storage.buckets["bucket"] == []

    # nonexistent bucket
    with pytest.raises(objects_handler.BucketNotFoundError):
        await objects_handler.empty_bucket("non_existent_bucket")

    # invalid bucket name
    with pytest.raises(objects_handler.InvalidBucketIdError):
        await objects_handler.empty_bucket("a")

    # already empty bucket
    await objects_handler.empty_bucket("bucket")
    assert storage.buckets["bucket"] == []


async def test_list_objects():
    """Test listing objects in a bucket.

    Test for happy path, invalid bucket ID, non-existent bucket, and empty bucket.
    """
    storage = get_storage_mock()
    objects_handler = ObjectsHandler(config=DEFAULT_TEST_CONFIG, object_storage=storage)

    # Happy path
    result = await objects_handler.list_objects("bucket")
    assert result == ["object1"]

    # Nonexistent bucket
    with pytest.raises(objects_handler.BucketNotFoundError):
        await objects_handler.list_objects("non_existent_bucket")

    # Invalid bucket name
    with pytest.raises(objects_handler.InvalidBucketIdError):
        await objects_handler.list_objects("a")

    # Empty bucket
    storage.buckets["bucket"] = []
    result = await objects_handler.list_objects("bucket")
