"""
Spatial Layout & Column Topology Engine
Reconstructs natural reading flow, unrolls multi-column documents, analyzes font hierarchy,
and detects code blocks and lists.
"""

from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
import fitz  # PyMuPDF


class LayoutAnalyzer:
    """Analyzes spatial topology and typographic hierarchy of PDF pages."""

    MONOSPACE_FONTS = {
        "courier", "consolas", "monaco", "menlo", "inconsolata",
        "dejavusansmono", "sourcecodepro", "lucidaconsole", "terminal",
        "monospace", "roboto mono", "fira mono", "fira code"
    }

    @classmethod
    def analyze_document_typography(cls, doc: fitz.Document) -> Dict[str, float]:
        """
        Samples font sizes across the document to establish statistical thresholds
        for body text, H1, H2, and H3 headers.
        """
        font_sizes: List[float] = []

        # Sample up to first 10 pages for rapid profiling
        sample_pages = min(len(doc), 10)
        for pno in range(sample_pages):
            page = doc[pno]
            text_page = page.get_text("dict")
            for block in text_page.get("blocks", []):
                if block.get("type") == 0:  # text
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                font_sizes.append(round(span.get("size", 10.0), 1))

        if not font_sizes:
            return {"body": 10.0, "h1": 20.0, "h2": 15.0, "h3": 12.0}

        counts = Counter(font_sizes)
        body_size = counts.most_common(1)[0][0]

        return {
            "body": body_size,
            "h1": body_size * 1.6,
            "h2": body_size * 1.3,
            "h3": body_size * 1.1,
        }

    @classmethod
    def get_ordered_blocks_for_page(
        cls,
        page: fitz.Page,
        excluded_bboxes: List[fitz.Rect],
        unroll_columns: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extracts all text blocks from a page, excluding specified bboxes (e.g. tables),
        and sorts them in natural reading order (handling multi-column layouts).
        """
        raw_dict = page.get_text("dict")
        raw_blocks = raw_dict.get("blocks", [])
        text_blocks = []

        # PyMuPDF links
        page_links = page.get_links()

        for b in raw_blocks:
            if b.get("type") != 0:  # Only process text blocks here
                continue

            bbox = fitz.Rect(b.get("bbox"))
            
            # Check if this block is entirely inside an excluded table bbox
            is_inside_table = False
            for tbox in excluded_bboxes:
                # If block overlaps significantly with table
                intersection = bbox & tbox
                if intersection.get_area() > 0.5 * bbox.get_area():
                    is_inside_table = True
                    break

            if is_inside_table:
                continue

            text_blocks.append(b)

        if not text_blocks:
            return []

        if not unroll_columns:
            # Simple top-to-bottom sort
            return sorted(text_blocks, key=lambda x: (round(x["bbox"][1] / 10), x["bbox"][0]))

        # Multi-column unrolling:
        return cls._sort_multi_column(page.rect.width, text_blocks)

    @classmethod
    def _sort_multi_column(cls, page_width: float, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects if blocks fall into 2 or 3 distinct vertical columns, sorting
        full-width elements chronologically and columns top-to-bottom.
        """
        mid_x = page_width / 2.0
        
        # Check if there is multi-column text:
        left_blocks = []
        right_blocks = []
        spanning_blocks = []

        for b in blocks:
            x0, y0, x1, y1 = b["bbox"]
            width = x1 - x0
            
            # If block spans more than 65% of page width, it's a spanning header/banner
            if width > page_width * 0.65:
                spanning_blocks.append(b)
            elif x1 <= mid_x + 20:
                left_blocks.append(b)
            elif x0 >= mid_x - 20:
                right_blocks.append(b)
            else:
                # Crossing the middle slightly
                spanning_blocks.append(b)

        # If either column is nearly empty, document is predominantly single-column
        if len(left_blocks) < 2 or len(right_blocks) < 2:
            return sorted(blocks, key=lambda b: (round(b["bbox"][1] / 5), b["bbox"][0]))

        # We have a multi-column document!
        # Reconstruct reading order:
        # Group spanning blocks and column segments by vertical segments
        all_elements = []
        
        # Sort left and right columns internally by top-to-bottom
        left_blocks.sort(key=lambda b: b["bbox"][1])
        right_blocks.sort(key=lambda b: b["bbox"][1])
        spanning_blocks.sort(key=lambda b: b["bbox"][1])

        # Slice reading stream: full-width banners, then left column, then right column
        # To maintain natural flow: if there is a top spanning banner, place it first
        top_spanners = [b for b in spanning_blocks if b["bbox"][1] < min(
            left_blocks[0]["bbox"][1] if left_blocks else 9999,
            right_blocks[0]["bbox"][1] if right_blocks else 9999
        )]
        
        bottom_spanners = [b for b in spanning_blocks if b not in top_spanners]

        all_elements.extend(top_spanners)
        all_elements.extend(left_blocks)
        all_elements.extend(right_blocks)
        all_elements.extend(bottom_spanners)

        return all_elements

    @classmethod
    def format_block_text(
        cls,
        block: Dict[str, Any],
        typo_stats: Dict[str, float],
        page_links: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Parses spans within a block, detecting headers, bold/italic styles,
        code snippets, and links.
        Returns: (block_type, formatted_markdown_text)
        block_type: 'header', 'code', 'list', 'paragraph'
        """
        lines = block.get("lines", [])
        if not lines:
            return "paragraph", ""

        # Check for monospace code block
        is_code = cls._is_monospace_block(lines)
        if is_code:
            code_text = cls._extract_raw_lines(lines)
            return "code", f"```text\n{code_text}\n```"

        # Check font sizes across lines to see if this is a header
        max_size = 0.0
        is_all_bold = True
        total_spans = 0

        rendered_lines: List[str] = []
        
        for line in lines:
            line_str = ""
            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text:
                    continue

                total_spans += 1
                size = span.get("size", 10.0)
                flags = span.get("flags", 0)  # bit 1: italic, bit 4: bold
                font_name = span.get("font", "").lower()

                if size > max_size:
                    max_size = size

                is_bold = bool(flags & (1 << 4)) or ("bold" in font_name) or ("black" in font_name)
                is_italic = bool(flags & (1 << 1)) or ("italic" in font_name) or ("oblique" in font_name)
                
                if not is_bold and len(text.strip()) > 3:
                    is_all_bold = False

                # Check if span intersects a hyperlink
                span_bbox = fitz.Rect(span.get("bbox", (0, 0, 0, 0)))
                link_url = cls._find_link_for_bbox(span_bbox, page_links)

                formatted_span = text
                if link_url:
                    formatted_span = f"[{formatted_span}]({link_url})"
                elif is_bold and is_italic:
                    formatted_span = f"***{formatted_span}***"
                elif is_bold:
                    formatted_span = f"**{formatted_span}**"
                elif is_italic:
                    formatted_span = f"*{formatted_span}*"

                line_str += formatted_span

            if line_str.strip():
                rendered_lines.append(line_str)

        full_text = "\n".join(rendered_lines).strip()
        if not full_text:
            return "paragraph", ""

        # Check if this block qualifies as a heading based on font thresholds
        body_size = typo_stats.get("body", 10.0)
        h1_thresh = typo_stats.get("h1", 16.0)
        h2_thresh = typo_stats.get("h2", 13.0)
        h3_thresh = typo_stats.get("h3", 11.5)

        # Single or short line header check
        is_short = len(full_text.split("\n")) <= 2 and len(full_text) < 120

        if is_short and max_size >= h1_thresh:
            clean_title = full_text.replace("**", "").replace("***", "")
            return "header", f"# {clean_title}"
        elif is_short and max_size >= h2_thresh:
            clean_title = full_text.replace("**", "").replace("***", "")
            return "header", f"## {clean_title}"
        elif is_short and (max_size >= h3_thresh or (is_all_bold and total_spans > 0)):
            clean_title = full_text.replace("**", "").replace("***", "")
            return "header", f"### {clean_title}"

        # Check for list items
        if full_text.startswith(("• ", "- ", "* ")) or (len(full_text) > 2 and full_text[0].isdigit() and full_text[1:3] in [". ", ") "]):
            return "list", full_text

        # Standard paragraph
        return "paragraph", full_text

    @classmethod
    def _is_monospace_block(cls, lines: List[Dict[str, Any]]) -> bool:
        """Determines if the majority of spans in lines use a monospace font."""
        mono_count = 0
        total_count = 0
        for line in lines:
            for span in line.get("spans", []):
                font = span.get("font", "").lower()
                total_count += 1
                if any(m in font for m in cls.MONOSPACE_FONTS):
                    mono_count += 1
        return total_count > 0 and (mono_count / total_count) >= 0.7

    @classmethod
    def _extract_raw_lines(cls, lines: List[Dict[str, Any]]) -> str:
        """Extracts unformatted verbatim lines (for code blocks)."""
        res = []
        for line in lines:
            line_str = "".join(span.get("text", "") for span in line.get("spans", []))
            res.append(line_str)
        return "\n".join(res)

    @classmethod
    def _find_link_for_bbox(cls, bbox: fitz.Rect, links: List[Dict[str, Any]]) -> Optional[str]:
        """Finds active URI hyperlink overlapping a given span bbox."""
        if not links or bbox.is_empty:
            return None
        for link in links:
            l_rect = fitz.Rect(link.get("from"))
            if bbox.intersects(l_rect):
                uri = link.get("uri")
                if uri:
                    return uri
        return None
