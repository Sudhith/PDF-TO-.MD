"""
AeroDoc - Enterprise Universal Document to Antigravity Markdown Converter
"""

from aerodoc.config import ConversionConfig
from aerodoc.core.converter import PDFConverter
from aerodoc.core.universal_converter import UniversalConverter

__version__ = "2.0.0"
__all__ = ["ConversionConfig", "PDFConverter", "UniversalConverter"]
