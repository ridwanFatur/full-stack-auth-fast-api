from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository


class JWTService:
    """
    Service responsible for JWT token generation and refresh token persistence.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.refresh_token_repo = RefreshTokenRepository(db)

    async def generate_tokens(self, user: User) -> tuple[str, str]:
        """
        Generate a new access token and refresh token pair.
        Persists the refresh token to the database.
        Returns (access_token, refresh_token).
        """
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.refresh_token_repo.create(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )

        return access_token, refresh_token
