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
from tests.fixtures.vault import DEFAULT_VAULT_PATH

pytestmark = pytest.mark.asyncio()

TEST_URL = f"/secrets/{DEFAULT_VAULT_PATH}"
HEADERS: dict[str, Any] = {"Authorization": VALID_BEARER_TOKEN}


@pytest.mark.parametrize(
    "stored_secrets",
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
async def test_get_secrets(stored_secrets: list[str]):
    """Test the GET secrets endpoint without errors."""
    vault_path_and_secrets = {DEFAULT_VAULT_PATH: stored_secrets}
    secrets_handler = DummySecretsHandler(secrets=vault_path_and_secrets)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        response = await client.get(TEST_URL, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == stored_secrets


@pytest.mark.parametrize(
    "stored_secrets",
    [
        [],
        ["secret1", "secret2", "secret3"],
    ],
    ids=["VaultIsEmpty", "VaultHasThreeSecrets"],
)
async def test_delete_secrets(stored_secrets: list[str]):
    """Test the DELETE secrets endpoint without errors."""
    vault_path_and_secrets = {DEFAULT_VAULT_PATH: stored_secrets}
    secrets_handler = DummySecretsHandler(secrets=vault_path_and_secrets)
    async with get_rest_client_with_mocks(
        config=DEFAULT_TEST_CONFIG, secrets_handler_override=secrets_handler
    ) as client:
        response = await client.delete(TEST_URL, headers=HEADERS)

    assert response.status_code == 204
    assert secrets_handler.secrets.get(DEFAULT_VAULT_PATH, []) == []
