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

from aiokafka import TopicPartition
from aiokafka.admin import AIOKafkaAdminClient, RecordsToDelete

from sms.config import Config
from sms.ports.inbound.events_handler import EventsHandlerPort


class EventsHandler(EventsHandlerPort):
    """A class to manage the state of kafka events."""

    def __init__(self, *, config: Config):
        self._config = config

    def get_admin_client(self) -> AIOKafkaAdminClient:
        """Construct and return an instance of AIOKafkaAdminClient."""
        return AIOKafkaAdminClient(bootstrap_servers=self._config.kafka_servers)

    async def clear_topics(self, *, topics: list[str], exclude_internal: bool = True):
        """Clear messages from given topic(s).

        If no topics are specified, all topics will be cleared, except internal topics
        unless otherwise specified.
        """
        admin_client = self.get_admin_client()
        await admin_client.start()
        try:
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
        finally:
            await admin_client.close()
