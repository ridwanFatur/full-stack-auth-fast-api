import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the authenticated user's profile information."""
    return current_user  # type: ignore[return-value]


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Upload or replace the user's profile picture. Stored in Supabase Storage."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are accepted.",
        )
    storage = StorageService()
    try:
        file_bytes = await file.read()
        url = await storage.upload_file(
            file_bytes=file_bytes,
            filename=file.filename or "avatar",
            content_type=file.content_type,
            folder="avatars",
        )
        user_repo = UserRepository(db)
        updated = await user_repo.update_profile_picture(current_user, url)
        return updated  # type: ignore[return-value]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Retrieve a user by their UUID. Requires authentication."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user  # type: ignore[return-value]
