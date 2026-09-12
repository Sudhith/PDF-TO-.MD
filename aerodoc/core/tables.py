"""
Table Extraction Engine
Identifies table boundaries, structures rows/columns, and generates clean GitHub-Flavored Markdown tables.
"""

from typing import List, Tuple, Dict, Any, Optional
import fitz  # PyMuPDF


class TableExtractor:
    """Extracts tables from PDF pages and formats them as GFM tables."""

    @staticmethod
    def extract_tables_from_page(page: fitz.Page) -> Tuple[List[Dict[str, Any]], List[fitz.Rect]]:
        """
        Detects tables on a page, returns:
        - List of table dicts containing markdown string, bbox, and row count
        - List of table bounding rectangles (for text exclusion)
        """
        extracted_tables = []
        table_bboxes = []

        try:
            tabs = page.find_tables()
            if not tabs or len(tabs.tables) == 0:
                return extracted_tables, table_bboxes

            for tab in tabs:
                bbox = fitz.Rect(tab.bbox)
                table_bboxes.append(bbox)
                
                # Extract 2D matrix of strings
                raw_matrix = tab.extract()
                if not raw_matrix or len(raw_matrix) == 0:
                    continue

                md_table = TableExtractor._matrix_to_gfm(raw_matrix)
                if md_table:
                    extracted_tables.append({
                        "bbox": bbox,
                        "markdown": md_table,
                        "rows": len(raw_matrix),
                        "cols": len(raw_matrix[0]) if raw_matrix else 0,
                    })
        except Exception:
            # Non-fatal fallback if tables module encounters anomalous graphics
            pass

        return extracted_tables, table_bboxes

    @staticmethod
    def _matrix_to_gfm(matrix: List[List[Optional[str]]]) -> str:
        """Converts a 2D matrix of strings into a GitHub-Flavored Markdown table."""
        if not matrix:
            return ""

        # Normalize rows to match max column length
        num_cols = max(len(row) for row in matrix)
        if num_cols == 0:
            return ""

        clean_rows: List[List[str]] = []
        for row in matrix:
            cleaned_row = []
            for c_idx in range(num_cols):
                val = row[c_idx] if c_idx < len(row) else ""
                if val is None:
                    val = ""
                # Replace inner newlines with space or <br>
                cell_str = str(val).strip().replace("\n", " ").replace("|", "\\|")
                cleaned_row.append(cell_str)
            clean_rows.append(cleaned_row)

        # First row is header
        header = clean_rows[0]
        # If header is completely empty, generate placeholder Col 1, Col 2...
        if all(len(c) == 0 for c in header):
            header = [f"Column {i+1}" for i in range(num_cols)]

        # Delimiter row
        delimiters = ["---"] * num_cols

        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(delimiters) + " |"
        ]

        for row in clean_rows[1:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)
