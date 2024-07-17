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
from pydantic import Field, SecretStr
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
            + " 'db1.collection1.crud'. The permissions are 'c' for create, 'r' for read,"
            + " 'u' for update, and 'd' for delete. If db_permissions is None, no"
            + " operations are allowed on any database or collection."
        ),
        examples=["db1.collection1.crud", "db2.*.r", "db3.*.*", "*.*.*"],
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


@config_from_yaml(prefix=SERVICE_NAME)
class Config(ApiConfigBase, LoggingConfig, SmsConfig):
    """Config parameters and their defaults."""

    service_name: str = Field(
        default=SERVICE_NAME, description="Short name of this service"
    )


CONFIG = Config()  # type: ignore
