from fastapi import UploadFile

from app.application.errors import FileTooLargeError

_CHUNK_SIZE = 1024 * 1024


async def read_upload_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Read an uploaded file into memory, refusing to read past ``max_bytes``."""
    buffer = bytearray()
    while chunk := await upload.read(_CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLargeError(max_bytes)
    return bytes(buffer)
