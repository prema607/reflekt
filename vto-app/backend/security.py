from fastapi import HTTPException

MAX_BYTES = 10 * 1024 * 1024
MAGIC = (b"\xff\xd8\xff", b"\x89PNG", b"RIFF")  # JPEG, PNG, WebP

def verify_image(data: bytes):
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image exceeds 10MB")
    if not data.startswith(MAGIC):  # magic bytes, not the client's header
        raise HTTPException(415, "Only JPEG/PNG/WebP allowed")
