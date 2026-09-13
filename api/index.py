"""
Vercel Serverless Entrypoint for AeroDoc
Exposes the FastAPI application to Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from aerodoc.web.server import app
