"""
AeroDoc Security & Hardening Layer
Implements magic-byte verification, path traversal defenses, size quotas,
and HTTP security headers.
"""

import re
from pathlib import Path
from typing import Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from aerodoc.exceptions import (
    InvalidPDFMagicByteError,
    OversizedFileError
)


def validate_pdf_stream(data: bytes, max_bytes: int) -> None:
    """
    Validates that the byte payload:
    1. Does not exceed max_bytes.
    2. Begins with the standard '%PDF-' magic byte sequence.
    """
    actual_len = len(data)
    if actual_len > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = actual_len / (1024 * 1024)
        raise OversizedFileError(max_mb=max_mb, actual_mb=actual_mb)

    if actual_len < 5:
        raise InvalidPDFMagicByteError("File is too small to be a valid PDF document.")

    # PDF standard allows the %PDF- header to appear anywhere in the first 1024 bytes
    header_chunk = data[:min(1024, actual_len)]
    if b"%PDF-" not in header_chunk:
        raise InvalidPDFMagicByteError(
            "Missing %PDF- header signature. File is not a valid PDF or has been altered."
        )


def sanitize_filename(raw_name: str) -> str:
    """
    Strips directory separators, null bytes, and path traversal sequences ('..').
    Returns a safe base stem.
    """
    if not raw_name:
        return "document"

    # Extract basename only
    base = Path(raw_name).name
    # Strip null bytes and control chars
    base = base.replace("\x00", "").strip()
    # Remove path traversal tokens
    base = re.sub(r"\.\.+", ".", base)
    # Whitelist alphanumeric, underscore, dash, dot
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", Path(base).stem)
    clean_stem = clean_stem.strip("._")
    return clean_stem if clean_stem else "document"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP security headers into every server response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
