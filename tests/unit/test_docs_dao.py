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
"""Test mongodb state management."""

import pytest
from hexkit.providers.mongodb.testutils import MongoDbFixture

from sms.adapters.outbound.docs_dao import DocsDao
from sms.models import DocumentType
from tests.fixtures.config import get_config

pytestmark = pytest.mark.asyncio()

TESTDB = "testdb"
ALLOPS = "allops"


async def test_all_ops(mongodb: MongoDbFixture):
    """Test get, upsert, and delete methods on the docs dao."""
    config = get_config(sources=[mongodb.config])

    # Verify the db is empty
    async with DocsDao(config=config) as docs_dao:
        initial_contents = await docs_dao.get(
            db_name=TESTDB, collection=ALLOPS, criteria={}
        )
        assert not initial_contents

        # Insert docs
        docs_to_insert: list[DocumentType] = [
            {"_id": "1", "test": "test"},
            {"_id": "2", "test": "second"},
            {"_id": "3", "test": "third"},
        ]
        await docs_dao.upsert(
            db_name=TESTDB,
            collection=ALLOPS,
            id_field="_id",
            documents=docs_to_insert,
        )

        # Check that docs are there
        post_insert = await docs_dao.get(db_name=TESTDB, collection=ALLOPS, criteria={})
        assert post_insert == docs_to_insert

        # Update docs
        doc_to_update = {"_id": "1", "test": "updated"}
        await docs_dao.upsert(
            db_name=TESTDB,
            collection=ALLOPS,
            id_field="_id",
            documents=[doc_to_update],
        )

        # Check that docs are updated
        post_update = await docs_dao.get(db_name=TESTDB, collection=ALLOPS, criteria={})
        docs_to_insert[0] = doc_to_update
        assert post_update == docs_to_insert

        # Delete first doc
        await docs_dao.delete(db_name=TESTDB, collection=ALLOPS, criteria={"_id": "3"})
        docs_to_insert.pop()

        # Check that other docs still remain
        remaining = await docs_dao.get(db_name=TESTDB, collection=ALLOPS, criteria={})
        assert remaining == docs_to_insert

        # Delete all docs
        await docs_dao.delete(db_name=TESTDB, collection=ALLOPS, criteria={})
        assert not await docs_dao.get(db_name=TESTDB, collection=ALLOPS, criteria={})


async def test_get_db_map_for_prefix(mongodb: MongoDbFixture):
    """Test get_db_map_for_prefix method on the docs dao."""
    config = get_config(sources=[mongodb.config])

    db_name1 = "db1"
    db_name2 = "db2"
    expected_db_map = {db_name1: ["test", "test2"], db_name2: ["test1"]}

    async with DocsDao(config=config) as docs_dao:
        # MongoDbFixture reset only empties collections, it doesn't delete them
        # so we need to drop the databases manually to verify the functionality
        for db in await docs_dao._client.list_database_names():
            if db.startswith(config.db_prefix):
                await docs_dao._client.drop_database(db)

        # Insert documents to create the expected db_map
        for db_name, colls in expected_db_map.items():
            for coll in colls:
                await docs_dao._client[f"{config.db_prefix}{db_name}"][coll].insert_one(
                    {"key": "value"}
                )

        assert not await docs_dao.get_db_map_for_prefix(prefix="db")
        assert not await docs_dao.get_db_map_for_prefix(prefix="")
        db_map = await docs_dao.get_db_map_for_prefix(prefix=config.db_prefix)
        assert db_map == expected_db_map

        db1_map = await docs_dao.get_db_map_for_prefix(
            prefix=config.db_prefix, db_name=db_name1
        )

        assert db1_map == {db_name1: ["test", "test2"]}

        assert await docs_dao.get_db_map_for_prefix(
            prefix=config.db_prefix, db_name="nonexistent"
        ) == {"nonexistent": []}
