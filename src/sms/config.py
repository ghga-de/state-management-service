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

"""Config Parameter Modeling and Parsing."""

from ghga_service_commons.api import ApiConfigBase
from hexkit.config import config_from_yaml
from hexkit.log import LoggingConfig
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings

SERVICE_NAME: str = "sms"


class SmsConfig(BaseSettings):
    """Configuration specific to the SMS."""

    token_hashes: list[str] = Field(
        default=...,
        description="List of token hashes corresponding to the tokens that can be used "
        + "to authenticate calls to this service. Hashes are made with SHA-256.",
        examples=["7ad83b6b9183c91674eec897935bc154ba9ff9704f8be0840e77f476b5062b6e"],
    )
    db_prefix: str = Field(
        default=...,
        description="Prefix to add to all database names used in the SMS.",
        examples=["testing-branch-name-"],
    )
    db_permissions: list[str] | None = Field(
        default=None,
        description=(
            "List of permissions that can be granted on a collection. Use * to signify"
            + " 'all'. The format is '<db_name>.<collection_name>.<permissions>', e.g."
            + " 'db1.collection1.crud'. The permissions are 'r' for read and 'w' for"
            + " write. Deletion is a write operation. If db_permissions are not set, no"
            + " operations are allowed on any database or collection."
        ),
        examples=[
            "db1.coll1.r",
            "db1.coll1.w",
            "db1.coll1.rw",
            "db1.coll1.*",
            "db2.*.r",
            "db3.*.*",
            "*.*.r",
            "*.*.*",
        ],
    )
    db_connection_str: SecretStr = Field(
        default=...,
        examples=["mongodb://localhost:27017"],
        description=(
            "MongoDB connection string. Might include credentials."
            + " For more information see:"
            + " https://naiveskill.com/mongodb-connection-string/"
        ),
    )

    @field_validator("db_permissions")
    @classmethod
    def validate_permissions(cls, value):
        """Validate the permissions to make sure only 'r', 'w', 'rw', and '*' are used."""
        if value is None:
            return value
        for perm in value:
            parts = perm.split(".")
            if len(parts) != 3:
                raise ValueError(
                    f"Invalid permission '{perm}'."
                    + " Must have exactly two periods ('.') in it."
                )
            ops = parts[2]
            if ops not in ("r", "w", "rw", "*"):
                raise ValueError(
                    f"Invalid permission '{ops}' in '{perm}'."
                    + " Only 'r', 'w', 'rw', and '*' are allowed."
                )
        return value


@config_from_yaml(prefix=SERVICE_NAME)
class Config(ApiConfigBase, LoggingConfig, SmsConfig):
    """Config parameters and their defaults."""

    service_name: str = Field(
        default=SERVICE_NAME, description="Short name of this service"
    )
