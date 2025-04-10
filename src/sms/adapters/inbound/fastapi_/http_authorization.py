# Copyright 2021 - 2025 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
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

"""Authorization specific code for FastAPI"""

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ghga_service_commons.auth.context import AuthContextProtocol
from ghga_service_commons.auth.policies import require_auth_context_using_credentials
from ghga_service_commons.utils.simple_token import check_token
from pydantic import BaseModel, Field

from sms.adapters.inbound.fastapi_.dummies import ConfigDummy

__all__ = ["TokenAuthContext", "require_token"]


class TokenAuthContext(BaseModel):
    """Auth context holding the ingest token."""

    token: str = Field(
        default=...,
        description="An alphanumeric token to authenticate HTTP requests",
    )


class TokenAuthProvider(AuthContextProtocol[TokenAuthContext]):
    """Provider for the ingest token auth context"""

    def __init__(self, *, token_hashes: list[str]):
        self._token_hashes = token_hashes

    async def get_context(self, token: str) -> TokenAuthContext:
        """Get ingest token auth context"""
        if not check_token(token=token, token_hashes=self._token_hashes):
            raise self.AuthContextValidationError("Invalid Token")

        return TokenAuthContext(token=token)


async def require_token_context(
    service_config: ConfigDummy,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> TokenAuthContext:
    """Require an authentication and authorization context using FastAPI.

    Both invalid and missing tokens will result in a 401 Unauthorized response.
    """
    return await require_auth_context_using_credentials(
        credentials=credentials,
        auth_provider=TokenAuthProvider(token_hashes=service_config.token_hashes),
    )


require_token = Security(require_token_context)
