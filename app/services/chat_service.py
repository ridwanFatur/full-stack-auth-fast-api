import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatCreate,
    ChatDetailResponse,
    ChatListResponse,
    ChatMessageResponse,
    ChatResponse,
    ChatUpdate,
)


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ChatRepository(db)

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    async def list_chats(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> ChatListResponse:
        items, total = await self.repo.list_by_user(user_id, skip=skip, limit=limit)
        return ChatListResponse(
            items=[ChatResponse.model_validate(c) for c in items],
            total=total,
        )

    async def get_chat(
        self, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatDetailResponse:
        chat = await self.repo.get_with_messages(chat_id, user_id)
        if not chat:
            raise ValueError("Chat not found or access denied.")
        return ChatDetailResponse(
            id=chat.id,
            user_id=chat.user_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            messages=[ChatMessageResponse.model_validate(m) for m in chat.messages],
        )

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    async def create_chat(
        self, user_id: uuid.UUID, data: ChatCreate
    ) -> ChatResponse:
        chat = await self.repo.create(user_id, data)
        return ChatResponse.model_validate(chat)

    async def rename_chat(
        self, chat_id: uuid.UUID, user_id: uuid.UUID, data: ChatUpdate
    ) -> ChatResponse:
        chat = await self.repo.get_by_id_and_user(chat_id, user_id)
        if not chat:
            raise ValueError("Chat not found or access denied.")
        chat = await self.repo.update(chat, data)
        return ChatResponse.model_validate(chat)

    async def delete_chat(
        self, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        chat = await self.repo.get_by_id_and_user(chat_id, user_id)
        if not chat:
            raise ValueError("Chat not found or access denied.")
        await self.repo.soft_delete(chat)
