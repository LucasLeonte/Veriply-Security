from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime


class EmailRuleCreate(BaseModel):
    integration_id: UUID
    bot_id: UUID
    folder_labels: Optional[List[str]] = Field(default=None, description="Folders/labels to monitor")
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    priority: int = 100
    is_active: bool = True


class EmailRuleUpdate(BaseModel):
    bot_id: Optional[UUID] = None
    folder_labels: Optional[List[str]] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class EmailRuleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    integration_id: UUID
    bot_id: UUID
    folder_labels: Optional[List[str]] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'tenant_id', 'user_id', 'integration_id', 'bot_id')
    def serialize_uuid(self, value: UUID):
        return str(value)


class ReorderRequest(BaseModel):
    # ordered list of rule IDs in desired priority order (index => priority)
    ordered_ids: List[UUID]


class ToggleResponse(BaseModel):
    id: UUID
    is_active: bool


class EmailSampleRequest(BaseModel):
    subject: str
    body: str
    sender: Optional[str] = None
    folder: Optional[str] = None
    labels: Optional[List[str]] = None


class EmailSampleResult(BaseModel):
    matched: bool
    rule_id: Optional[UUID] = None
    explanation: str


# Monitoring telemetry schemas (Story 6.3 Tasks 6-7)
class MonitoringStatusResponse(BaseModel):
    integration_id: UUID
    is_paused: bool
    last_poll_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    next_poll_at: Optional[datetime] = None
    error_count: int

    model_config = ConfigDict(from_attributes=True)


class MonitoringPauseRequest(BaseModel):
    is_paused: bool
