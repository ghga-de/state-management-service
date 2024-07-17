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

import logging
from collections.abc import Mapping
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from sms.config import Config
from sms.ports.outbound.docs import DocsDaoPort


# TODO: Document errors and args for each method
def log_and_raise_permissions_error(db_name: str, collection: str, operation: str):
    """Log and raise a PermissionError."""
    error = PermissionError(
        "Operation '%s' not allowed on db '%s' collection '%s'.",
        operation,
        db_name,
        collection,
    )
    logging.error(
        error,
        extra={"db_name": db_name, "collection": collection, "operation": operation},
    )
    raise error


class Permissions(BaseModel):
    """A class to parse and interpret configured permissions for database operations."""

    permissions: list[str] | None

    def get_permissions(self, db_name, collection_name) -> str:
        """List the operations allowed on the specified collection."""
        if not self.permissions:
            return ""

        for permission in self.permissions:
            db, collection, ops = permission.split(".")
            if db in ("*", db_name) and collection in ("*", collection_name):
                return ops
        return ""

    def is_op_allowed(self, db_name, collection_name, op) -> bool:
        """Check if the operation is allowed on the specified collection."""
        permissions = self.get_permissions(db_name, collection_name)
        return op in permissions or "*" in permissions


class DocsDao(DocsDaoPort):
    """A class to perform CRUD operations in MongoDB."""

    def __init__(self, config: Config):
        """Initialize a DocDao instance."""
        self._prefix = config.db_prefix
        self._permissions = Permissions(permissions=config.db_permissions)
        self.client = AsyncIOMotorClient(config.db_connection_str.get_secret_value())

    async def get(
        self, db_name: str, collection: str, criteria: Mapping[str, Any]
    ) -> list[Mapping[str, Any]]:
        """Get documents satisfying the criteria."""
        if not self._permissions.is_op_allowed(db_name, collection, "r"):
            log_and_raise_permissions_error(db_name, collection, "read")
        return [x async for x in self.client[db_name][collection].find(criteria)]

    async def upsert(
        self,
        db_name: str,
        collection: str,
        documents: Mapping[str, Any] | list[Mapping[str, Any]],
    ) -> None:
        """Insert or update a document."""
        # Get permissions for collection
        permissions = [
            p
            for p in ("c", "u")
            if self._permissions.is_op_allowed(db_name, collection, p)
        ]

        if not permissions:
            log_and_raise_permissions_error(db_name, collection, "create, update")

        # Work with a list
        if not isinstance(documents, list):
            documents = [documents]

        for document in documents:
            doc_in_db = self.client[db_name][collection].find_one(document)
            if doc_in_db is not None:
                if "u" in permissions:
                    await self.client[db_name][collection].update_one(
                        {"_id": document["_id"]}, {"$set": document}
                    )
                else:
                    log_and_raise_permissions_error(db_name, collection, "update")
            elif "c" in permissions:
                await self.client[db_name][collection].insert_one(document)
            else:
                log_and_raise_permissions_error(db_name, collection, "create")

    async def delete(
        self, db_name: str, collection: str, criteria: Mapping[str, Any]
    ) -> None:
        """Delete documents satisfying the criteria."""
        if not self._permissions.is_op_allowed(db_name, collection, "d"):
            log_and_raise_permissions_error(db_name, collection, "delete")

        await self.client[db_name][collection].delete_many(criteria)
