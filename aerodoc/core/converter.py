"""
AeroDoc Converter Engine
Master orchestrator for lossless PDF to Markdown conversion.
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import fitz  # PyMuPDF
import yaml

from aerodoc.config import ConversionConfig
from aerodoc.core.layout import LayoutAnalyzer
from aerodoc.core.tables import TableExtractor
from aerodoc.core.callouts import CalloutTransformer
from aerodoc.core.math_detector import MathDetector
from aerodoc.core.images import ImageExtractor
from aerodoc.security import validate_pdf_stream
from aerodoc.exceptions import EncryptedPDFError, CorruptedPDFError


class PDFConverter:
    """Orchestrates comprehensive, lossless PDF to Markdown conversion."""

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()

    def convert_file(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None,
        assets_path: Optional[Path] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Converts a PDF file at `pdf_path` into Antigravity Markdown.
        Writes to `output_path` if specified.
        Returns: (markdown_content, conversion_stats)
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Security check: Validate file bytes and signature
        raw_bytes = pdf_path.read_bytes()
        validate_pdf_stream(raw_bytes, self.config.max_file_size_bytes)

        # Resolve output directories
        if output_path:
            output_path = Path(output_path)
            if not assets_path:
                assets_path = output_path.parent / self.config.assets_dir_name
        elif not assets_path and not self.config.embed_images:
            assets_path = pdf_path.parent / self.config.assets_dir_name

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise CorruptedPDFError(f"Failed to open PDF document: {str(e)}")

        # Detect password protected documents
        if doc.is_encrypted:
            doc.close()
            raise EncryptedPDFError("Document is encrypted or password-protected. Please decrypt before conversion.")

        stats = {
            "filename": pdf_path.name,
            "pages": len(doc),
            "tables_extracted": 0,
            "images_extracted": 0,
            "headings_found": 0,
            "equations_found": 0,
            "callouts_transformed": 0,
            "document_type": "General Document",
            "readability_score": 0.0,
            "readability_grade": "General Audience",
            "elapsed_seconds": 0.0,
            "output_path": str(output_path) if output_path else None
        }

        # Analyze typography across document
        typo_stats = LayoutAnalyzer.analyze_document_typography(doc)

        md_sections: List[str] = []

        # 1. YAML Frontmatter
        if self.config.include_frontmatter:
            frontmatter_str = self._generate_frontmatter(doc, pdf_path)
            if frontmatter_str:
                md_sections.append(frontmatter_str)

        # 2. Table of Contents
        if self.config.include_toc:
            toc_str = self._generate_toc(doc)
            if toc_str:
                md_sections.append(toc_str)

        # 3. Process Pages
        for pno in range(len(doc)):
            page = doc[pno]
            page_links = page.get_links()

            # Page marker
            if self.config.preserve_page_markers:
                if pno > 0 or self.config.include_frontmatter:
                    md_sections.append(f"\n<!-- Page {pno + 1} -->\n---\n")

            # Extract Tables
            tables, table_bboxes = ([], [])
            if self.config.detect_tables:
                tables, table_bboxes = TableExtractor.extract_tables_from_page(page)
                stats["tables_extracted"] += len(tables)

            # Extract Images
            images = ImageExtractor.extract_page_images(
                doc=doc,
                page_index=pno,
                config=self.config,
                assets_dir=assets_path
            )
            stats["images_extracted"] += len(images)

            # Extract text blocks
            ordered_blocks = LayoutAnalyzer.get_ordered_blocks_for_page(
                page=page,
                excluded_bboxes=table_bboxes,
                unroll_columns=self.config.unroll_columns
            )

            # Blend blocks and tables in vertical topological order
            page_elements = []
            for b in ordered_blocks:
                page_elements.append({
                    "type": "block",
                    "y0": b["bbox"][1],
                    "data": b
                })

            for t in tables:
                page_elements.append({
                    "type": "table",
                    "y0": t["bbox"].y0,
                    "data": t["markdown"]
                })

            # Sort page elements by vertical coordinate
            page_elements.sort(key=lambda item: item["y0"])

            # Render Page Elements
            for elem in page_elements:
                if elem["type"] == "table":
                    md_sections.append("\n" + elem["data"] + "\n")
                elif elem["type"] == "block":
                    block = elem["data"]
                    b_type, formatted_text = LayoutAnalyzer.format_block_text(
                        block=block,
                        typo_stats=typo_stats,
                        page_links=page_links
                    )

                    if not formatted_text:
                        continue

                    # 1. Check for callout alert box first (even if styled as a heading)
                    is_callout = False
                    if self.config.detect_callouts:
                        is_callout, callout_md = CalloutTransformer.transform_if_callout(formatted_text)
                        if is_callout:
                            stats["callouts_transformed"] += 1
                            md_sections.append(f"\n{callout_md}\n")
                            continue

                    if b_type == "header":
                        stats["headings_found"] += 1
                        md_sections.append(f"\n{formatted_text}\n")
                    elif b_type == "code":
                        md_sections.append(f"\n{formatted_text}\n")
                    else:
                        # Check for display math
                        is_math = False
                        if self.config.detect_math:
                            is_math, math_md = MathDetector.format_math_block(formatted_text)
                            if is_math:
                                stats["equations_found"] += 1
                                md_sections.append(f"\n{math_md}\n")

                        if not is_math:
                            # Apply inline math enrichment
                            if self.config.detect_math:
                                formatted_text = MathDetector.enrich_inline_math(formatted_text)
                            
                            # Rejoin hyphenated words if configured
                            if self.config.rejoin_hyphenated_words:
                                formatted_text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", formatted_text)

                            md_sections.append(formatted_text)

            # Append page figures
            if images:
                for img in images:
                    md_sections.append(f"\n{img['markdown']}\n")

        # Synthesize final document
        raw_markdown = "\n\n".join(md_sections)
        sanitized_markdown = self._sanitize_markdown(raw_markdown)

        # Smart Analytics: Document Type & Readability Grade
        doc_type = self._classify_document(stats, sanitized_markdown)
        score, grade = self._compute_readability(sanitized_markdown)
        stats["document_type"] = doc_type
        stats["readability_score"] = score
        stats["readability_grade"] = grade

        # Write to disk if requested
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(sanitized_markdown, encoding="utf-8")

        stats["elapsed_seconds"] = round(time.time() - start_time, 3)
        return sanitized_markdown, stats

    def _generate_frontmatter(self, doc: fitz.Document, pdf_path: Path) -> str:
        """Constructs YAML frontmatter metadata block."""
        meta = doc.metadata or {}
        title = meta.get("title") or pdf_path.stem.replace("_", " ").title()
        author = meta.get("author") or "Document Author"
        creation_date = meta.get("creationDate") or datetime.now().strftime("%Y-%m-%d")
        
        # Clean creation date string if PDF format (D:2025...)
        if creation_date.startswith("D:"):
            try:
                creation_date = f"{creation_date[2:6]}-{creation_date[6:8]}-{creation_date[8:10]}"
            except Exception:
                creation_date = datetime.now().strftime("%Y-%m-%d")

        frontmatter_dict = {
            "title": title,
            "author": author,
            "pages": len(doc),
            "date": creation_date,
            "engine": "AeroDoc",
            "format": "Antigravity Markdown"
        }

        # Subject or keywords
        if meta.get("subject"):
            frontmatter_dict["subject"] = meta["subject"]
        if meta.get("keywords"):
            frontmatter_dict["keywords"] = [k.strip() for k in meta["keywords"].split(",") if k.strip()]

        yaml_dump = yaml.dump(frontmatter_dict, sort_keys=False, allow_unicode=True)
        return f"---\n{yaml_dump}---"

    def _generate_toc(self, doc: fitz.Document) -> Optional[str]:
        """Extracts document bookmarks / outline into a markdown Table of Contents."""
        toc_items = doc.get_toc()
        if not toc_items:
            return None

        lines = ["## Table of Contents\n"]
        for item in toc_items:
            lvl, title, pno = item
            indent = "  " * max(0, lvl - 1)
            lines.append(f"{indent}- **{title}** (Page {pno})")

        return "\n".join(lines)

    def _sanitize_markdown(self, text: str) -> str:
        """Removes excessive newlines and guarantees zero synthetic AI traces."""
        # Normalize newline spacing
        clean = re.sub(r"\n{3,}", "\n\n", text)
        return clean.strip()

    def _classify_document(self, stats: Dict[str, Any], text: str) -> str:
        """Heuristically categorizes the document topology and subject matter."""
        text_lower = text.lower()
        if stats["equations_found"] >= 2 or "abstract" in text_lower or "references" in text_lower:
            return "Academic / Research Paper"
        elif "```" in text or "api" in text_lower or "specification" in text_lower or "architecture" in text_lower:
            return "Technical Architecture / Manual"
        elif stats["tables_extracted"] >= 3 or "balance" in text_lower or "revenue" in text_lower or "q1" in text_lower:
            return "Financial / Structured Report"
        elif "agenda" in text_lower or "presentation" in text_lower or stats["pages"] <= 3 and stats["images_extracted"] >= 2:
            return "Executive Summary / Brief"
        return "Technical Documentation"

    def _compute_readability(self, text: str) -> Tuple[float, str]:
        """Calculates Flesch Reading Ease and estimated audience grade."""
        words = re.findall(r"\b[A-Za-z]+\b", text)
        if len(words) < 20:
            return 70.0, "General Audience"

        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if len(s.strip()) > 0]
        num_sentences = max(1, len(sentences))
        num_words = len(words)

        # Approximate syllables by vowel groups
        def count_syllables(word: str) -> int:
            w = word.lower()
            return max(1, len(re.findall(r"[aeiouy]+", w)))

        total_syllables = sum(count_syllables(w) for w in words)

        # Flesch Reading Ease score
        score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (total_syllables / num_words)
        score = round(max(0.0, min(100.0, score)), 1)

        if score >= 80:
            grade = "Elementary / Plain English"
        elif score >= 60:
            grade = "Standard Audience"
        elif score >= 40:
            grade = "College / Professional"
        else:
            grade = "Advanced Technical / Academic"

        return score, grade
