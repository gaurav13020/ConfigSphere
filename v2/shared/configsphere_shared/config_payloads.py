from __future__ import annotations

import os
import time
import uuid
from datetime import datetime
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def _table_name() -> str:
    return os.getenv("DYNAMODB_TABLE", "config_payloads")


def _endpoint() -> str | None:
    return os.getenv("DYNAMODB_ENDPOINT")


def _region() -> str:
    return os.getenv("DYNAMODB_REGION", "us-east-1")


def _connect_timeout_seconds() -> int:
    return int(os.getenv("DYNAMODB_CONNECT_TIMEOUT_SECONDS", "2"))


def _read_timeout_seconds() -> int:
    return int(os.getenv("DYNAMODB_READ_TIMEOUT_SECONDS", "2"))


def _startup_retries() -> int:
    return int(os.getenv("DYNAMODB_STARTUP_RETRIES", "15"))


def _startup_retry_delay_seconds() -> float:
    return float(os.getenv("DYNAMODB_STARTUP_RETRY_DELAY_SECONDS", "1.5"))


def dynamodb_resource():
    kwargs: dict[str, Any] = {
        "region_name": _region(),
        "config": Config(
            connect_timeout=_connect_timeout_seconds(),
            read_timeout=_read_timeout_seconds(),
            retries={"max_attempts": 1, "mode": "standard"},
        ),
    }
    endpoint = _endpoint()
    if endpoint:
        kwargs["endpoint_url"] = endpoint
        kwargs["aws_access_key_id"] = "dummy"
        kwargs["aws_secret_access_key"] = "dummy"
    return boto3.resource("dynamodb", **kwargs)


def ensure_table() -> None:
    table_name = _table_name()
    attempts = _startup_retries()
    delay_seconds = _startup_retry_delay_seconds()

    for attempt in range(1, attempts + 1):
        try:
            dynamodb = dynamodb_resource()
            existing = {table.name for table in dynamodb.tables.all()}
            if table_name in existing:
                return

            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "sk", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "pk", "AttributeType": "S"},
                    {"AttributeName": "sk", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            ).wait_until_exists()
            return
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code == "ResourceInUseException":
                return
            if attempt == attempts:
                raise
        except BotoCoreError:
            if attempt == attempts:
                raise

        time.sleep(delay_seconds)


class ConfigPayloadStore:
    def __init__(self) -> None:
        ensure_table()
        self.table = dynamodb_resource().Table(_table_name())

    def put_document(self, entity_type: str, entity_id: str, version_token: str, payload: dict[str, Any]) -> str:
        document_id = payload.get("documentId") or str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        item = {
            "pk": f"ENTITY#{entity_type}#{entity_id}",
            "sk": f"VERSION#{version_token}",
            "documentId": document_id,
            "createdAt": payload.get("createdAt", now),
            **payload,
        }
        self.table.put_item(Item=item)
        return document_id

    def get_document(self, entity_type: str, entity_id: str, version_token: str) -> dict[str, Any] | None:
        response = self.table.get_item(
            Key={
                "pk": f"ENTITY#{entity_type}#{entity_id}",
                "sk": f"VERSION#{version_token}",
            }
        )
        return response.get("Item")

    def get_document_by_id(self, entity_type: str, entity_id: str, document_id: str) -> dict[str, Any] | None:
        response = self.table.query(
            KeyConditionExpression=Key("pk").eq(f"ENTITY#{entity_type}#{entity_id}")
        )
        for item in response.get("Items", []):
            if item.get("documentId") == document_id:
                return item
        return None
