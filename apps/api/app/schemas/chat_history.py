from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class ChatHistoryItem(BaseModel):
    id: str
    bot_id: str
    tenant_id: str
    role: str
    content: str
    session_id: Optional[str]
    client_message_id: Optional[str]
    answer_id: Optional[str]
    citations: List[Any]
    created_at: datetime

    class Config:
        orm_mode = True
