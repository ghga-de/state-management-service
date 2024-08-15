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
"""Integration tests for the /objects endpoints."""

import pytest
from hexkit.providers.s3.testutils import S3Fixture, temp_file_object

from tests.fixtures.config import get_config
from tests.fixtures.utils import VALID_BEARER_TOKEN, get_rest_client

pytestmark = pytest.mark.asyncio()


def bucket_not_found_json(bucket_id: str) -> dict[str, str]:
    """Return the JSON response for a bucket not found error."""
    return {"detail": f"Bucket with ID '{bucket_id}' does not exist."}


def invalid_bucket_json(bucket_id: str) -> dict[str, str]:
    """Return the JSON response for an invalid bucket ID error."""
    return {"detail": f"Bucket ID '{bucket_id}' is invalid."}


def invalid_object_json(object_id: str) -> dict[str, str]:
    """Return the JSON response for an invalid object ID error."""
    return {"detail": f"Object ID '{object_id}' is invalid."}


async def populate_items(s3: S3Fixture, buckets: dict[str, list[str]]):
    """Convenience function to populate the S3 storage with buckets and objects."""
    # Populate the buckets so even empty buckets are established
    await s3.populate_buckets([_ for _ in buckets])
    for bucket, objects in buckets.items():
        for object in objects:
            with temp_file_object(bucket, object, 1) as file:
                await s3.populate_file_objects([file])


@pytest.mark.parametrize(
    "bucket_id, object_id",
    [
        ("bucket1", "object1"),
        ("a", "object1"),
        ("bucket1", "a"),
    ],
    ids=["Valid", "InvalidBucket", "InvalidObject"],
)
@pytest.mark.parametrize(
    "buckets",
    [
        {"bucket1": []},
        {"bucket1": ["object1", "object2"]},
        {},
        {"another-bucket": ["object1", "object2"]},
    ],
    ids=[
        "BucketExistsNoObjects",
        "BucketAndObjectExist",
        "NothingExists",
        "OnlyObjectExists",
    ],
)
async def test_does_object_exist(
    s3: S3Fixture,
    bucket_id: str,
    object_id: str,
    buckets: dict[str, list[str]],
):
    """Test the /objects/{bucket_id}/{object_id} endpoint."""
    config = get_config([s3.config])

    await populate_items(s3, buckets)

    async with get_rest_client(config=config) as client:
        response = await client.get(
            f"/objects/{bucket_id}/{object_id}",
            headers={"Authorization": VALID_BEARER_TOKEN},
        )

        # Check for errors in order that they would be caught, ending with happy path.
        if bucket_id == "a":
            assert response.status_code == 422
            assert response.json() == invalid_bucket_json(bucket_id)
        elif bucket_id not in buckets:
            assert response.status_code == 404
            assert response.json() == bucket_not_found_json(bucket_id)
        elif object_id == "a":
            assert response.status_code == 422
            assert response.json() == invalid_object_json(object_id)
        else:
            assert response.status_code == 200
            assert response.json() == (object_id in buckets.get(bucket_id, []))


async def test_list_objects(s3: S3Fixture):
    """Test the GET /objects/{bucket_id} endpoint."""
    config = get_config([s3.config])

    buckets = {
        "bucket1": ["object1", "object2"],
        "empty": [],
    }

    statuses = [
        ("bucket1", 200),
        ("empty", 200),
        ("does-not-exist", 404),
        ("a", 422),
    ]

    await populate_items(s3, buckets)

    async with get_rest_client(config=config) as client:
        for bucket_id, expected_status in statuses:
            response = await client.get(
                f"/objects/{bucket_id}",
                headers={"Authorization": VALID_BEARER_TOKEN},
            )

            assert response.status_code == expected_status
            if expected_status == 200:
                assert response.json() == buckets.get(bucket_id, [])
            elif expected_status == 404:
                assert response.json() == bucket_not_found_json(bucket_id)
            elif expected_status == 422:
                assert response.json() == invalid_bucket_json(bucket_id)


async def test_delete_objects(s3: S3Fixture):
    """Test the DELETE /objects/{bucket_id} endpoint."""
    config = get_config([s3.config])

    buckets = {
        "bucket1": ["object1", "object2"],
        "empty": [],
    }

    statuses = [
        ("bucket1", 204),
        ("empty", 204),
        ("does-not-exist", 204),
        ("a", 422),
    ]

    await populate_items(s3, buckets)

    async with get_rest_client(config=config) as client:
        for bucket_id, expected_status in statuses:
            response = await client.delete(
                f"/objects/{bucket_id}",
                headers={"Authorization": VALID_BEARER_TOKEN},
            )

            assert response.status_code == expected_status
            if expected_status == 422:
                assert response.json() == invalid_bucket_json(bucket_id)

        for bucket_id in ["bucket1", "empty"]:
            response = await client.get(
                f"/objects/{bucket_id}",
                headers={"Authorization": VALID_BEARER_TOKEN},
            )
            assert response.status_code == 200
            assert response.json() == []
