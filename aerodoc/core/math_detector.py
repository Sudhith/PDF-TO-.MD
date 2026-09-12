"""
Mathematical Formula & KaTeX Expression Recognizer
Detects LaTeX math, mathematical symbols, and equations, formatting them for KaTeX rendering.
"""

import re
from typing import Tuple

class MathDetector:
    """Detects and formats inline and display mathematics for KaTeX."""

    # Common unicode math operators and Greek letters
    MATH_SYMBOLS = set("∑∫∂√ππαβγδεζηθικλμνξοπρστυφχψω∆∇∈∉⊂⊆∪∩≤≥≠≈≡±×÷∞∀∃ℝℂℤℕ")
    
    # Common LaTeX math tokens
    LATEX_TOKENS = [
        r"\frac", r"\sum", r"\int", r"\partial", r"\sqrt", r"\alpha", r"\beta",
        r"\gamma", r"\theta", r"\lambda", r"\sigma", r"\omega", r"\times",
        r"\pm", r"\infty", r"\in", r"\subset", r"\approx", r"\neq", r"\le", r"\ge",
        r"\mathbb", r"\mathcal", r"\mathbf", r"\begin", r"\end"
    ]

    # Superscript / Subscript character map
    SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ", "0123456789+-=()ni")
    SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎", "0123456789+-=()")

    @classmethod
    def format_math_block(cls, text: str) -> Tuple[bool, str]:
        """
        Checks if an entire block or line is a standalone display math equation.
        Returns (is_math, formatted_latex).
        """
        trimmed = text.strip()
        
        # If already formatted as math
        if trimmed.startswith("$$") and trimmed.endswith("$$"):
            return True, trimmed

        # If it contains explicit LaTeX commands and math symbols
        has_latex = any(tok in trimmed for tok in cls.LATEX_TOKENS)
        symbol_count = sum(1 for ch in trimmed if ch in cls.MATH_SYMBOLS)

        # Standalone equation pattern like "E = m c^2" or "f(x) = \int ..."
        is_isolated_eq = bool(re.match(r"^[A-Za-z0-9\(\)\[\]\\_^{}\s+\-*/=><∑∫∂√±×÷π\.,]+$", trimmed)) and (
            ("=" in trimmed or "≈" in trimmed or "≤" in trimmed or "≥" in trimmed) and
            (has_latex or symbol_count >= 1 or "^" in trimmed or "_" in trimmed)
        )

        if has_latex or (symbol_count >= 2 and is_isolated_eq):
            # Format display equation
            clean_eq = cls._convert_unicode_symbols_to_latex(trimmed)
            return True, f"$$\n{clean_eq}\n$$"

        return False, text

    @classmethod
    def enrich_inline_math(cls, text: str) -> str:
        """
        Detects inline formulas and wraps them in $ ... $ while preserving currency ($50.00).
        """
        # If already has math fences, skip
        if "$" in text:
            # Check if this is KaTeX or currency
            # If standard currency like $50 or $1,000, don't break it
            currency_pattern = re.compile(r"\$\d+(?:\.\d+)?(?:\s*(?:USD|million|billion|k|M))?")
            # Temporarily protect currency
            placeholders = {}
            def repl_curr(m):
                key = f"__CURR_{len(placeholders)}__"
                placeholders[key] = m.group(0)
                return key
            
            clean_text = currency_pattern.sub(repl_curr, text)
        else:
            clean_text = text
            placeholders = {}

        # Look for isolated single-variable or symbol equations like "where x = y + 1" or "α + β = γ"
        def repl_symbol_eq(m):
            frag = m.group(0)
            if any(tok in frag for tok in cls.LATEX_TOKENS) or any(ch in frag for ch in cls.MATH_SYMBOLS):
                converted = cls._convert_unicode_symbols_to_latex(frag)
                return f"${converted}$"
            return frag

        # Match short inline expressions with math symbols
        # e.g., (x_i + y_i), \lambda_max, etc.
        inline_pattern = re.compile(
            r"(?<!\$)\b(?:[a-zA-Z]\s*=\s*[0-9a-zA-Z_^{}\+\-*/]+|[a-zA-Z]_[0-9a-zA-Z]+|[a-zA-Z]\^[0-9a-zA-Z]+|[∑∫∂√ππαβγδεζηθικλμνξοπρστυφχψω∆∇≤≥≠≈±×÷][0-9a-zA-Z_^{}\+\-*/\s=><]*)\b(?!\$)"
        )
        clean_text = inline_pattern.sub(repl_symbol_eq, clean_text)

        # Restore currency
        for key, val in placeholders.items():
            clean_text = clean_text.replace(key, val)

        return clean_text

    @classmethod
    def _convert_unicode_symbols_to_latex(cls, text: str) -> str:
        """Converts common unicode mathematical symbols to LaTeX representation."""
        mapping = {
            "∑": r"\sum ",
            "∫": r"\int ",
            "∂": r"\partial ",
            "√": r"\sqrt",
            "π": r"\pi ",
            "α": r"\alpha ",
            "β": r"\beta ",
            "γ": r"\gamma ",
            "δ": r"\delta ",
            "θ": r"\theta ",
            "λ": r"\lambda ",
            "μ": r"\mu ",
            "σ": r"\sigma ",
            "ω": r"\omega ",
            "∆": r"\Delta ",
            "∇": r"\nabla ",
            "≤": r"\le ",
            "≥": r"\ge ",
            "≠": r"\neq ",
            "≈": r"\approx ",
            "±": r"\pm ",
            "×": r"\times ",
            "÷": r"\div ",
            "∞": r"\infty ",
            "∈": r"\in ",
            "∉": r"\notin ",
        }
        res = text
        for u_char, lat in mapping.items():
            res = res.replace(u_char, lat)
        return res
