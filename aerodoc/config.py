"""
AeroDoc Configuration Specification
Defines conversion parameters, layout tolerances, and export modes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class ConversionConfig:
    """Settings controlling the PDF to Markdown conversion process."""
    
    # Lossless content flags
    preserve_all_content: bool = True
    preserve_page_markers: bool = True
    include_frontmatter: bool = True
    include_toc: bool = True
    
    # Structural detectors
    detect_tables: bool = True
    detect_math: bool = True
    detect_code: bool = True
    detect_callouts: bool = True
    detect_links: bool = True
    
    # Layout handling
    unroll_columns: bool = True
    column_gap_threshold: float = 20.0
    suppress_headers_footers: bool = False  # Keep all content lossless
    
    # Image & Asset handling
    extract_images: bool = True
    embed_images: bool = False  # If True, embeds images as Base64 data URIs inside the .md file
    image_format: str = "png"
    min_image_width: int = 40
    min_image_height: int = 40
    assets_dir_name: str = "assets"
    
    # Text flow & clean-up
    rejoin_hyphenated_words: bool = True
    preserve_monospace: bool = True
    
    # Security & Guardrails
    max_file_size_bytes: int = 50 * 1024 * 1024  # 50 MB
    rate_limit_conversions_per_minute: int = 15
    rate_limit_requests_per_minute: int = 60

    # Output file paths
    output_path: Optional[Path] = None
    assets_path: Optional[Path] = None
