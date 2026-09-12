"""
AeroDoc Exception Hierarchy
Provides structured, typed error classes with machine-readable error codes
and actionable human-readable messages.
"""

from typing import Optional, Dict, Any


class AeroDocBaseException(Exception):
    """Base exception for all AeroDoc engine and service errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "AERODOC_GENERAL_ERROR",
        http_status: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes exception for JSON API responses."""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class InvalidPDFMagicByteError(AeroDocBaseException):
    """Raised when uploaded file lacks the required %PDF- signature."""

    def __init__(self, message: str = "Invalid PDF signature. File is not a valid PDF document.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_PDF_SIGNATURE",
            http_status=415,
            details=details
        )


class OversizedFileError(AeroDocBaseException):
    """Raised when an uploaded document exceeds the maximum permitted byte ceiling."""

    def __init__(self, max_mb: float, actual_mb: float):
        super().__init__(
            message=f"File exceeds maximum allowed upload size of {max_mb:.1f} MB (received {actual_mb:.1f} MB).",
            error_code="FILE_TOO_LARGE",
            http_status=413,
            details={"max_mb": max_mb, "actual_mb": actual_mb}
        )


class EncryptedPDFError(AeroDocBaseException):
    """Raised when the PDF document is password-protected or encrypted."""

    def __init__(self, message: str = "Document is encrypted or password-protected. Please decrypt before conversion."):
        super().__init__(
            message=message,
            error_code="PDF_ENCRYPTED",
            http_status=422
        )


class CorruptedPDFError(AeroDocBaseException):
    """Raised when the PDF parser encounters structural corruption or unrecoverable EOF."""

    def __init__(self, message: str = "The PDF file is malformed or corrupted and cannot be parsed."):
        super().__init__(
            message=message,
            error_code="PDF_CORRUPTED",
            http_status=400
        )


class RateLimitExceededError(AeroDocBaseException):
    """Raised when a client IP exceeds request or conversion quotas."""

    def __init__(self, retry_after: int, quota_type: str = "conversions"):
        super().__init__(
            message=f"Rate limit exceeded for {quota_type}. Please retry after {retry_after} seconds.",
            error_code="RATE_LIMIT_EXCEEDED",
            http_status=429,
            details={"retry_after_seconds": retry_after, "quota_type": quota_type}
        )


class ExtractionError(AeroDocBaseException):
    """Raised when an internal extraction subsystem fails on malformed elements."""

    def __init__(self, subsystem: str, detail: str):
        super().__init__(
            message=f"Extraction failure in {subsystem}: {detail}",
            error_code="EXTRACTION_FAILED",
            http_status=500,
            details={"subsystem": subsystem, "internal_detail": detail}
        )
