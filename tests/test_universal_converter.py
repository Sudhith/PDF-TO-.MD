"""
Universal Multi-Format Ingestion Test Suite
Validates conversion for DOCX, CSV, HTML, and Plain Text into Antigravity Markdown.
"""

import sys
from pathlib import Path
import pytest
import docx

# Ensure root directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aerodoc.config import ConversionConfig
from aerodoc.core.universal_converter import UniversalConverter


@pytest.fixture
def sample_docx(tmp_path) -> Path:
    """Generates a synthetic test DOCX document with headings, tables, and bold runs."""
    doc_path = tmp_path / "executive_report.docx"
    doc = docx.Document()
    
    # Title & Heading
    doc.add_heading("Global Investment Strategy", level=1)
    
    # Paragraph with formatting
    p = doc.add_paragraph("This document details ")
    run = p.add_run("portfolio allocations")
    run.bold = True
    p.add_run(" across emerging markets.")

    # Callout
    doc.add_paragraph("Note: Rebalance threshold must remain within 5% variance.")

    # Table
    table = doc.add_table(rows=3, cols=3)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Asset Class"
    hdr_cells[1].text = "Target Weight"
    hdr_cells[2].text = "Risk Profile"

    row1 = table.rows[1].cells
    row1[0].text = "Equities"
    row1[1].text = "45%"
    row1[2].text = "High"

    row2 = table.rows[2].cells
    row2[0].text = "Fixed Income"
    row2[1].text = "35%"
    row2[2].text = "Moderate"

    doc.save(str(doc_path))
    return doc_path


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    """Generates a synthetic CSV data table."""
    csv_path = tmp_path / "telemetry_metrics.csv"
    csv_content = (
        "Server,Region,Uptime,P99_Latency\n"
        "us-east-1a,Virginia,99.99%,12ms\n"
        "eu-west-1b,Ireland,99.95%,18ms\n"
        "ap-south-1a,Mumbai,99.98%,15ms\n"
    )
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def sample_html(tmp_path) -> Path:
    """Generates a synthetic HTML web page."""
    html_path = tmp_path / "developer_manual.html"
    html_content = """<!DOCTYPE html>
    <html>
    <head><title>System Architecture Guide</title></head>
    <body>
        <h1>API Gateway Architecture</h1>
        <p>The system leverages asynchronous event routing.</p>
        <blockquote>Warning: Always validate authorization headers.</blockquote>
        <table>
            <tr><th>Route</th><th>Method</th><th>Auth</th></tr>
            <tr><td>/api/convert</td><td>POST</td><td>Bearer</td></tr>
        </table>
    </body>
    </html>"""
    html_path.write_text(html_content, encoding="utf-8")
    return html_path


def test_docx_conversion(sample_docx):
    """Verifies that Word (.docx) documents are cleanly converted into Antigravity Markdown."""
    converter = UniversalConverter()
    md, stats = converter.convert(sample_docx)

    assert "# Global Investment Strategy" in md
    assert "**portfolio allocations**" in md
    assert "> [!NOTE]" in md
    assert "| Asset Class | Target Weight | Risk Profile |" in md
    assert "| Equities | 45% | High |" in md
    assert stats["format"] == "Microsoft Word (.docx)"
    assert stats["tables_extracted"] == 1


def test_csv_conversion(sample_csv):
    """Verifies that CSV data files are converted into structured GFM tables."""
    converter = UniversalConverter()
    md, stats = converter.convert(sample_csv)

    assert "| Server | Region | Uptime | P99_Latency |" in md
    assert "| us-east-1a | Virginia | 99.99% | 12ms |" in md
    assert stats["tables_extracted"] == 1


def test_html_conversion(sample_html):
    """Verifies that HTML documents are parsed into structural Markdown."""
    converter = UniversalConverter()
    md, stats = converter.convert(sample_html)

    assert "# API Gateway Architecture" in md
    assert "> [!WARNING]" in md
    assert "| Route | Method | Auth |" in md
    assert stats["format"] == "HTML Document"
