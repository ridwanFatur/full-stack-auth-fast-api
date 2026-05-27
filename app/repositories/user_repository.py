import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.google_id == google_id, User.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        google_id: str,
        email: str,
        full_name: str,
        profile_picture: Optional[str] = None,
    ) -> User:
        user = User(
            google_id=google_id,
            email=email,
            full_name=full_name,
            profile_picture=profile_picture,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_profile_picture(self, user: User, url: Optional[str]) -> User:
        user.profile_picture = url
        await self.db.flush()
        await self.db.refresh(user)
        return user
