from app.exception.CustomException import (
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
)

# Maximum file upload limit: 100 MB
MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024  # 104,857,600 bytes

ALLOWED_MIME_EXTENSIONS = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "flac": "audio/flac",
}


def detect_audio_video_mime(content: bytes) -> str | None:
    """Detects audio or video MIME type based on binary magic bytes inspection."""
    if len(content) < 4:
        return None

    # MP3 (ID3 tag or MPEG sync word)
    if content.startswith(b"ID3") or (
        len(content) >= 2 and content[0] == 0xFF and (content[1] & 0xE0) == 0xE0
    ):
        return "audio/mpeg"

    # WAV (RIFF + WAVE)
    if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WAVE":
        return "audio/wav"

    # OGG (OggS)
    if content.startswith(b"OggS"):
        return "audio/ogg"

    # FLAC (fLaC)
    if content.startswith(b"fLaC"):
        return "audio/flac"

    # WebM / Matroska (\x1a\x45\xdf\xa3)
    if content.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm"

    # MP4 / M4A / MOV container (ftyp at offset 4)
    if len(content) >= 12 and content[4:8] in (b"ftyp", b"moov"):
        ftyp_brand = content[8:12]
        if ftyp_brand in (b"M4A ", b"M4B ", b"m4a "):
            return "audio/mp4"
        return "video/mp4"

    return None


def validate_audio_video_upload(
    filename: str,
    content: bytes,
    max_size: int = MAX_UPLOAD_SIZE_BYTES,
) -> str:
    """Validates file upload payload size and binary magic bytes.

    Raises:
        PayloadTooLargeException: If file size exceeds max_size.
        UnsupportedMediaTypeException: If binary signature does not match supported audio/video types.

    Returns:
        Detected MIME type string.
    """
    if len(content) > max_size:
        max_mb = max_size // (1024 * 1024)
        raise PayloadTooLargeException(
            f"File size ({len(content) / (1024 * 1024):.1f} MB) exceeds maximum limit of {max_mb} MB."
        )

    mime_type = detect_audio_video_mime(content)
    if not mime_type:
        ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
        raise UnsupportedMediaTypeException(
            f"File '{filename}' ({ext}) is not a valid audio/video recording format. Supported formats: MP3, WAV, OGG, M4A, MP4, WebM, FLAC."
        )

    return mime_type
