import logging
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.core.AppConfig import settings

logger = logging.getLogger(__name__)


class ObjectStorageService:
    """Dual-Mode Object Storage Service supporting Supabase Storage REST & Local Disk Fallback.

    1. Supabase Storage Mode:
       - Uses Supabase Storage REST API with SUPABASE_SERVICE_ROLE_KEY.
       - Stores recordings in SUPABASE_STORAGE_BUCKET (default: 'interview-recordings').
       - Generates presigned URLs for secure browser playback.
    2. Local Disk Fallback Mode:
       - Stores recordings in 'storage/recordings/'.
       - Serves audio via backend streaming endpoint with HTTP 206 Partial Content support.
    """

    def __init__(self) -> None:
        self.supabase_url = settings.effective_supabase_url
        self.service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self.bucket = settings.SUPABASE_STORAGE_BUCKET or "interview-recordings"
        self.local_storage_dir = Path("storage/recordings")
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    async def _ensure_supabase_bucket(self, client: httpx.AsyncClient) -> bool:
        """Ensure Supabase storage bucket exists."""
        if not self.is_supabase_configured:
            return False
        url = f"{self.supabase_url}/storage/v1/bucket"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apiKey": self.service_role_key,
        }
        try:
            # Check if bucket exists
            res = await client.get(f"{url}/{self.bucket}", headers=headers)
            if res.status_code == 200:
                return True
            # Create if not exists
            create_res = await client.post(
                url,
                headers=headers,
                json={"id": self.bucket, "name": self.bucket, "public": False},
            )
            return create_res.status_code in (200, 201)
        except Exception as exc:
            logger.warning("Could not verify/create Supabase bucket: %s", exc)
            return False

    async def upload_audio_file(
        self,
        content: bytes,
        filename: str,
        content_type: str = "audio/mpeg",
    ) -> tuple[str, str]:
        """Uploads audio file to Supabase Storage if configured; otherwise saves to local disk.

        Returns (url_or_path, mode) where mode is 'SUPABASE' or 'LOCAL'.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{filename.replace(' ', '_')}"

        # 1. Attempt Supabase Storage upload
        if self.is_supabase_configured:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await self._ensure_supabase_bucket(client)
                    upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{safe_name}"
                    headers = {
                        "Authorization": f"Bearer {self.service_role_key}",
                        "apiKey": self.service_role_key,
                        "Content-Type": content_type,
                        "x-upsert": "true",
                    }
                    res = await client.post(upload_url, headers=headers, content=content)
                    if res.status_code in (200, 201):
                        logger.info("Successfully uploaded %s to Supabase Storage bucket %s", safe_name, self.bucket)
                        # Generate 7-day presigned URL
                        sign_url = f"{self.supabase_url}/storage/v1/object/sign/{self.bucket}/{safe_name}"
                        sign_res = await client.post(
                            sign_url,
                            headers=headers,
                            json={"expiresIn": 7 * 24 * 3600},
                        )
                        if sign_res.status_code == 200:
                            signed_data = sign_res.json()
                            signed_path = signed_data.get("signedURL")
                            if signed_path:
                                full_signed_url = f"{self.supabase_url}/storage/v1{signed_path}"
                                return full_signed_url, "SUPABASE"
                        # Fallback to direct object URL
                        return f"{self.supabase_url}/storage/v1/object/{self.bucket}/{safe_name}", "SUPABASE"
                    else:
                        logger.warning(
                            "Supabase Storage upload returned status %d: %s. Falling back to local disk.",
                            res.status_code,
                            res.text,
                        )
            except Exception as exc:
                logger.warning("Supabase Storage upload failed: %s. Falling back to local disk.", exc)

        # 2. Local disk fallback
        local_path = self.local_storage_dir / safe_name
        local_path.write_bytes(content)
        logger.info("Saved audio file locally at %s", local_path)
        return str(local_path.as_posix()), "LOCAL"

    def resolve_audio_stream_url(
        self,
        source_url: str | None,
        session_id: int | str,
        token: str | None = None,
    ) -> str:
        """Returns the public or streamable URL for the frontend audio player."""
        if not source_url:
            base = f"/api/v1/interviews/sessions/{session_id}/audio"
            return f"{base}?token={token}" if token else base

        if source_url.startswith(("http://", "https://")):
            return source_url

        # Local file path -> return streaming endpoint
        base = f"/api/v1/interviews/sessions/{session_id}/audio"
        return f"{base}?token={token}" if token else base
