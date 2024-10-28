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
"""Unit tests for the Vault part of the SMS REST API."""

from typing import Any

import pytest

from tests.fixtures.config import DEFAULT_TEST_CONFIG
from tests.fixtures.dummies import DummySecretsHandler
from tests.fixtures.utils import VALID_BEARER_TOKEN, get_rest_client_with_mocks

pytestmark = pytest.mark.asyncio()

TEST_URL = "/secrets/"
HEADERS: dict[str, Any] = {"Authorization": VALID_BEARER_TOKEN}


@pytest.mark.parametrize(
    "secrets",
    [
        [],
        ["secret1"],
        ["secret1", "secret2"],
    ],
    ids=[
        "EmptyVault",
        "OneSecret",
        "TwoSecrets",
    ],
)
async def test_get_secrets(secrets: list[str]):
    """Test the GET secrets endpoint without errors."""
    secrets_handler = DummySecretsHandler(secrets=secrets)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        response = await client.get(TEST_URL, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == secrets


async def test_get_secrets_error():
    """Test the GET secrets endpoint with an error."""
    secrets_handler = DummySecretsHandler(fail_on_get_secrets=True)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        response = await client.get(TEST_URL, headers=HEADERS)

    assert response.status_code == 500


@pytest.mark.parametrize(
    "secrets_to_delete",
    [None, [], ["secret1"], ["secret1", "secret2"]],
    ids=[
        "DeleteArgNotProvided",
        "DeleteEmptyList",
        "DeleteSecret1",
        "DeleteSecret1AndSecret2",
    ],
)
@pytest.mark.parametrize(
    "stored_secrets",
    [
        [],
        ["secret1", "secret2", "secret3"],
    ],
    ids=["VaultIsEmpty", "VaultHasThreeSecrets"],
)
async def test_delete_secrets(
    stored_secrets: list[str], secrets_to_delete: list[str] | None
):
    """Test the DELETE secrets endpoint without errors."""
    secrets_handler = DummySecretsHandler(secrets=stored_secrets)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        if secrets_to_delete is None:
            response = await client.delete(TEST_URL, headers=HEADERS)
        else:
            response = await client.delete(
                TEST_URL,
                headers=HEADERS,
                params={"secrets_to_delete": secrets_to_delete},
            )

    assert response.status_code == 204

    expected_remaining_secrets = (
        [s for s in stored_secrets if s not in secrets_to_delete]
        if secrets_to_delete
        else []
    )

    assert secrets_handler.secrets == expected_remaining_secrets, secrets_handler.recent


async def test_delete_secrets_error():
    """Test the DELETE secrets endpoint with an error.

    This is triggered by setting the `fail_on_get_secrets` flag to True and
    not providing any secrets to delete.
    """
    secrets_handler = DummySecretsHandler(fail_on_get_secrets=True)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        response = await client.delete(TEST_URL, headers=HEADERS)

    assert response.status_code == 500
