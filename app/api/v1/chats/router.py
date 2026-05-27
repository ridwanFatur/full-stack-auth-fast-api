"""
Chats API
---------
REST endpoints for chat CRUD + WebSocket for real-time streaming AI chat.

WebSocket auth: pass JWT as query param  ?token=<access_token>

Message protocol (JSON):
  Client → Server:  {"message": "user text"}
  Server → Client:  {"type": "chunk",   "content": "token text"}
                    {"type": "done",    "content": "full response", "message_id": "uuid"}
                    {"type": "error",   "detail": "error message"}
"""

import json
import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_access_token
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.user_repository import UserRepository
from app.schemas.chat import (
    ChatCreate,
    ChatDetailResponse,
    ChatListResponse,
    ChatResponse,
    ChatUpdate,
)
from app.services.ai_service import stream_agent_response
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])


# ====================================================================== #
#  REST — Chat CRUD                                                        #
# ====================================================================== #


@router.get("", response_model=ChatListResponse)
async def list_chats(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatListResponse:
    """List all chats for the authenticated user (newest first)."""
    service = ChatService(db)
    return await service.list_chats(current_user.id, skip=skip, limit=limit)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Create a new chat session."""
    service = ChatService(db)
    return await service.create_chat(current_user.id, data)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatDetailResponse:
    """Get a chat with its full message history."""
    service = ChatService(db)
    try:
        return await service.get_chat(chat_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{chat_id}", response_model=ChatResponse)
async def rename_chat(
    chat_id: uuid.UUID,
    data: ChatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Rename a chat session."""
    service = ChatService(db)
    try:
        return await service.rename_chat(chat_id, current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-delete a chat and all its messages."""
    service = ChatService(db)
    try:
        await service.delete_chat(chat_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ====================================================================== #
#  WebSocket — Streaming AI chat                                           #
# ====================================================================== #


@router.websocket("/{chat_id}/ws")
async def chat_websocket(
    chat_id: uuid.UUID,
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
) -> None:
    """
    WebSocket endpoint for streaming AI chat.

    Authentication: pass the JWT access token as query param ?token=<jwt>
    Message flow:
      1. Client sends: {"message": "user text"}
      2. Server sends chunks: {"type": "chunk", "content": "..."}
      3. Server sends done:   {"type": "done", "content": "full text", "message_id": "uuid"}
    """
    from app.core.database import AsyncSessionLocal

    await websocket.accept()

    # ── Auth ──────────────────────────────────────────────────────────── #
    user_id_str = verify_access_token(token)
    if not user_id_str:
        await websocket.send_json({"type": "error", "detail": "Invalid or expired token"})
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        try:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(uuid.UUID(user_id_str))
            if not user or not user.is_active:
                await websocket.send_json({"type": "error", "detail": "User not found or inactive"})
                await websocket.close(code=4001)
                return

            # ── Verify chat ownership ─────────────────────────────────── #
            chat_repo = ChatRepository(db)
            chat = await chat_repo.get_by_id_and_user(chat_id, user.id)
            if not chat:
                await websocket.send_json({"type": "error", "detail": "Chat not found or access denied"})
                await websocket.close(code=4004)
                return

            # ── Main loop ─────────────────────────────────────────────── #
            while True:
                try:
                    raw = await websocket.receive_text()
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected for chat %s", chat_id)
                    break

                # Parse incoming message
                try:
                    payload = json.loads(raw)
                    user_message = payload.get("message", "").strip()
                except (json.JSONDecodeError, AttributeError):
                    await websocket.send_json({"type": "error", "detail": "Invalid JSON payload"})
                    continue

                if not user_message:
                    await websocket.send_json({"type": "error", "detail": "Empty message"})
                    continue

                # Save user message to DB
                await chat_repo.add_message(chat_id, "user", user_message)

                # Load recent history (last 40 messages for context)
                messages = await chat_repo.get_messages(chat_id, limit=40)
                # Exclude the last message (the one we just added) to build history
                history = [
                    (m.role, m.content)
                    for m in messages[:-1]
                ]

                # Stream AI response token by token
                full_response = ""
                try:
                    async for chunk in stream_agent_response(history, user_message):
                        full_response += chunk
                        await websocket.send_json({"type": "chunk", "content": chunk})
                except WebSocketDisconnect:
                    logger.info("Client disconnected mid-stream for chat %s", chat_id)
                    break
                except Exception as exc:
                    logger.error("AI streaming error: %s", exc, exc_info=True)
                    await websocket.send_json({"type": "error", "detail": str(exc)})
                    continue

                # Save assistant response to DB
                if full_response:
                    saved_msg = await chat_repo.add_message(chat_id, "assistant", full_response)
                    await chat_repo.touch_updated_at(chat)
                    await db.commit()

                    # Auto-generate title from first message
                    if chat.title == "New Chat":
                        new_title = user_message[:80]
                        from app.schemas.chat import ChatUpdate as _ChatUpdate
                        await chat_repo.update(chat, _ChatUpdate(title=new_title))
                        await db.commit()

                    await websocket.send_json({
                        "type": "done",
                        "content": full_response,
                        "message_id": str(saved_msg.id),
                        "chat_title": chat.title,
                    })
                else:
                    await websocket.send_json({"type": "done", "content": "", "message_id": None})

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for chat %s", chat_id)
        except Exception as exc:
            logger.error("WebSocket error for chat %s: %s", chat_id, exc, exc_info=True)
            try:
                await websocket.send_json({"type": "error", "detail": "Internal server error"})
            except Exception:
                pass
