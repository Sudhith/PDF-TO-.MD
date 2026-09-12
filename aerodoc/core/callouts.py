"""
Antigravity Alert & Callout Transformer
Detects warning, note, tip, and important callouts and converts them to standard Antigravity alerts.
"""

import re
from typing import Tuple, Optional


class CalloutTransformer:
    """Transforms note/warning/tip patterns into standard Antigravity Markdown alerts."""

    CALLOUT_MAP = {
        "note": "NOTE",
        "notice": "NOTE",
        "info": "NOTE",
        "tip": "TIP",
        "hint": "TIP",
        "best practice": "TIP",
        "important": "IMPORTANT",
        "attention": "IMPORTANT",
        "key point": "IMPORTANT",
        "warning": "WARNING",
        "warn": "WARNING",
        "caution": "CAUTION",
        "danger": "CAUTION",
    }

    # Regex pattern matching callout prefix at start of paragraph or heading
    # e.g., "### Note: ...", "**Note:**", "[Note]", "Warning -", etc.
    PATTERN = re.compile(
        r"^(?:#{1,6}\s*)?(?:\*{1,2}|\[)?\s*(Note|Notice|Info|Tip|Hint|Best Practice|Important|Attention|Key Point|Warning|Warn|Caution|Danger)\s*(?:\*{1,2}|\])?\s*[:\-—]\s*(.*)$",
        re.IGNORECASE | re.DOTALL
    )

    @classmethod
    def transform_if_callout(cls, text: str) -> Tuple[bool, str]:
        """
        Tests if text block is a callout.
        Returns (is_callout, transformed_markdown).
        """
        trimmed = text.strip()
        match = cls.PATTERN.match(trimmed)
        if not match:
            return False, text

        tag_raw = match.group(1).lower()
        content = match.group(2).strip()

        alert_type = cls.CALLOUT_MAP.get(tag_raw, "NOTE")

        # Split content into lines and prefix each line with '>'
        content_lines = content.split("\n")
        formatted_lines = [f"> [!{alert_type}]"]
        for line in content_lines:
            line_str = line.strip()
            # Remove any trailing Markdown boldness markers if present
            line_str = re.sub(r"^\*\*|\*\*$", "", line_str)
            if line_str:
                formatted_lines.append(f"> {line_str}")
            else:
                formatted_lines.append(">")

        return True, "\n".join(formatted_lines)
