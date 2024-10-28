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

"""Unit tests for the SecretsHandler class"""

from unittest.mock import Mock, call

import pytest
from hvac.exceptions import InvalidPath

from sms.core.secrets_handler import SecretsHandler
from tests.fixtures.config import DEFAULT_TEST_CONFIG


@pytest.mark.parametrize(
    "secrets",
    [[], ["key1"], ["key1", "key2"]],
    ids=["empty", "single", "multiple"],
)
def test_get_secrets(monkeypatch: pytest.MonkeyPatch, secrets: list[str]):
    """Test get_secrets method without errors"""
    # patch the hvac client with a mock
    mock_client = Mock()
    mock_client.secrets.kv.v2.list_secrets.return_value = {"data": {"keys": secrets}}
    monkeypatch.setattr(SecretsHandler, "client", mock_client)
    secrets_handler = SecretsHandler(config=DEFAULT_TEST_CONFIG)

    assert secrets_handler.get_secrets() == secrets
    mock_client.secrets.kv.v2.list_secrets.assert_called_once()


def test_get_secrets_error(monkeypatch: pytest.MonkeyPatch, caplog):
    """Test get_secrets method with an error"""
    # patch the hvac client with a mock
    mock_client = Mock()
    mock_client.secrets.kv.v2.list_secrets.side_effect = InvalidPath("Invalid path")
    monkeypatch.setattr(SecretsHandler, "client", mock_client)
    secrets_handler = SecretsHandler(config=DEFAULT_TEST_CONFIG)

    # Make sure the error is logged as a warning but an empty list is still returned
    caplog.clear()
    secrets = secrets_handler.get_secrets()
    assert len(caplog.messages) == 1
    assert caplog.messages[0] == (
        "Invalid path error when fetching secrets. The path might be invalid,"
        + " or no secrets may exist."
    )
    assert caplog.records[0].levelname == "WARNING"
    assert secrets == []
    mock_client.secrets.kv.v2.list_secrets.assert_called_once()


def test_delete_secrets_error(monkeypatch: pytest.MonkeyPatch):
    """Test delete_secrets method on empty vault and without specifying secrets."""
    # patch the hvac client with a mock
    mock_client = Mock()
    mock_client.secrets.kv.v2.list_secrets.side_effect = InvalidPath("Invalid path")
    monkeypatch.setattr(SecretsHandler, "client", mock_client)
    secrets_handler = SecretsHandler(config=DEFAULT_TEST_CONFIG)

    # Call delete_secrets() without specifying secrets in order to trigger get_secrets
    secrets_handler.delete_secrets()
    mock_client.secrets.kv.v2.list_secrets.assert_called_once()
    mock_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_not_called()


@pytest.mark.parametrize(
    "secrets_to_delete",
    [
        None,
        [],
        ["key1"],
        ["key2"],
        ["key1", "key2"],
    ],
    ids=[
        "None",
        "Empty",
        "DeleteKey1",
        "DeleteKey2",
        "DeleteBoth",
    ],
)
@pytest.mark.parametrize(
    "stored_secrets",
    [[], ["key1"], ["key1", "key2"]],
    ids=["Empty", "OneSecret", "TwoSecrets"],
)
def test_delete_successful(
    monkeypatch: pytest.MonkeyPatch,
    secrets_to_delete: list[str] | None,
    stored_secrets: list[str],
):
    """Test delete_secrets method.

    Use a variety of combinations of stored secrets and secrets to delete.
    """
    # create a mock for the hvac client
    list_stored_secrets = {"data": {"keys": stored_secrets}}
    mock_client = Mock()

    # list_secrets either returns all keys or raises an InvalidPath error
    if stored_secrets:
        mock_client.secrets.kv.v2.list_secrets.return_value = list_stored_secrets
    else:
        mock_client.secrets.kv.v2.list_secrets.side_effect = InvalidPath("Invalid path")

    # apply the mock to the SecretsHandler
    monkeypatch.setattr(SecretsHandler, "client", mock_client)
    secrets_handler = SecretsHandler(config=DEFAULT_TEST_CONFIG)

    # call delete_secrets()
    secrets_handler.delete_secrets(secrets=secrets_to_delete)

    # list_secrets is ONLY called if secrets_to_delete is None or empty list
    if not secrets_to_delete:
        mock_client.secrets.kv.v2.list_secrets.assert_called_once()
    else:
        mock_client.secrets.kv.v2.list_secrets.assert_not_called()

    # delete_metadata_and_all_versions is called for each secret in secrets_to_delete
    #   if that's not supplied, then it is called for each value in list_secrets
    calls = (
        [
            call(path=f"{DEFAULT_TEST_CONFIG.vault_path}/{secret}")
            for secret in stored_secrets
        ]
        if not secrets_to_delete
        else [
            call(path=f"{DEFAULT_TEST_CONFIG.vault_path}/{secret}")
            for secret in secrets_to_delete
        ]
    )
    mock_client.secrets.kv.v2.delete_metadata_and_all_versions.assert_has_calls(
        calls,
        any_order=True,
    )
