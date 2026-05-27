"""
StorageService — wraps Supabase Storage for file uploads.

File uploads (e.g. company logos, employee photos) are stored in Supabase Storage.
Configure SUPABASE_URL and SUPABASE_KEY in .env to enable uploads.
If either value is absent the service raises a clear error.
"""
import uuid
from typing import Optional

from app.core.config import settings


class StorageService:
    """
    Upload files to Supabase Storage and return public URLs.
    All synchronous Supabase SDK calls are run in a thread-pool executor
    to avoid blocking the async event loop.
    """

    def __init__(self) -> None:
        self._client: Optional[object] = None

    def _get_client(self):  # type: ignore[return]
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env to enable file uploads."
            )
        if self._client is None:
            try:
                from supabase import create_client  # type: ignore[import]

                self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except ImportError as exc:
                raise ImportError(
                    "supabase package is required for file uploads. "
                    "Run: uv add supabase"
                ) from exc
        return self._client

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> str:
        """
        Upload *file_bytes* to Supabase Storage and return its public URL.

        The remote path is ``{folder}/{uuid4}_{filename}``.
        """
        import asyncio

        bucket = settings.SUPABASE_STORAGE_BUCKET
        remote_name = f"{folder}/{uuid.uuid4()}_{filename}"

        def _upload() -> str:
            client = self._get_client()
            client.storage.from_(bucket).upload(  # type: ignore[attr-defined]
                path=remote_name,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            public_url: str = client.storage.from_(bucket).get_public_url(remote_name)  # type: ignore[attr-defined]
            return public_url

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _upload)

    async def delete_file(self, file_url: str) -> None:
        """
        Delete a file from Supabase Storage by its public URL.
        Silently ignores errors (best-effort cleanup).
        """
        import asyncio

        bucket = settings.SUPABASE_STORAGE_BUCKET

        # Extract the path after the bucket name
        try:
            marker = f"/storage/v1/object/public/{bucket}/"
            path = file_url.split(marker, 1)[1]
        except (IndexError, ValueError):
            return

        def _delete() -> None:
            try:
                client = self._get_client()
                client.storage.from_(bucket).remove([path])  # type: ignore[attr-defined]
            except Exception:
                pass  # best-effort

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _delete)
