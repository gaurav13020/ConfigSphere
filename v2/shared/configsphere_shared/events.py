from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class BaseEvent(BaseModel):
    event_type: str
    correlation_id: str
    created_at: datetime


class ImplementRequestedEvent(BaseEvent):
    event_type: Literal["IMPLEMENT_REQUESTED"] = "IMPLEMENT_REQUESTED"
    request_id: UUID
    revision_id: UUID
    service_id: UUID
    target_config_node_id: UUID


class RollbackRequestedEvent(BaseEvent):
    event_type: Literal["ROLLBACK_REQUESTED"] = "ROLLBACK_REQUESTED"
    rollback_request_id: UUID
    request_id: UUID
    revision_id: UUID
    service_id: UUID
    target_config_node_id: UUID

