"""
Security, Exception Hierarchy, and Rate Limiter Verification Suite
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import io

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aerodoc.security import validate_pdf_stream, sanitize_filename
from aerodoc.exceptions import (
    InvalidPDFMagicByteError,
    OversizedFileError,
    EncryptedPDFError
)
from aerodoc.web.server import app
from aerodoc.web.rate_limiter import SlidingWindowRateLimiter
from tests.generate_test_pdf import generate_benchmark_pdf


def test_magic_byte_validation():
    """Ensures non-PDF payloads are rejected immediately."""
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00SomeExecutablePayload"
    with pytest.raises(InvalidPDFMagicByteError):
        validate_pdf_stream(fake_exe, max_bytes=1024*1024)

    fake_text = b"This is just plain text, not a PDF."
    with pytest.raises(InvalidPDFMagicByteError):
        validate_pdf_stream(fake_text, max_bytes=1024*1024)

    # Valid PDF signature
    valid_pdf_start = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n" + b"x" * 100
    validate_pdf_stream(valid_pdf_start, max_bytes=1024*1024)  # Should not raise


def test_oversized_file_rejection():
    """Ensures files exceeding the byte ceiling are rejected."""
    payload = b"%PDF-1.5\n" + b"0" * 200
    # Set max ceiling to 100 bytes
    with pytest.raises(OversizedFileError) as exc_info:
        validate_pdf_stream(payload, max_bytes=100)
    assert exc_info.value.http_status == 413


def test_path_traversal_sanitization():
    """Verifies that malicious directory traversal filenames are neutralized."""
    assert sanitize_filename("../../../secret.pdf") == "secret"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.pdf") == "calc"
    assert sanitize_filename("normal_paper.pdf") == "normal_paper"
    assert sanitize_filename("") == "document"


def test_sliding_window_rate_limiter():
    """Verifies that the rate limiter throttles excessive requests."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
    client_ip = "192.168.1.50"

    # First 3 should pass
    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True
    assert limiter.is_allowed(client_ip)[0] is True

    # 4th should be blocked with retry-after > 0
    allowed, retry_after = limiter.is_allowed(client_ip)
    assert allowed is False
    assert retry_after > 0


def test_api_invalid_pdf_rejection():
    """Tests that the FastAPI endpoint returns structured JSON error on invalid PDF bytes."""
    client = TestClient(app)
    fake_data = io.BytesIO(b"Not a real PDF file")
    resp = client.post(
        "/api/convert",
        files={"file": ("malicious.pdf", fake_data, "application/pdf")}
    )
    assert resp.status_code == 415
    json_data = resp.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "INVALID_PDF_SIGNATURE"


def test_api_sample_endpoint():
    """Tests that the /api/sample endpoint generates and converts the sample document."""
    client = TestClient(app)
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "quantum_benchmark" in data["uniqueFilename"]
    assert data["stats"]["pages"] == 2
    assert "Operational Telemetry Matrix" in data["markdown"]
