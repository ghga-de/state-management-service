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

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager, nullcontext
from typing import Any

from fastapi import FastAPI

from sms.api import dummies
from sms.api.configure import get_configured_app
from sms.config import Config
from sms.core.docs import DocsDao
from sms.ports.outbound.docs import DocsDaoPort

# TODO: Remove config dummy if it's not needed


@contextmanager
def prepare_docs_dao(
    *,
    config: Config,
) -> Generator[DocsDaoPort, None, None]:
    """Prepare a dummy for the DocsDaoPort dependency."""
    docs_dao = DocsDao(config=config)
    yield docs_dao


def prepare_docs_dao_with_override(
    *, config: Config, docs_dao_override: DocsDaoPort | None = None
):
    """Resolve the docs dao context manager based on config and override (if any)."""
    return (
        nullcontext(docs_dao_override)
        if docs_dao_override
        else prepare_docs_dao(config=config)
    )


@asynccontextmanager
async def prepare_rest_app(
    *,
    config: Config,
    docs_dao_override: Any | None = None,
) -> AsyncGenerator[FastAPI, None]:
    """Construct and initialize a REST API app along with all its dependencies.
    By default, the core dependencies are automatically prepared but you can also
    provide them using the docs_dao_override parameter.
    """
    app = get_configured_app(config=config)

    with prepare_docs_dao_with_override(
        config=config, docs_dao_override=docs_dao_override
    ) as docs_dao:
        app.dependency_overrides[dummies.config_dummy] = lambda: config
        app.dependency_overrides[dummies.docs_dao_port] = lambda: docs_dao
        yield app
