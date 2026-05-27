import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_refresh_token
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import GoogleAuthUrlResponse, RefreshTokenResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services.google_oauth_service import GoogleOAuthService, GoogleUserInfo
from app.services.jwt_service import JWTService


class AuthService:
    """
    Service responsible for authentication business logic.
    Orchestrates Google OAuth verification, user management, and JWT generation.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.google_service = GoogleOAuthService()
        self.jwt_service = JWTService(db)

    # ------------------------------------------------------------------ #
    #  Google OAuth — auth URL                                             #
    # ------------------------------------------------------------------ #

    def get_google_auth_url(self) -> GoogleAuthUrlResponse:
        """
        Generate the Google OAuth authorization URL and a CSRF state token.
        The caller (Next.js route handler) stores the state in an httpOnly cookie.
        """
        url, state = self.google_service.get_auth_url()
        return GoogleAuthUrlResponse(url=url, state=state)

    # ------------------------------------------------------------------ #
    #  Google OAuth — token flows                                          #
    # ------------------------------------------------------------------ #

    async def google_login(self, id_token: str) -> TokenResponse:
        """
        Authenticate via a Google ID token (e.g. popup / direct token flow).
        """
        google_user = await self.google_service.verify_id_token(id_token)
        return await self._authenticate_google_user(google_user)

    async def google_callback(self, code: str) -> TokenResponse:
        """
        Authenticate via a Google authorization code (redirect flow).
        Exchanges the code server-side; never exposes GOOGLE_CLIENT_SECRET.
        """
        google_user = await self.google_service.exchange_code(code)
        return await self._authenticate_google_user(google_user)

    # ------------------------------------------------------------------ #
    #  Shared authentication logic                                         #
    # ------------------------------------------------------------------ #

    async def _authenticate_google_user(self, google_user: GoogleUserInfo) -> TokenResponse:
        """
        Find or create a user from verified Google identity, issue JWT tokens.
        """
        user = await self.user_repo.get_by_google_id(google_user.google_id)

        if not user:
            user = await self.user_repo.create(
                google_id=google_user.google_id,
                email=google_user.email,
                full_name=google_user.full_name,
                profile_picture=None,  # do not import Google profile picture
            )

        user = await self.user_repo.update_last_login(user)
        access_token, refresh_token = await self.jwt_service.generate_tokens(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            user=UserResponse.model_validate(user),
        )

    # ------------------------------------------------------------------ #
    #  Token refresh + logout                                              #
    # ------------------------------------------------------------------ #

    async def refresh_access_token(self, refresh_token: str) -> RefreshTokenResponse:
        """
        Validate refresh token, revoke it, and issue a new access + refresh token pair.
        Implements token rotation for security.
        """
        user_id_str = verify_refresh_token(refresh_token)
        if not user_id_str:
            raise ValueError("Invalid refresh token")

        stored_token = await self.refresh_token_repo.get_by_token(refresh_token)
        if not stored_token:
            raise ValueError("Refresh token not found or already revoked")

        if stored_token.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token has expired")

        await self.refresh_token_repo.revoke(stored_token)

        user = await self.user_repo.get_by_id(uuid.UUID(user_id_str))
        if not user:
            raise ValueError("User not found")

        new_access_token, new_refresh_token = await self.jwt_service.generate_tokens(user)

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
        )

    async def logout(self, refresh_token: str) -> None:
        """
        Revoke the provided refresh token, ending the session.
        """
        stored_token = await self.refresh_token_repo.get_by_token(refresh_token)
        if stored_token:
            await self.refresh_token_repo.revoke(stored_token)
