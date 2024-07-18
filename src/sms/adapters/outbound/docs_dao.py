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
"""Contains the implementation of the DocsDao, providing the state management for MongoDB"""

from motor.motor_asyncio import AsyncIOMotorClient

from sms.config import Config
from sms.models import Criteria, DocumentType
from sms.ports.outbound.docs_dao import DocsDaoPort

# TODO: Document errors and args for each method


class DocsDao(DocsDaoPort):
    """A class to perform CRUD operations in MongoDB."""

    def __init__(self, *, config: Config):
        """Initialize a DocDao instance."""
        self._client: AsyncIOMotorClient = AsyncIOMotorClient(
            config.db_connection_str.get_secret_value()
        )

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context manager and close the client connection."""
        self._client.close()

    async def get(
        self, *, db_name: str, collection: str, criteria: Criteria
    ) -> list[DocumentType]:
        """Get documents satisfying the criteria."""
        return [x async for x in self._client[db_name][collection].find(criteria)]

    async def upsert(
        self,
        *,
        db_name: str,
        collection: str,
        id_field: str,
        documents: list[DocumentType],
    ) -> None:
        """Insert or update one or more documents."""
        collection_instance = self._client[db_name][collection]

        for doc in documents:
            await collection_instance.update_one(
                {id_field: doc[id_field]}, {"$set": doc}, upsert=True
            )

    async def delete(
        self, *, db_name: str, collection: str, criteria: Criteria
    ) -> None:
        """Delete documents satisfying the criteria."""
        await self._client[db_name][collection].delete_many(criteria)
