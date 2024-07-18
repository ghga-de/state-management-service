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

"""Test the DocDao class without any real"""

from contextlib import nullcontext
from unittest.mock import AsyncMock

import pytest
from hexkit.providers.mongodb.testutils import MongoDbFixture

from sms.core.docs_handler import DocsHandler, Permissions
from sms.inject import prepare_docs_handler
from sms.models import DocumentType, UpsertionDetails
from sms.ports.outbound.docs_dao import DocsDaoPort
from tests.fixtures.config import get_config

# tests:
# doc dao class
#     test for erring and successful calls to each method
#     test for correct prefix usage

TEST_DOCS: list[DocumentType] = [
    {"_id": "1", "test": "test"},
    {"_id": "2", "test": "second"},
]

READONLY = "readonly"
WRITEONLY = "writeonly"
READWRITE = "readwrite"
ALLOPS = "allops"
UNLISTED_COLLECTION = "unlistedcollection"
UNLISTED_DB = "unlisteddb"
TEST_DB = "testdb"


def test_permissions():
    """Test the Permissions class."""
    config = get_config()
    permissions = Permissions(config.db_permissions or [])

    assert permissions.get_permissions(TEST_DB, ALLOPS) == "*"
    assert permissions.get_permissions(TEST_DB, READONLY) == "r"
    assert permissions.get_permissions(TEST_DB, WRITEONLY) == "w"
    assert permissions.get_permissions(TEST_DB, READWRITE) == "rw"
    assert permissions.get_permissions(TEST_DB, UNLISTED_COLLECTION) == ""
    assert permissions.get_permissions(UNLISTED_DB, "all") == ""


@pytest.mark.parametrize(
    "db_name, collection, error",
    [
        (TEST_DB, UNLISTED_COLLECTION, PermissionError),
        (TEST_DB, WRITEONLY, PermissionError),
        (TEST_DB, READONLY, None),
        (TEST_DB, READWRITE, None),
        (TEST_DB, ALLOPS, None),
        (UNLISTED_DB, "all", PermissionError),
    ],
)
@pytest.mark.asyncio
async def test_read(
    mongodb: MongoDbFixture,
    db_name: str,
    collection: str,
    error: type[Exception] | None,
):
    """Make sure we get a permission error when trying to read a write-only collection."""
    config = get_config(sources=[mongodb.config])

    async with prepare_docs_handler(config=config) as docs_handler:
        # Attempt read
        with pytest.raises(error) if error else nullcontext():
            await docs_handler.get(db_name=db_name, collection=collection, criteria={})


@pytest.mark.parametrize(
    "db_name, collection, error",
    [
        (TEST_DB, UNLISTED_COLLECTION, PermissionError),
        (TEST_DB, WRITEONLY, None),
        (TEST_DB, READONLY, PermissionError),
        (TEST_DB, READWRITE, None),
        (TEST_DB, ALLOPS, None),
        (UNLISTED_DB, "all", PermissionError),
    ],
    ids=[
        "UnlistedCollection",
        "WriteOnlyCollection",
        "ReadOnlyCollection",
        "ReadWriteCollection",
        "AllOpsCollection",
        "UnlistedDB",
    ],
)
@pytest.mark.asyncio
async def test_write(
    mongodb: MongoDbFixture,
    db_name: str,
    collection: str,
    error: type[Exception] | None,
):
    """Make sure we get a permission error when trying to write to a read-only collection."""
    config = get_config(sources=[mongodb.config])

    upsertion_details = UpsertionDetails(documents=TEST_DOCS)
    async with prepare_docs_handler(config=config) as docs_handler:
        with pytest.raises(error) if error else nullcontext():
            # Attempt upsert
            await docs_handler.upsert(
                db_name=db_name,
                collection=collection,
                upsertion_details=upsertion_details,
            )

        with pytest.raises(error) if error else nullcontext():
            # Attempt delete
            await docs_handler.delete(
                db_name=db_name,
                collection=collection,
                criteria={},
            )


@pytest.mark.asyncio
async def test_dao_error_handling():
    """Test errors that bubble up from the DocsDao. Currently they are not handled."""
    docs_dao = AsyncMock(spec=DocsDaoPort)
    docs_dao.get.side_effect = DocsHandler.OperationError()
    docs_dao.upsert.side_effect = DocsHandler.OperationError()
    docs_dao.delete.side_effect = DocsHandler.OperationError()

    config = get_config()
    docs_handler = DocsHandler(config=config, docs_dao=docs_dao)
    with pytest.raises(DocsHandler.OperationError):
        await docs_handler.get(db_name=TEST_DB, collection=ALLOPS, criteria={})

    with pytest.raises(DocsHandler.OperationError):
        await docs_handler.upsert(
            db_name=TEST_DB,
            collection=ALLOPS,
            upsertion_details=UpsertionDetails(documents=TEST_DOCS),
        )

    with pytest.raises(DocsHandler.OperationError):
        await docs_handler.delete(db_name=TEST_DB, collection=ALLOPS, criteria={})
