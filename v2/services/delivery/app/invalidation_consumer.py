from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid

import aiokafka

from configsphere_shared.cache import TwoTierCache

# Re-exported so tests can patch `app.invalidation_consumer.AIOKafkaConsumer`
AIOKafkaConsumer = aiokafka.AIOKafkaConsumer

logger = logging.getLogger(__name__)

_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
_TOPIC = os.getenv("KAFKA_INVALIDATION_TOPIC", "config.invalidated")


_RETRY_DELAY_SECONDS = float(os.getenv("KAFKA_CONSUMER_RETRY_DELAY_SECONDS", "5"))
_MAX_RETRIES = int(os.getenv("KAFKA_CONSUMER_MAX_RETRIES", "12"))  # ~1 min total


async def run_invalidation_consumer(cache: TwoTierCache) -> None:
    group_id = f"delivery-cache-invalidator-{uuid.uuid4()}"

    for attempt in range(1, _MAX_RETRIES + 1):
        consumer = AIOKafkaConsumer(
            _TOPIC,
            bootstrap_servers=_BOOTSTRAP,
            group_id=group_id,
            auto_offset_reset="latest",
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        )
        try:
            await consumer.start()
            break
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning("Kafka not ready (attempt %d/%d): %s", attempt, _MAX_RETRIES, exc)
            if attempt == _MAX_RETRIES:
                logger.error("Giving up on Kafka invalidation consumer after %d attempts", _MAX_RETRIES)
                return
            await asyncio.sleep(_RETRY_DELAY_SECONDS)

    logger.info("Invalidation consumer started (group=%s, topic=%s)", group_id, _TOPIC)
    try:
        async for msg in consumer:
            service_name = msg.value.get("service_name")
            path = msg.value.get("path")
            if not service_name or not path:
                logger.warning("Malformed invalidation message: %s", msg.value)
                continue
            config_key = f"delivery:config:{service_name}:{path}"
            version_key = f"delivery:version:{service_name}:{path}"
            cache.delete(config_key)
            cache.delete(version_key)
            logger.info("Cache invalidated: service=%s path=%s", service_name, path)
    except asyncio.CancelledError:
        pass
    finally:
        await consumer.stop()
        logger.info("Invalidation consumer stopped")
