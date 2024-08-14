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
"""Dependency injection required to run the SMS service."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from ghga_service_commons.utils.context import asyncnullcontext
from hexkit.providers.s3 import S3ObjectStorage

from sms.adapters.inbound.fastapi_ import dummies
from sms.adapters.inbound.fastapi_.configure import get_configured_app
from sms.adapters.outbound.docs_dao import DocsDao
from sms.config import Config
from sms.core.docs_handler import DocsHandler
from sms.core.objects_handler import ObjectsHandler
from sms.ports.inbound.docs_handler import DocsHandlerPort
from sms.ports.inbound.objects_handler import ObjectsHandlerPort


@asynccontextmanager
async def prepare_docs_handler(
    *, config: Config
) -> AsyncGenerator[DocsHandlerPort, None]:
    """Prepare the DocsHandler with a DocsDao to manage the database."""
    async with DocsDao(config=config) as docs_dao:
        docs_handler = DocsHandler(config=config, docs_dao=docs_dao)
        yield docs_handler


def prepare_docs_handler_with_override(
    *, config: Config, docs_handler_override: DocsHandlerPort | None = None
):
    """Resolve the docs handler context manager based on config and override (if any)."""
    return (
        asyncnullcontext(docs_handler_override)
        if docs_handler_override
        else prepare_docs_handler(config=config)
    )


def prepare_objects_handler(*, config: Config) -> ObjectsHandlerPort:
    """Prepare the ObjectsHandler with an S3ObjectStorage instance."""
    object_storage = S3ObjectStorage(config=config)
    return ObjectsHandler(config=config, object_storage=object_storage)


def prepare_objects_handler_with_override(
    *, config: Config, objects_handler_override: ObjectsHandlerPort | None = None
) -> ObjectsHandlerPort:
    """Resolve the objects handler context manager based on config and override (if any)."""
    return (
        objects_handler_override
        if objects_handler_override
        else prepare_objects_handler(config=config)
    )


@asynccontextmanager
async def prepare_rest_app(
    *,
    config: Config,
    docs_handler_override: DocsHandlerPort | None = None,
    objects_handler_override: ObjectsHandlerPort | None = None,
) -> AsyncGenerator[FastAPI, None]:
    """Construct and initialize a REST API app along with all its dependencies.
    By default, the core dependencies are automatically prepared but you can also
    provide them using the "_override" parameter(s).
    """
    app = get_configured_app(config=config)

    objects_handler = prepare_objects_handler_with_override(
        config=config, objects_handler_override=objects_handler_override
    )
    app.dependency_overrides[dummies.objects_handler_port] = lambda: objects_handler

    async with prepare_docs_handler_with_override(
        config=config, docs_handler_override=docs_handler_override
    ) as docs_handler:
        app.dependency_overrides[dummies.config_dummy] = lambda: config
        app.dependency_overrides[dummies.docs_handler_port] = lambda: docs_handler
        yield app
