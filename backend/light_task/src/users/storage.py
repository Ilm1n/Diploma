from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.config import settings
from src.s3 import S3Client, get_s3_client


class AvatarStorageError(Exception):
    pass


class AvatarStorageGateway:
    def __init__(self, s3_client: S3Client) -> None:
        self._s3_client = s3_client

    async def upload_file(
        self,
        *,
        file_data: bytes,
        object_name: str,
        content_type: str,
    ) -> str:
        try:
            return await self._s3_client.upload_file(
                file_data=file_data,
                object_name=object_name,
                content_type=content_type,
            )
        except Exception as exc:
            raise AvatarStorageError() from exc

    async def delete_file(self, object_name: str) -> None:
        await self._s3_client.delete_file(object_name)

    def object_key_from_url(self, url: str | None) -> str | None:
        if not url:
            return None

        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        if (
            settings.s3.bucket_name not in path
            and settings.s3.bucket_name not in parsed.netloc
        ):
            return None

        if path.startswith(settings.s3.bucket_name):
            return path.replace(f"{settings.s3.bucket_name}/", "", 1)

        return None


def get_avatar_storage_gateway(
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
) -> AvatarStorageGateway:
    return AvatarStorageGateway(s3_client)
