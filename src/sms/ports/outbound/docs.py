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

"""Contains port definition for a Doc Handler"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


# TODO: Document errors and args for each method
class DocsDaoPort(ABC):
    """Port definition for a Doc Handler"""

    @abstractmethod
    async def get(
        self, db_name: str, collection: str, criteria: Mapping[str, Any]
    ) -> list[Mapping[str, Any]]:
        """Get documents satisfying the criteria."""
        ...

    @abstractmethod
    async def upsert(
        self,
        db_name: str,
        collection: str,
        documents: Mapping[str, Any] | list[Mapping[str, Any]],
    ) -> None:
        """Insert or update a document."""
        ...

    @abstractmethod
    async def delete(
        self, db_name: str, collection: str, criteria: Mapping[str, Any]
    ) -> None:
        """Delete documents satisfying the criteria."""
        ...
