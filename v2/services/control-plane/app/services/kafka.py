from __future__ import annotations

import json
import os

from confluent_kafka import Producer


class KafkaPublisher:
    def __init__(self) -> None:
        self.enabled = os.getenv("KAFKA_BOOTSTRAP_SERVERS") is not None
        self.producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")})

    def publish(self, topic: str, payload: dict) -> None:
        if not self.enabled:
            return
        self.producer.produce(topic, json.dumps(payload).encode("utf-8"))
        self.producer.flush()

