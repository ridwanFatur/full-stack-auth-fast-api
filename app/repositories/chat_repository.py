import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat
from app.models.chat_message import ChatMessage
from app.schemas.chat import ChatCreate, ChatUpdate


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------ #
    #  Chat queries                                                         #
    # ------------------------------------------------------------------ #

    async def get_by_id(self, chat_id: uuid.UUID) -> Optional[Chat]:
        result = await self.db.execute(
            select(Chat).where(Chat.id == chat_id, Chat.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Chat]:
        """Return chat only if it belongs to the given user."""
        result = await self.db.execute(
            select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
                Chat.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_with_messages(
        self, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Chat]:
        """Return chat with all non-deleted messages eagerly loaded."""
        result = await self.db.execute(
            select(Chat)
            .options(selectinload(Chat.messages))
            .where(
                Chat.id == chat_id,
                Chat.user_id == user_id,
                Chat.is_deleted == False,
            )
        )
        chat = result.scalar_one_or_none()
        if chat:
            # Filter out soft-deleted messages in Python
            chat.messages = [m for m in chat.messages if not m.is_deleted]
        return chat

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Chat], int]:
        from sqlalchemy import func

        base_query = select(Chat).where(
            Chat.user_id == user_id, Chat.is_deleted == False
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total: int = count_result.scalar_one()
        result = await self.db.execute(
            base_query.order_by(Chat.updated_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    # ------------------------------------------------------------------ #
    #  Chat mutations                                                       #
    # ------------------------------------------------------------------ #

    async def create(self, user_id: uuid.UUID, data: ChatCreate) -> Chat:
        chat = Chat(user_id=user_id, **data.model_dump())
        self.db.add(chat)
        await self.db.flush()
        await self.db.refresh(chat)
        return chat

    async def update(self, chat: Chat, data: ChatUpdate) -> Chat:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(chat, field, value)
        await self.db.flush()
        await self.db.refresh(chat)
        return chat

    async def soft_delete(self, chat: Chat) -> None:
        chat.is_deleted = True
        chat.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def touch_updated_at(self, chat: Chat) -> None:
        """Bump updated_at so the chat surfaces at the top of the list."""
        chat.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    # ------------------------------------------------------------------ #
    #  Message mutations                                                    #
    # ------------------------------------------------------------------ #

    async def add_message(
        self, chat_id: uuid.UUID, role: str, content: str
    ) -> ChatMessage:
        msg = ChatMessage(chat_id=chat_id, role=role, content=content)
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    async def get_messages(
        self, chat_id: uuid.UUID, limit: int = 50
    ) -> Sequence[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.chat_id == chat_id,
                ChatMessage.is_deleted == False,
            )
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
