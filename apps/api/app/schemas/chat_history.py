from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel


class ChatHistoryItem(BaseModel):
    id: UUID
    bot_id: UUID
    tenant_id: UUID
    role: str
    content: str
    session_id: Optional[str]
    client_message_id: Optional[str]
    answer_id: Optional[UUID]
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    origin: Optional[str] = None
    citations: Optional[List[Any]] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
