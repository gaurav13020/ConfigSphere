from __future__ import annotations

import json
import os

from confluent_kafka import Producer


class InvalidationPublisher:
    """Publishes cache invalidation events to Kafka after a config version is activated."""

    def __init__(self) -> None:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self._topic = os.getenv("KAFKA_INVALIDATION_TOPIC", "config.invalidated")
        self._producer = Producer({"bootstrap.servers": bootstrap})

    def publish_invalidation(self, service_name: str, path: str, tree_version: int) -> None:
        payload = {"service_name": service_name, "path": path, "tree_version": tree_version}
        self._producer.produce(self._topic, json.dumps(payload).encode("utf-8"))
        self._producer.flush()
