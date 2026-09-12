"""
Universal Multi-Format Document Ingestion Engine
Handles conversion across PDF, DOCX, Plain Text, HTML, CSV, and Markdown formats
into publication-grade Antigravity Markdown.
"""

import os
import re
import csv
import io
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from bs4 import BeautifulSoup
import docx
import yaml

from aerodoc.config import ConversionConfig
from aerodoc.core.converter import PDFConverter
from aerodoc.core.callouts import CalloutTransformer
from aerodoc.core.math_detector import MathDetector
from aerodoc.exceptions import CorruptedPDFError


class UniversalConverter:
    """Dispatches and converts multiple document formats into standard Antigravity Markdown."""

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".doc", ".txt", ".text", ".log",
        ".csv", ".tsv", ".html", ".htm", ".rtf", ".md", ".json", ".yaml"
    }

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()
        self.pdf_converter = PDFConverter(self.config)

    def convert(
        self,
        file_path: Path,
        output_path: Optional[Path] = None,
        assets_path: Optional[Path] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Routes file based on extension to appropriate format parser.
        Returns: (markdown_content, telemetry_stats)
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            return self.pdf_converter.convert_file(file_path, output_path, assets_path)
        elif ext in (".docx", ".doc"):
            return self._convert_docx(file_path, output_path)
        elif ext in (".html", ".htm", ".rtf"):
            return self._convert_html(file_path, output_path)
        elif ext in (".csv", ".tsv"):
            return self._convert_delimited(file_path, output_path, delimiter="," if ext == ".csv" else "\t")
        elif ext in (".txt", ".text", ".log", ".json", ".yaml", ".md"):
            return self._convert_text(file_path, output_path, ext)
        else:
            # Fallback to plain text
            return self._convert_text(file_path, output_path, ext)

    def _convert_docx(self, docx_path: Path, output_path: Optional[Path]) -> Tuple[str, Dict[str, Any]]:
        """Parses Microsoft Word (.docx) documents, preserving hierarchy, tables, and styles."""
        start_time = time.time()
        try:
            doc = docx.Document(docx_path)
        except Exception as e:
            raise CorruptedPDFError(f"Failed to parse Word document: {str(e)}")

        stats = {
            "filename": docx_path.name,
            "format": "Microsoft Word (.docx)",
            "pages": max(1, len(doc.paragraphs) // 15),
            "tables_extracted": len(doc.tables),
            "images_extracted": 0,
            "headings_found": 0,
            "equations_found": 0,
            "callouts_transformed": 0,
            "document_type": "Executive Document",
            "readability_score": 75.0,
            "readability_grade": "Corporate / Professional",
            "elapsed_seconds": 0.0,
            "output_path": str(output_path) if output_path else None
        }

        md_sections = []

        # Frontmatter
        if self.config.include_frontmatter:
            meta = {
                "title": docx_path.stem.replace("_", " ").title(),
                "format": "Antigravity Markdown",
                "source_type": "Microsoft Word (.docx)",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "engine": "AeroDoc Universal"
            }
            md_sections.append(f"---\n{yaml.dump(meta, sort_keys=False)}---\n")

        # Process paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""

            # Check for callouts first
            if self.config.detect_callouts:
                is_callout, callout_md = CalloutTransformer.transform_if_callout(text)
                if is_callout:
                    stats["callouts_transformed"] += 1
                    md_sections.append(f"\n{callout_md}\n")
                    continue

            # Check for headings
            if "heading 1" in style_name or style_name == "title":
                stats["headings_found"] += 1
                md_sections.append(f"\n# {text}\n")
            elif "heading 2" in style_name:
                stats["headings_found"] += 1
                md_sections.append(f"\n## {text}\n")
            elif "heading 3" in style_name:
                stats["headings_found"] += 1
                md_sections.append(f"\n### {text}\n")
            elif "heading 4" in style_name:
                stats["headings_found"] += 1
                md_sections.append(f"\n#### {text}\n")
            elif "list" in style_name or "bullet" in style_name:
                md_sections.append(f"- {text}")
            else:
                # Reconstruct formatted runs (bold, italic)
                formatted_runs = []
                for run in p.runs:
                    run_text = run.text
                    if not run_text:
                        continue
                    if run.bold and run.italic:
                        formatted_runs.append(f"***{run_text}***")
                    elif run.bold:
                        formatted_runs.append(f"**{run_text}**")
                    elif run.italic:
                        formatted_runs.append(f"*{run_text}*")
                    else:
                        formatted_runs.append(run_text)

                paragraph_text = "".join(formatted_runs).strip()
                if self.config.detect_math:
                    paragraph_text = MathDetector.enrich_inline_math(paragraph_text)

                md_sections.append(paragraph_text)

        # Process Tables
        if self.config.detect_tables and doc.tables:
            for table in doc.tables:
                rows_data = []
                for row in table.rows:
                    cells = [cell.text.strip().replace("\n", " ").replace("|", "\\|") for cell in row.cells]
                    rows_data.append(cells)

                if rows_data:
                    num_cols = max(len(r) for r in rows_data)
                    header = rows_data[0]
                    delims = ["---"] * num_cols
                    table_lines = [
                        "| " + " | ".join(header) + " |",
                        "| " + " | ".join(delims) + " |"
                    ]
                    for r in rows_data[1:]:
                        # Pad row if short
                        padded = r + [""] * (num_cols - len(r))
                        table_lines.append("| " + " | ".join(padded) + " |")

                    md_sections.append("\n" + "\n".join(table_lines) + "\n")

        full_md = "\n\n".join(md_sections).strip()

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(full_md, encoding="utf-8")

        stats["elapsed_seconds"] = round(time.time() - start_time, 3)
        return full_md, stats

    def _convert_html(self, html_path: Path, output_path: Optional[Path]) -> Tuple[str, Dict[str, Any]]:
        """Converts HTML/RTF web documents into clean structural Markdown."""
        start_time = time.time()
        raw_html = html_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw_html, "html.parser")

        # Strip script and style noise
        for s in soup(["script", "style", "meta", "noscript"]):
            s.decompose()

        md_sections = []
        if self.config.include_frontmatter:
            title = soup.title.string.strip() if soup.title else html_path.stem.title()
            meta = {
                "title": title,
                "format": "Antigravity Markdown",
                "source_type": "HTML Document",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "engine": "AeroDoc Universal"
            }
            md_sections.append(f"---\n{yaml.dump(meta, sort_keys=False)}---\n")

        # Extract structural elements
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "table", "pre", "ul", "ol", "blockquote"]):
            text = tag.get_text(separator=" ", strip=True)
            if not text and tag.name != "table":
                continue

            if tag.name == "h1":
                md_sections.append(f"\n# {text}\n")
            elif tag.name == "h2":
                md_sections.append(f"\n## {text}\n")
            elif tag.name == "h3":
                md_sections.append(f"\n### {text}\n")
            elif tag.name == "h4":
                md_sections.append(f"\n#### {text}\n")
            elif tag.name == "blockquote":
                is_callout, callout_md = CalloutTransformer.transform_if_callout(text)
                md_sections.append(f"\n{callout_md}\n" if is_callout else f"> {text}")
            elif tag.name == "pre":
                md_sections.append(f"```text\n{tag.get_text()}\n```")
            elif tag.name in ("ul", "ol"):
                items = [f"- {li.get_text(strip=True)}" for li in tag.find_all("li") if li.get_text(strip=True)]
                if items:
                    md_sections.append("\n".join(items))
            elif tag.name == "table":
                rows = []
                for tr in tag.find_all("tr"):
                    cells = [td.get_text(strip=True).replace("|", "\\|") for td in tr.find_all(["th", "td"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    max_cols = max(len(r) for r in rows)
                    header = rows[0]
                    delims = ["---"] * max_cols
                    tbl = ["| " + " | ".join(header) + " |", "| " + " | ".join(delims) + " |"]
                    for r in rows[1:]:
                        padded = r + [""] * (max_cols - len(r))
                        tbl.append("| " + " | ".join(padded) + " |")
                    md_sections.append("\n" + "\n".join(tbl) + "\n")
            else:
                md_sections.append(text)

        full_md = "\n\n".join(md_sections).strip()
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(full_md, encoding="utf-8")

        stats = {
            "filename": html_path.name,
            "format": "HTML Document",
            "pages": 1,
            "tables_extracted": len(soup.find_all("table")),
            "images_extracted": 0,
            "headings_found": len(soup.find_all(["h1", "h2", "h3"])),
            "equations_found": 0,
            "callouts_transformed": 0,
            "document_type": "Web Architecture",
            "readability_score": 80.0,
            "readability_grade": "Standard Audience",
            "elapsed_seconds": round(time.time() - start_time, 3),
            "output_path": str(output_path) if output_path else None
        }
        return full_md, stats

    def _convert_delimited(self, file_path: Path, output_path: Optional[Path], delimiter: str = ",") -> Tuple[str, Dict[str, Any]]:
        """Converts tabular data (CSV / TSV) into a clean GitHub-Flavored Markdown table."""
        start_time = time.time()
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
        rows = list(reader)

        if not rows:
            return "", {"filename": file_path.name, "pages": 1, "elapsed_seconds": 0.0}

        num_cols = max(len(r) for r in rows)
        header = rows[0]
        delims = ["---"] * num_cols

        table_lines = [
            f"# {file_path.stem.replace('_', ' ').title()}\n",
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(delims) + " |"
        ]

        for r in rows[1:]:
            padded = r + [""] * (num_cols - len(r))
            clean_cells = [c.replace("|", "\\|").strip() for c in padded]
            table_lines.append("| " + " | ".join(clean_cells) + " |")

        full_md = "\n".join(table_lines)
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(full_md, encoding="utf-8")

        stats = {
            "filename": file_path.name,
            "format": "Delimited Data",
            "pages": max(1, len(rows) // 40),
            "tables_extracted": 1,
            "images_extracted": 0,
            "headings_found": 1,
            "equations_found": 0,
            "callouts_transformed": 0,
            "document_type": "Structured Data Matrix",
            "readability_score": 90.0,
            "readability_grade": "Data Table",
            "elapsed_seconds": round(time.time() - start_time, 3),
            "output_path": str(output_path) if output_path else None
        }
        return full_md, stats

    def _convert_text(self, file_path: Path, output_path: Optional[Path], ext: str) -> Tuple[str, Dict[str, Any]]:
        """Converts plain text, JSON, YAML, or Markdown files."""
        start_time = time.time()
        content = file_path.read_text(encoding="utf-8", errors="replace").strip()

        if ext in (".json", ".yaml"):
            lang = ext.lstrip(".")
            full_md = f"# {file_path.stem.title()}\n\n```{lang}\n{content}\n```"
        else:
            # Check for callouts line by line
            lines = content.split("\n")
            processed_lines = []
            callouts_found = 0
            for line in lines:
                is_callout, callout_md = CalloutTransformer.transform_if_callout(line)
                if is_callout:
                    callouts_found += 1
                    processed_lines.append(callout_md)
                else:
                    processed_lines.append(line)
            full_md = "\n".join(processed_lines)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(full_md, encoding="utf-8")

        stats = {
            "filename": file_path.name,
            "format": f"Plain Text ({ext})",
            "pages": max(1, len(content.split("\n")) // 40),
            "tables_extracted": 0,
            "images_extracted": 0,
            "headings_found": 1,
            "equations_found": 0,
            "callouts_transformed": 0,
            "document_type": "Source Code / Text",
            "readability_score": 85.0,
            "readability_grade": "General Technical",
            "elapsed_seconds": round(time.time() - start_time, 3),
            "output_path": str(output_path) if output_path else None
        }
        return full_md, stats
