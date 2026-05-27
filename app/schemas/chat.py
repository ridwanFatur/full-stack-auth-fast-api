import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
#  Request schemas                                                      #
# ------------------------------------------------------------------ #


class ChatCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=500)


class ChatUpdate(BaseModel):
    title: str = Field(max_length=500)


# ------------------------------------------------------------------ #
#  Response schemas                                                     #
# ------------------------------------------------------------------ #


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    items: List[ChatResponse]
    total: int


class ChatDetailResponse(ChatResponse):
    messages: List[ChatMessageResponse] = []
