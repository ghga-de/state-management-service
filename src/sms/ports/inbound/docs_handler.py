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
"""Contains the abstract definition of a DocsHandler."""

from abc import ABC, abstractmethod

from sms.models import Criteria, DocumentType, UpsertionDetails


class DocsHandlerPort(ABC):
    """Port definition for a Doc Handler"""

    class MissingIdFieldError(RuntimeError):
        """Raised when the id field is missing."""

        def __init__(self, *, id_field: str):
            super().__init__(f"The id '{id_field}' field is missing on a document.")

    class OperationError(RuntimeError):
        """Raised when a database operation fails."""

        def __init__(self):
            super().__init__("The database operation failed.")

    @abstractmethod
    async def get(
        self, db_name: str, collection: str, criteria: Criteria
    ) -> list[DocumentType]:
        """Get documents satisfying the criteria."""
        ...

    @abstractmethod
    async def upsert(
        self, db_name: str, collection: str, upsertion_details: UpsertionDetails
    ) -> None:
        """Insert or update one or more documents."""
        ...

    @abstractmethod
    async def delete(self, db_name: str, collection: str, criteria: Criteria) -> None:
        """Delete documents satisfying the criteria."""
        ...
