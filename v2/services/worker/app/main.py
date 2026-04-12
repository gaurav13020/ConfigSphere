from __future__ import annotations

import json
import logging
import os
import time
import uuid

from confluent_kafka import Consumer, Producer

from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.events import JiraSyncRequestedEvent

from app.core.jira_client import JiraClient
from app.core.jira_sync import JiraSyncProcessor
from app.core.processor import PropagationProcessor
from app.db import SessionLocal

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer(
            {"bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")}
        )
    return _producer


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": "configsphere-v2-worker",
            "auto.offset.reset": "earliest",
        }
    )


def handle_implement_message(payload: dict) -> None:
    correlation_id = payload.get("correlation_id")
    if not correlation_id:
        return
    with SessionLocal() as db:
        processor = PropagationProcessor(db, ConfigPayloadStore())
        processor.process_job(correlation_id)
        if processor._pending_sync_event_ids:
            producer = get_producer()
            for sid in processor._pending_sync_event_ids:
                event = JiraSyncRequestedEvent(
                    sync_event_id=sid,
                    correlation_id=str(sid),
                    created_at=__import__("datetime").datetime.utcnow(),
                )
                producer.produce(
                    "jira-sync-events",
                    json.dumps(event.model_dump(mode="json")).encode("utf-8"),
                )
                logger.info("Published Jira sync event %s to jira-sync-events", sid)
            producer.flush()


def handle_jira_sync_message(payload: dict) -> None:
    sync_event_id = payload.get("sync_event_id")
    if not sync_event_id:
        logger.warning("Jira sync message missing sync_event_id")
        return
    jira = JiraClient()
    with SessionLocal() as db:
        processor = JiraSyncProcessor(db, jira)
        processor.process_event(uuid.UUID(sync_event_id))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    consumer = build_consumer()
    consumer.subscribe(["config-implement-requests", "jira-sync-events"])
    logger.info("Worker started, listening on config-implement-requests and jira-sync-events")
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            time.sleep(1)
            continue
        if msg.error():
            logger.error("Kafka error: %s", msg.error())
            time.sleep(1)
            continue
        topic = msg.topic()
        payload = json.loads(msg.value().decode("utf-8"))
        if topic == "config-implement-requests":
            handle_implement_message(payload)
        elif topic == "jira-sync-events":
            handle_jira_sync_message(payload)
        consumer.commit(msg)


if __name__ == "__main__":
    main()

