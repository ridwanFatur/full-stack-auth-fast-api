import asyncio
import secrets
import urllib.parse
from dataclasses import dataclass
from typing import Optional

import requests as http_requests
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
    Service responsible for all Google OAuth operations:
    - Building the authorization URL (redirect flow)
    - Exchanging an authorization code for user info (redirect flow)
    - Verifying an ID token directly (token flow)

    All network calls run in a thread pool executor to keep the async event loop free.
    """

    # ------------------------------------------------------------------ #
    #  Auth URL generation                                                  #
    # ------------------------------------------------------------------ #

    def get_auth_url(self) -> tuple[str, str]:
        """
        Build the Google OAuth 2.0 authorization URL and generate a CSRF state token.

        Returns:
            (url, state) — the full authorization URL and the random state string.
        """
        state = secrets.token_hex(32)
        params = urllib.parse.urlencode({
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "select_account",
        })
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
        return url, state

    # ------------------------------------------------------------------ #
    #  Authorization code exchange                                          #
    # ------------------------------------------------------------------ #

    async def exchange_code(self, code: str) -> GoogleUserInfo:
        """
        Exchange a Google authorization code for user info.

        Steps:
          1. POST to Google's token endpoint (server-side; uses GOOGLE_CLIENT_SECRET).
          2. Extract the ID token from the response.
          3. Verify and decode the ID token.
        """
        loop = asyncio.get_running_loop()
        token_data = await loop.run_in_executor(None, self._exchange_code_sync, code)

        google_id_token = token_data.get("id_token")
        if not google_id_token:
            raise ValueError("No ID token returned by Google during code exchange.")

        return await self.verify_id_token(google_id_token)

    def _exchange_code_sync(self, code: str) -> dict:
        """
        Synchronous code→token exchange with Google's token endpoint.
        Intended to be called via run_in_executor.
        """
        response = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if not response.ok:
            raise ValueError(
                f"Google token exchange failed ({response.status_code}): {response.text}"
            )
        return response.json()

    # ------------------------------------------------------------------ #
    #  ID token verification                                               #
    # ------------------------------------------------------------------ #

    async def verify_id_token(self, token: str) -> GoogleUserInfo:
        """
        Verify a Google ID token and extract user information.
        Runs synchronous verification in a thread pool to avoid blocking the event loop.
        """
        loop = asyncio.get_running_loop()
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
