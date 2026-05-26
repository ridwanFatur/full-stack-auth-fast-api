from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthUrlResponse,
    GoogleCallbackRequest,
    GoogleLoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.services.google_oauth_service import GoogleOAuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/auth-url", response_model=GoogleAuthUrlResponse)
async def google_auth_url() -> GoogleAuthUrlResponse:
    """
    Generate the Google OAuth authorization URL and a CSRF state token.

    The Next.js route handler stores the state in an httpOnly cookie and
    redirects the browser to the returned URL.  All Google credentials stay
    on the backend; nothing sensitive is sent to the browser.

    This endpoint requires no authentication and no database access.
    """
    url, state = GoogleOAuthService().get_auth_url()
    return GoogleAuthUrlResponse(url=url, state=state)


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(
    request: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Exchange a Google authorization code for JWT tokens (redirect-based OAuth flow).

    The Next.js route handler verifies the CSRF state cookie before calling this
    endpoint and then forwards only the authorization code.
    GOOGLE_CLIENT_SECRET is used here and never leaves the backend.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.google_callback(request.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/google/login", response_model=TokenResponse)
async def google_login(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user using a Google ID token (direct token flow).
    Creates a new user account if one does not exist.
    Returns JWT access and refresh tokens.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.google_login(request.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """
    Generate a new access token using a valid refresh token.
    Rotates the refresh token for security.
    """
    auth_service = AuthService(db)
    try:
        return await auth_service.refresh_access_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Revoke the provided refresh token, ending the user session.
    Requires a valid access token for authentication.
    """
    auth_service = AuthService(db)
    await auth_service.logout(request.refresh_token)
    return {"message": "Logged out successfully"}
