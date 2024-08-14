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

"""Test the objects-related REST API endpoints' behavior."""

from unittest.mock import AsyncMock

import pytest
from hexkit.custom_types import JsonObject

from tests.fixtures.config import DEFAULT_TEST_CONFIG
from tests.fixtures.dummies import DummyObjectsHandler
from tests.fixtures.utils import VALID_BEARER_TOKEN, get_rest_client

pytestmark = pytest.mark.asyncio()

TEST_URL = "/objects"
INVALID_BUCKET_RESPONSE = {"detail": "Bucket ID 'invalid' is invalid."}
INVALID_OBJECT_RESPONSE = {"detail": "Object ID 'invalid' is invalid."}


@pytest.mark.parametrize(
    "bucket_id, object_id, expected_result",
    [
        ("bucket", "object1", True),
        ("bucket", "non_existent_object", False),
        ("non_existent_bucket", "object1", False),
        ("invalid", "object1", INVALID_BUCKET_RESPONSE),
        ("bucket", "invalid", INVALID_OBJECT_RESPONSE),
    ],
    ids=[
        "happy_path",
        "nonexistent_object",
        "nonexistent_bucket",
        "invalid_bucket",
        "invalid_object",
    ],
)
async def test_does_object_exist(bucket_id: str, object_id: str, expected_result: bool):
    """Test the `does_object_exist` method.

    Check for:
    - Happy path (object exists)
    - Bucket exists, object does not
    - Bucket does not exist
    - Invalid bucket ID
    - Invalid object ID
    """
    mock_docs_handler = AsyncMock()  # don't declare spec (to keep imports cleaner)

    dummy_objects_handler = DummyObjectsHandler(buckets={"bucket": ["object1"]})
    async with get_rest_client(
        config=DEFAULT_TEST_CONFIG,
        docs_handler_override=mock_docs_handler,
        objects_handler_override=dummy_objects_handler,
    ) as client:
        response = await client.get(
            f"{TEST_URL}/{bucket_id}/{object_id}",
            headers={"Authorization": VALID_BEARER_TOKEN},
        )

        assert response.json() == expected_result
        assert (
            response.status_code == 422
            if (bucket_id == "invalid" or object_id == "invalid")
            else 200
        )


@pytest.mark.parametrize(
    "bucket_id, expected_result, status_code",
    [
        ("bucket", ["object1"], 200),
        ("empty_bucket", [], 200),
        (
            "non_existent_bucket",
            {"detail": "Bucket with ID 'non_existent_bucket' does not exist."},
            404,
        ),
        ("invalid", INVALID_BUCKET_RESPONSE, 422),
    ],
    ids=["HappyPath", "EmptyBucket", "NonExistentBucket", "InvalidBucket"],
)
async def test_list_objects(
    bucket_id: str, expected_result: JsonObject, status_code: int
):
    """Test the /objects/{bucket_id} endpoint (list_objects).

    Check for:
    - Happy path (bucket exists, has objects)
    - Bucket exists, no objects
    - Bucket does not exist
    - Invalid bucket ID
    """
    mock_docs_handler = AsyncMock()
    dummy_objects_handler = DummyObjectsHandler(
        buckets={"bucket": ["object1"], "empty_bucket": []}
    )
    async with get_rest_client(
        config=DEFAULT_TEST_CONFIG,
        docs_handler_override=mock_docs_handler,
        objects_handler_override=dummy_objects_handler,
    ) as client:
        response = await client.get(
            f"{TEST_URL}/{bucket_id}",
            headers={"Authorization": VALID_BEARER_TOKEN},
        )

        assert response.status_code == status_code
        assert response.json() == expected_result


# TODO: test_delete_objects
