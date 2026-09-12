"""
AeroDoc Web Studio Server
FastAPI backend providing high-throughput conversion, live page rendering,
rate limiting, security middleware, exception handlers, unique dynamic filenames,
and immediate ephemeral post-download cleanup.
"""

import os
import shutil
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import tempfile
import zipfile

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF

from aerodoc.config import ConversionConfig
from aerodoc.core.converter import PDFConverter
from aerodoc.exceptions import (
    AeroDocBaseException,
    RateLimitExceededError,
    InvalidPDFMagicByteError,
    OversizedFileError,
    EncryptedPDFError,
    CorruptedPDFError
)
from aerodoc.security import SecurityHeadersMiddleware, sanitize_filename
from aerodoc.web.rate_limiter import RateLimitMiddleware
from tests.generate_test_pdf import generate_benchmark_pdf

logger = logging.getLogger("aerodoc.server")

app = FastAPI(
    title="AeroDoc Studio Engine",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# Attach Security and Rate Limiting Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, conversion_limit=15, general_limit=60, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(AeroDocBaseException)
async def aerodoc_exception_handler(request: Request, exc: AeroDocBaseException):
    logger.warning(f"AeroDocException [{exc.error_code}]: {exc.message}")
    return JSONResponse(status_code=exc.http_status, content=exc.to_dict())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            }
        }
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during processing. Please verify your document.",
                "details": {"error_type": type(exc).__name__}
            }
        }
    )


# Base temporary directory for active sessions
SESSIONS_ROOT = Path(tempfile.gettempdir()) / "aerodoc_sessions"
SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)

# In-memory session registry
SESSIONS = {}


def secure_wipe_path(path: Path):
    """Immediately zeroes and purges the file or directory after download."""
    try:
        if path.is_file():
            try:
                path.write_bytes(b"")
            except Exception:
                pass
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


@app.post("/api/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    embed_images: bool = Form(True),
    include_frontmatter: bool = Form(True),
    detect_tables: bool = Form(True),
    detect_math: bool = Form(True),
    detect_callouts: bool = Form(True),
    unroll_columns: bool = Form(True)
):
    """
    Accepts PDF upload, verifies magic bytes, generates layout-aware Antigravity Markdown,
    assigns a unique download token and filename.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents (.pdf) are supported.")

    session_id = uuid.uuid4().hex
    session_dir = SESSIONS_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    input_pdf_path = session_dir / "input.pdf"
    
    # Read uploaded PDF
    content = await file.read()
    input_pdf_path.write_bytes(content)

    # Sanitize file name base to prevent path traversal
    safe_stem = sanitize_filename(Path(file.filename).stem)

    # Generate unique filename with timestamp and random cryptographic token
    unique_suffix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:6]}"
    unique_md_filename = f"{safe_stem}_{unique_suffix}.md"
    unique_zip_filename = f"{safe_stem}_{unique_suffix}_bundle.zip"

    output_md_path = session_dir / unique_md_filename
    assets_dir = session_dir / "assets"

    config = ConversionConfig(
        extract_images=True,
        embed_images=embed_images,
        include_frontmatter=include_frontmatter,
        detect_tables=detect_tables,
        detect_math=detect_math,
        detect_callouts=detect_callouts,
        unroll_columns=unroll_columns,
        output_path=output_md_path,
        assets_path=assets_dir
    )

    converter = PDFConverter(config)
    markdown_content, stats = converter.convert_file(
        pdf_path=input_pdf_path,
        output_path=output_md_path,
        assets_path=assets_dir
    )

    # Word count and reading time calculation
    word_count = len(markdown_content.split())
    reading_time_min = max(1, round(word_count / 200))

    # Pre-generate ZIP package if assets were saved to disk
    zip_path = None
    if assets_dir.exists() and any(assets_dir.iterdir()):
        zip_path = session_dir / unique_zip_filename
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_f:
            zip_f.write(output_md_path, arcname=unique_md_filename)
            for asset_file in assets_dir.rglob("*"):
                if asset_file.is_file():
                    arcname = f"assets/{asset_file.name}"
                    zip_f.write(asset_file, arcname=arcname)

    # Store in registry
    SESSIONS[session_id] = {
        "md_path": output_md_path,
        "zip_path": zip_path,
        "pdf_path": input_pdf_path,
        "session_dir": session_dir,
        "md_filename": unique_md_filename,
        "zip_filename": unique_zip_filename,
        "total_pages": stats["pages"]
    }

    return JSONResponse({
        "success": True,
        "sessionId": session_id,
        "uniqueFilename": unique_md_filename,
        "uniqueZipFilename": unique_zip_filename if zip_path else None,
        "markdown": markdown_content,
        "stats": {
            **stats,
            "word_count": word_count,
            "reading_time_minutes": reading_time_min
        }
    })


@app.get("/api/sample")
async def load_sample_document():
    """
    Generates and processes a benchmark sample PDF on demand for 1-click instant testing.
    """
    session_id = uuid.uuid4().hex
    session_dir = SESSIONS_ROOT / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    input_pdf_path = session_dir / "quantum_benchmark.pdf"
    generate_benchmark_pdf(input_pdf_path)

    unique_suffix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:6]}"
    unique_md_filename = f"quantum_benchmark_{unique_suffix}.md"
    output_md_path = session_dir / unique_md_filename

    config = ConversionConfig(
        extract_images=True,
        embed_images=True,
        output_path=output_md_path
    )
    converter = PDFConverter(config)
    markdown_content, stats = converter.convert_file(input_pdf_path, output_path=output_md_path)

    word_count = len(markdown_content.split())
    reading_time_min = max(1, round(word_count / 200))

    SESSIONS[session_id] = {
        "md_path": output_md_path,
        "zip_path": None,
        "pdf_path": input_pdf_path,
        "session_dir": session_dir,
        "md_filename": unique_md_filename,
        "zip_filename": None,
        "total_pages": stats["pages"]
    }

    return JSONResponse({
        "success": True,
        "sessionId": session_id,
        "uniqueFilename": unique_md_filename,
        "uniqueZipFilename": None,
        "markdown": markdown_content,
        "stats": {
            **stats,
            "word_count": word_count,
            "reading_time_minutes": reading_time_min
        }
    })


@app.get("/api/download/md/{session_id}")
async def download_markdown(session_id: str, background_tasks: BackgroundTasks):
    """
    Streams the converted .md file with its unique filename and
    immediately zeroes and purges the file on the server.
    """
    session = SESSIONS.get(session_id)
    if not session or not session["md_path"].exists():
        raise HTTPException(status_code=404, detail="File has expired or was already purged.")

    md_path: Path = session["md_path"]
    filename = session["md_filename"]

    # Schedule immediate post-transmission purge
    background_tasks.add_task(secure_wipe_path, md_path)

    return FileResponse(
        path=str(md_path),
        media_type="text/markdown; charset=utf-8",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/download/zip/{session_id}")
async def download_bundle_zip(session_id: str, background_tasks: BackgroundTasks):
    """
    Streams the bundle ZIP file with unique filename and
    immediately zeroes and purges it from disk after transmission.
    """
    session = SESSIONS.get(session_id)
    if not session or not session.get("zip_path") or not session["zip_path"].exists():
        raise HTTPException(status_code=404, detail="Bundle file has expired or was already purged.")

    zip_path: Path = session["zip_path"]
    filename = session["zip_filename"]

    # Schedule immediate post-transmission purge
    background_tasks.add_task(secure_wipe_path, zip_path)

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/page-preview/{session_id}/{page_num}")
async def get_page_preview(session_id: str, page_num: int):
    """Renders a specific page of the PDF as a high-definition PNG preview."""
    session = SESSIONS.get(session_id)
    if not session or not session["pdf_path"].exists():
        raise HTTPException(status_code=404, detail="PDF session expired.")

    try:
        doc = fitz.open(session["pdf_path"])
        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=400, detail="Invalid page number.")

        page = doc[page_num - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img_bytes = pix.tobytes("png")
        doc.close()

        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static directory
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
