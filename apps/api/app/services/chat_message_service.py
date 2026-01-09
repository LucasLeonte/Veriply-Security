"""Service for managing chat message logs."""

import logging
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.chat_message import ChatMessageLog

logger = logging.getLogger(__name__)


class ChatMessageService:
    """Service for managing chat message logs."""

    async def log_message(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[UUID] = None,
        citations: Optional[List[dict]] = None,
        answer_id: Optional[UUID] = None,
        client_message_id: Optional[str] = None,
        origin: Optional[str] = None,
        commit: bool = True,
    ) -> Optional[ChatMessageLog]:
        """
        Log a chat message to the database.
        
        Args:
            db: Database session
            bot_id: ID of the bot
            tenant_id: ID of the tenant
            session_id: Chat session ID
            role: 'user' or 'assistant'
            content: Message content
            user_id: Optional ID of the user (if authenticated)
            citations: Optional list of citations for assistant messages
            answer_id: Optional ID linking to a specific answer/response
            client_message_id: Optional ID provided by client
            origin: Optional origin of the message (e.g. 'widget', 'website')
            commit: Whether to commit the transaction (default True)
            
        Returns:
            Created ChatMessageLog entry or None if failed
        """
        try:
            message = ChatMessageLog(
                id=uuid4(),
                tenant_id=tenant_id,
                bot_id=bot_id,
                user_id=user_id,
                session_id=session_id,
                role=role,
                content=content,
                citations=citations,
                answer_id=answer_id,
                client_message_id=client_message_id,
                origin=origin
            )
            
            db.add(message)
            await db.flush()
            
            if commit:
                await db.commit()
            
            logger.debug(
                f"Logged chat message: role={role}, session={session_id}, bot={bot_id}"
            )
            return message
            
        except Exception as e:
            logger.error(f"Failed to log chat message: {e}")
            try:
                # If flush/commit failed, we should rollback to keep session usable
                await db.rollback()
            except Exception:
                pass
            return None
