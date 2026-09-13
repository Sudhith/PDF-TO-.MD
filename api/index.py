"""
Vercel Serverless Entrypoint for AeroDoc
Exposes the FastAPI application to Vercel's Python runtime.
"""

import sys
import traceback
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Top-level FastAPI instance recognized by Vercel static analysis
app = FastAPI(title="AeroDoc Universal Engine")

try:
    import aerodoc.web.server
    app = aerodoc.web.server.app
except Exception as e:
    _err_msg = str(e)
    _err_tb = traceback.format_exc()

    @app.api_route("/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def debug_error(request: Request, rest_of_path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "AeroDoc serverless initialization failed",
                "exception": _err_msg,
                "traceback": _err_tb,
                "path": request.url.path,
                "sys_path": sys.path
            }
        )


