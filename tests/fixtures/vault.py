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
"""HashiCorp vault fixture for testing"""

import time
from collections.abc import Generator

import hvac
import pytest
from pydantic import Field
from pydantic_settings import BaseSettings

# from testcontainers.vault import DockerContainer
from testcontainers.core.generic import DockerContainer

VAULT_URL = "http://0.0.0.0:8200"
VAULT_NAMESPACE = "vault"
VAULT_TOKEN = "dev-token"
VAULT_PORT = 8200


class VaultConfig(BaseSettings):
    """Configuration for vault container/fixture"""

    vault_url: str = Field(
        default="http://0.0.0.0:8200", description="URL of the vault server"
    )
    vault_role_id: str = Field(..., description="Role ID for vault authentication")
    vault_secret_id: str = Field(..., description="Secret ID for vault authentication")
    vault_path: str = Field(default="ekss", description="Path to store secrets")


class VaultFixture:
    """Contains initialized vault client"""

    def __init__(self, config: VaultConfig):
        self.config = config

    def store_secret(self, key: str):
        """Store a secret in vault"""
        client = hvac.Client(url=self.config.vault_url, token=VAULT_TOKEN)
        client.auth.approle.login(
            role_id=self.config.vault_role_id,
            secret_id=self.config.vault_secret_id,
        )
        client.secrets.kv.v2.create_or_update_secret(
            path=f"{self.config.vault_path}/{key}",
            secret={key: f"secret_for_{key}"},
        )


@pytest.fixture
def vault_fixture() -> Generator[VaultFixture, None, None]:
    """Generate preconfigured test container"""
    vault_container = (
        DockerContainer(image="hashicorp/vault:1.12")
        .with_exposed_ports(VAULT_PORT)
        .with_env("VAULT_ADDR", VAULT_URL)
        .with_env("VAULT_DEV_ROOT_TOKEN_ID", VAULT_TOKEN)
    )
    with vault_container:
        host = vault_container.get_container_host_ip()
        port = vault_container.get_exposed_port(VAULT_PORT)
        role_id, secret_id = configure_vault(host=host, port=int(port))
        config = VaultConfig(
            vault_url=f"http://{host}:{port}",
            vault_role_id=role_id,
            vault_secret_id=secret_id,
            vault_path="ekss",
        )
        # client needs some time after creation
        time.sleep(2)
        yield VaultFixture(config=config)


def configure_vault(*, host: str, port: int):
    """Configure vault using direct interaction with hvac.Client"""
    client = hvac.Client(url=f"http://{host}:{port}", token=VAULT_TOKEN)
    # client needs some time after creation
    time.sleep(2)

    # enable authentication with role_id/secret_id
    client.sys.enable_auth_method(
        method_type="approle",
    )

    # create access policy to bind to role
    ekss_policy = """
    path "secret/data/ekss/*" {
        capabilities = ["read", "create"]
    }
    path "secret/metadata/ekss/*" {
        capabilities = ["delete"]
    }
    """

    # inject policy
    client.sys.create_or_update_policy(
        name="ekss",
        policy=ekss_policy,
    )

    role_name = "test_role"
    # create role and bind policy
    response = client.auth.approle.create_or_update_approle(
        role_name=role_name,
        token_policies=["ekss"],
        token_type="service",
    )

    # retrieve role_id
    response = client.auth.approle.read_role_id(role_name=role_name)
    role_id = response["data"]["role_id"]

    # retrieve secret_id
    response = client.auth.approle.generate_secret_id(
        role_name=role_name,
    )
    secret_id = response["data"]["secret_id"]

    # log out root token client
    client.logout()

    return role_id, secret_id
