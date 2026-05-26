import asyncio
from dataclasses import dataclass
from typing import Optional

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings


@dataclass
class GoogleUserInfo:
    google_id: str
    email: str
    full_name: str
    profile_picture: Optional[str]


class GoogleOAuthService:
    """
    Service responsible for verifying Google ID tokens.
    Token verification is performed server-side using google-auth library.
    """

    async def verify_id_token(self, token: str) -> GoogleUserInfo:
        """
        Verify Google ID token and extract user information.
        Runs synchronous verification in a thread pool to avoid blocking the event loop.
        """
        loop = asyncio.get_event_loop()
        id_info = await loop.run_in_executor(None, self._verify_token_sync, token)
        return GoogleUserInfo(
            google_id=id_info["sub"],
            email=id_info["email"],
            full_name=id_info.get("name", ""),
            profile_picture=id_info.get("picture"),
        )

    def _verify_token_sync(self, token: str) -> dict:
        try:
            return id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            raise ValueError(f"Invalid Google ID token: {e}")
