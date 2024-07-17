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

"""Test the REST API endpoints for /docs/"""

from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import pytest
from ghga_service_commons.api.testing import AsyncTestClient

from sms.config import Config
from sms.inject import prepare_rest_app
from sms.ports.outbound.docs import DocsDaoPort
from tests.fixtures.config import get_config

pytestmark = pytest.mark.asyncio()
VALID_BEARER_TOKEN = "Bearer 43fadc91-b98f-4925-bd31-1b054b13dc55"


@dataclass
class DocsApiCallArgs:
    """Arguments for an API call."""

    method: str
    db_name: str
    collection: str
    criteria: Mapping[str, Any] | None = None
    documents: Mapping[str, Any] | list[Mapping[str, Any]] | None = None


class DummyDocsDao(DocsDaoPort):
    """Dummy DocsDao implementation for unit testing."""

    calls: list[DocsApiCallArgs]

    def __init__(self):
        self.calls = []

    async def get(self, db_name: str, collection: str, criteria: Mapping[str, Any]):
        """Dummy get implementation."""
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
        documents: Mapping[str, Any] | list[Mapping[str, Any]],
    ):
        """Dummy upsert implementation."""
        call = DocsApiCallArgs(
            method="put", db_name=db_name, collection=collection, documents=documents
        )
        self.calls.append(call)
        if collection == "permission_error":
            raise PermissionError()

    async def delete(self, db_name: str, collection: str, criteria: Mapping[str, Any]):
        """Dummy delete implementation."""
        call = DocsApiCallArgs(
            method="delete", db_name=db_name, collection=collection, criteria=criteria
        )
        self.calls.append(call)
        if collection == "permission_error":
            raise PermissionError()


@asynccontextmanager
async def get_rest_client(config: Config, docs_dao_override: DocsDaoPort):
    """Prepare a REST API client for testing."""
    async with prepare_rest_app(
        config=config, docs_dao_override=docs_dao_override
    ) as app:
        async with AsyncTestClient(app) as client:
            yield client


async def test_health_check():
    """Test the health check endpoint."""
    config = get_config()
    async with get_rest_client(config, DummyDocsDao()) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "OK"}


@pytest.mark.parametrize(
    "headers",
    [{"Authorization": "Bearer 123"}, {}],
    ids=["WrongApiKey", "NoApiKey"],
)
@pytest.mark.parametrize(
    "http_method",
    ["get", "put", "delete"],
    ids=["GET", "PUT", "DELETE"],
)
async def test_unauthenticated_calls(http_method: str, headers: dict[str, str]):
    """Test unauthenticated calls, which should result in a 401 Unauthorized code."""
    config = get_config()
    dummy_docs_dao = DummyDocsDao()
    async with get_rest_client(config, dummy_docs_dao) as client:
        method_to_call = getattr(client, http_method)
        response = await method_to_call("/docs/testdb/testcollection", headers=headers)

    # Verify status code and make sure there were no DAO method calls
    assert response.status_code == 401
    assert dummy_docs_dao.calls == []


@pytest.mark.parametrize(
    "http_method, expected_status_code",
    [
        ("get", 200),
        ("put", 204),
        ("delete", 204),
    ],
    ids=["GET", "PUT", "DELETE"],
)
async def test_authenticated_valid_calls(http_method: str, expected_status_code: int):
    """Verify authenticated calls are successfully passed to the DAO."""
    config = get_config()
    dummy_docs_dao = DummyDocsDao()
    async with get_rest_client(config, dummy_docs_dao) as client:
        method_to_call = getattr(client, http_method)

        put_args: dict[str, Any] = {"json": {}} if http_method == "put" else {}
        response = await method_to_call(
            url="/docs/testdb/testcollection",
            headers={"Authorization": VALID_BEARER_TOKEN},
            **put_args,
        )

    # Verify status code and DAO method calls
    assert response.status_code == expected_status_code, response.json()
    call = DocsApiCallArgs(
        method=http_method,
        db_name="testdb",
        collection="testcollection",
        criteria=None if http_method == "put" else {},
        documents=None if http_method != "put" else {},
    )
    assert dummy_docs_dao.calls == [call]


@pytest.mark.parametrize(
    "http_method, expected_status_code",
    [("get", 200), ("delete", 204)],
    ids=["GET", "DELETE"],
)
@pytest.mark.parametrize(
    "query_string, as_dict",
    [
        # Test with a few different query strings
        ("name=Alice&age=34", {"name": "Alice", "age": "34"}),
        ("name=Alice&age=34&", {"name": "Alice", "age": "34"}),
        (
            "name=Ellen_Ripley&age=62&location=",
            {"name": "Ellen_Ripley", "age": "62", "location": ""},
        ),
    ],
)
async def test_calls_with_query_params(
    http_method: str,
    expected_status_code: int,
    query_string: str,
    as_dict: Mapping[str, str],
):
    """Verify calls with query parameters (GET and DELETE)."""
    config = get_config()
    dummy_docs_dao = DummyDocsDao()
    async with get_rest_client(config, dummy_docs_dao) as client:
        method_to_call = getattr(client, http_method)
        response = await method_to_call(
            url=f"/docs/testdb/testcollection?{query_string}",
            headers={"Authorization": VALID_BEARER_TOKEN},
        )

    # Verify status code and DAO method calls
    assert response.status_code == expected_status_code
    call = DocsApiCallArgs(
        method=http_method,
        db_name="testdb",
        collection="testcollection",
        criteria=as_dict,
    )
    assert dummy_docs_dao.calls == [call]


@pytest.mark.parametrize(
    "http_method",
    ["get", "put", "delete"],
    ids=["GET", "PUT", "DELETE"],
)
async def test_permission_errors(
    http_method: str,
):
    """Test that permission errors are handled correctly."""
    config = get_config()
    dummy_docs_dao = DummyDocsDao()
    async with get_rest_client(config, dummy_docs_dao) as client:
        method_to_call = getattr(client, http_method)
        put_args: dict[str, Any] = {"json": {}} if http_method == "put" else {}
        response = await method_to_call(
            url="/docs/testdb/permission_error",
            headers={"Authorization": VALID_BEARER_TOKEN},
            **put_args,
        )
    assert response.status_code == 403

    assert len(dummy_docs_dao.calls) == 1
    assert dummy_docs_dao.calls[0].method == http_method


async def test_put_with_docs():
    """Test PUT with documents."""
    config = get_config()
    dummy_docs_dao = DummyDocsDao()
    docs_to_insert: list[Mapping[str, Any]] = [{"name": "Alice"}, {"name": "Bob"}]
    async with get_rest_client(config, dummy_docs_dao) as client:
        response = await client.put(
            url="/docs/testdb/testcollection",
            headers={"Authorization": VALID_BEARER_TOKEN},
            json=docs_to_insert,
        )

    # Verify status code and DAO method calls
    assert response.status_code == 204
    call = DocsApiCallArgs(
        method="put",
        db_name="testdb",
        collection="testcollection",
        documents=docs_to_insert,
    )
    assert dummy_docs_dao.calls == [call]
