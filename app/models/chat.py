import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampSoftDeleteMixin

if TYPE_CHECKING:
    from app.models.chat_message import ChatMessage
    from app.models.user import User


class Chat(Base, TimestampSoftDeleteMixin):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="New Chat",
    )

    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat",
        order_by="ChatMessage.created_at",
        lazy="select",
    )
