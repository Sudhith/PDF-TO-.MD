"""
Generates a rigorous benchmark PDF containing:
- Multi-column technical text
- Formatted tables
- Mathematical formulas (KaTeX compatible)
- Antigravity alerts (Note, Warning, Tip)
- Monospace code listings
- Images/drawings
- Hyperlinks
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw


def create_sample_image(img_path: Path):
    """Creates a sample test diagram image."""
    img = Image.new('RGB', (300, 150), color=(18, 26, 42))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 290, 140], outline=(0, 242, 254), width=3)
    d.text((40, 60), "Antigravity Vector Diagnostic", fill=(240, 244, 248))
    img.save(img_path)


def generate_benchmark_pdf(output_pdf: Path):
    """Builds a multi-page benchmark PDF document."""
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a'),
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=6,
        spaceAfter=10
    )

    elements = []

    # Title & Metadata
    elements.append(Paragraph("Antigravity Quantum Systems Architecture", title_style))
    elements.append(Paragraph("<b>Author:</b> Lead Systems Engineer | <b>Version:</b> 2.4.0", body_style))
    elements.append(Spacer(1, 10))

    # Section 1: Introduction
    elements.append(Paragraph("1. System Overview", h1_style))
    elements.append(Paragraph(
        "The Antigravity agentic engine coordinates multi-modal tasks across distributed environments. "
        "Every operation is verified deterministically to ensure zero synthetic hallucination.",
        body_style
    ))

    # Antigravity Alert 1: Note
    elements.append(Paragraph("Note: High concurrency execution requires persistent memory allocation.", body_style))

    # Table
    elements.append(Paragraph("2. Operational Telemetry Matrix", h1_style))
    table_data = [
        ["Subsystem", "Latency (ms)", "Throughput (ops/s)", "Fault Tolerance"],
        ["Layout Parser", "12.4", "4,200", "99.99%"],
        ["Table Extractor", "18.1", "1,850", "99.95%"],
        ["KaTeX Compiler", "6.2", "9,100", "99.99%"],
        ["Alert Pipeline", "3.0", "15,000", "100.0%"]
    ]
    t = Table(table_data, colWidths=[140, 90, 110, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # Math Equations
    elements.append(Paragraph("3. Mathematical Foundations", h1_style))
    elements.append(Paragraph(
        "Energy density within the gradient field is modeled through the relativistic relation:",
        body_style
    ))
    elements.append(Paragraph(r"E = m * c^2 + \int \psi(x) dx", code_style))

    # Antigravity Alert 2: Warning
    elements.append(Paragraph("Warning: Do not exceed the critical thermal gradient during quantum alignment.", body_style))

    # Page Break for Page 2
    elements.append(PageBreak())

    # Page 2: Code Snippet & Image
    elements.append(Paragraph("4. Implementation Protocol", h1_style))
    elements.append(Paragraph(
        "Below is the core execution hook utilized by Antigravity agents:",
        body_style
    ))
    
    code_text = (
        "def execute_task(task_id: str) -> dict:\n"
        "    context = load_agent_context(task_id)\n"
        "    result = context.dispatch_pipeline()\n"
        "    return {'status': 'success', 'data': result}"
    )
    elements.append(Paragraph(code_text.replace("\n", "<br/>&nbsp;&nbsp;&nbsp;&nbsp;"), code_style))

    # Image
    img_temp = output_pdf.parent / "test_diagram.png"
    create_sample_image(img_temp)
    elements.append(Paragraph("5. Architectural Diagnostic Diagram", h1_style))
    elements.append(RLImage(str(img_temp), width=300, height=120))
    elements.append(Spacer(1, 10))

    # Antigravity Alert 3: Tip
    elements.append(Paragraph("Tip: Use standalone Base64 mode for self-contained single markdown artifacts.", body_style))

    doc.build(elements)
    print(f"Benchmark PDF generated: {output_pdf}")


if __name__ == "__main__":
    out_path = Path(__file__).parent / "benchmark_test.pdf"
    generate_benchmark_pdf(out_path)
