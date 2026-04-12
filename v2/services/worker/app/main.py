from __future__ import annotations

import json
import os
import time

from confluent_kafka import Consumer

from configsphere_shared.config_payloads import ConfigPayloadStore

from app.core.processor import PropagationProcessor
from app.db import SessionLocal


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": "configsphere-v2-worker",
            "auto.offset.reset": "earliest",
        }
    )


def handle_message(payload: dict) -> None:
    correlation_id = payload.get("correlation_id")
    if not correlation_id:
        return
    with SessionLocal() as db:
        processor = PropagationProcessor(db, ConfigPayloadStore())
        processor.process_job(correlation_id)


def main() -> None:
    consumer = build_consumer()
    consumer.subscribe(["config-implement-requests"])
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            time.sleep(1)
            continue
        if msg.error():
            time.sleep(1)
            continue
        payload = json.loads(msg.value().decode("utf-8"))
        handle_message(payload)
        consumer.commit(msg)


if __name__ == "__main__":
    main()

