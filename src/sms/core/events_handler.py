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
"""Contains implementation of the EventsHandler class."""

import json
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer, TopicPartition
from aiokafka.admin import AIOKafkaAdminClient, RecordsToDelete
from hexkit.correlation import new_correlation_id
from hexkit.providers.akafka.provider.utils import generate_ssl_context

from sms.config import Config
from sms.ports.inbound.events_handler import EventsHandlerPort


class EventsHandler(EventsHandlerPort):
    """A class to manage the state of kafka events."""

    def __init__(self, *, config: Config):
        self._config = config

    @asynccontextmanager
    async def get_admin_client(self) -> AsyncGenerator[AIOKafkaAdminClient, None]:
        """Construct and return an instance of AIOKafkaAdminClient that is closed after use."""
        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=self._config.kafka_servers,
            security_protocol=self._config.kafka_security_protocol,
            ssl_context=generate_ssl_context(self._config),
        )
        await admin_client.start()
        try:
            yield admin_client
        finally:
            await admin_client.close()

    @asynccontextmanager
    async def get_producer(self) -> AsyncGenerator[AIOKafkaProducer, None]:
        """Construct and return an instance of AIOKafkaProducer that is closed after use."""
        producer = AIOKafkaProducer(
            bootstrap_servers=self._config.kafka_servers,
            security_protocol=self._config.kafka_security_protocol,
            ssl_context=generate_ssl_context(self._config),
        )
        await producer.start()
        try:
            yield producer
        finally:
            await producer.stop()

    async def clear_topics(self, *, topics: list[str], exclude_internal: bool = True):
        """Clear messages from given topic(s).

        If no topics are specified, all topics will be cleared, except internal topics
        unless otherwise specified.
        """
        async with self.get_admin_client() as admin_client:
            if not topics:
                topics = await admin_client.list_topics()
            if exclude_internal:
                topics = [topic for topic in topics if not topic.startswith("__")]
            topics_info = await admin_client.describe_topics(topics)
            records_to_delete = {
                TopicPartition(
                    topic=topic_info["topic"], partition=partition_info["partition"]
                ): RecordsToDelete(before_offset=-1)
                for topic_info in topics_info
                for partition_info in topic_info["partitions"]
            }
            await admin_client.delete_records(records_to_delete, timeout_ms=10000)

    async def publish_event(
        self,
        *,
        topic: str,
        payload: Mapping[str, str],
        type_: bytes,
        key: bytes,
    ):
        """Publish a single event to the given topic.

        Assign a correlation ID to the event and set it in the headers.
        """
        async with self.get_producer() as producer:
            correlation_id = new_correlation_id()
            headers = {"correlation_id": correlation_id.encode()}
            if type_:
                headers["type"] = type_

            value = json.dumps(payload).encode("utf-8")
            await producer.send_and_wait(
                topic,
                value=value,
                key=key,
                headers=[(k, v) for k, v in headers.items()],
            )
