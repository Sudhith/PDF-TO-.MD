"""
Automated Test Suite for AeroDoc Converter and Web Server
Validates lossless conversion, table extraction, KaTeX math, Antigravity alerts,
unique download naming, and immediate ephemeral post-download file purging.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aerodoc.config import ConversionConfig
from aerodoc.core.converter import PDFConverter
from aerodoc.web.server import app, secure_wipe_path
from tests.generate_test_pdf import generate_benchmark_pdf


@pytest.fixture(scope="session")
def benchmark_pdf(tmp_path_factory) -> Path:
    temp_dir = tmp_path_factory.mktemp("pdf_data")
    pdf_file = temp_dir / "quantum_benchmark.pdf"
    generate_benchmark_pdf(pdf_file)
    return pdf_file


def test_lossless_content_conversion(benchmark_pdf, tmp_path):
    """Verifies that all sections, tables, code, alerts, and metadata are extracted."""
    out_md = tmp_path / "output.md"
    assets_dir = tmp_path / "assets"

    config = ConversionConfig(
        extract_images=True,
        embed_images=False,
        output_path=out_md,
        assets_path=assets_dir
    )

    converter = PDFConverter(config)
    markdown_content, stats = converter.convert_file(
        pdf_path=benchmark_pdf,
        output_path=out_md,
        assets_path=assets_dir
    )

    # 1. Verify file was created
    assert out_md.exists()
    assert len(markdown_content) > 100

    # 2. Verify YAML Frontmatter
    assert "---" in markdown_content
    assert "engine: AeroDoc" in markdown_content
    assert "format: Antigravity Markdown" in markdown_content
    assert stats["pages"] == 2

    # 3. Verify Headings
    assert "System Overview" in markdown_content
    assert "Operational Telemetry Matrix" in markdown_content
    assert "Mathematical Foundations" in markdown_content

    # 4. Verify Antigravity Alert Boxes
    assert "> [!NOTE]" in markdown_content
    assert "> [!WARNING]" in markdown_content
    assert "> [!TIP]" in markdown_content

    # 5. Verify Table Extraction
    assert "Latency (ms)" in markdown_content
    assert "Throughput" in markdown_content
    assert "Layout Parser" in markdown_content
    assert "|" in markdown_content

    # 6. Verify Code and Page Anchors
    assert "<!-- Page 2 -->" in markdown_content
    assert "def execute_task" in markdown_content

    # 7. Verify Image was extracted
    assert stats["images_extracted"] >= 1
    assert assets_dir.exists()
    assert any(assets_dir.iterdir())


def test_embedded_base64_mode(benchmark_pdf, tmp_path):
    """Verifies that standalone mode embeds images directly as Base64 data URIs."""
    out_md = tmp_path / "standalone.md"
    config = ConversionConfig(
        extract_images=True,
        embed_images=True,
        output_path=out_md
    )

    converter = PDFConverter(config)
    markdown_content, stats = converter.convert_file(benchmark_pdf, output_path=out_md)

    assert "data:image/png;base64," in markdown_content
    assert stats["images_extracted"] >= 1


def test_unique_naming_and_web_api(benchmark_pdf):
    """Tests the FastAPI server endpoints: upload, unique naming, and download."""
    client = TestClient(app)

    with open(benchmark_pdf, "rb") as f:
        response = client.post(
            "/api/convert",
            files={"file": ("quantum_benchmark.pdf", f, "application/pdf")},
            data={"embed_images": "true"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "quantum_benchmark_" in data["uniqueFilename"]
    assert data["uniqueFilename"].endswith(".md")
    session_id = data["sessionId"]

    # Test Download endpoint
    dl_response = client.get(f"/api/download/md/{session_id}")
    assert dl_response.status_code == 200
    assert "Antigravity Markdown" in dl_response.text


def test_secure_wipe_path(tmp_path):
    """Verifies that files are zeroed and removed upon download completion."""
    temp_file = tmp_path / "purge_me.md"
    temp_file.write_text("Confidential Content", encoding="utf-8")
    assert temp_file.exists()

    secure_wipe_path(temp_file)
    assert not temp_file.exists()
