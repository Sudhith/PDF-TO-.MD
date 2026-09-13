# AeroDoc: Enterprise Document Intelligence & Universal Markdown Synthesizer

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FSudhith%2FPDF-TO-.MD)
[![License: MIT](https://img.shields.io/badge/License-MIT-d4af37.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-lightgrey.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-10141d.svg)](https://fastapi.tiangolo.com)
[![Status: Production](https://img.shields.io/badge/Status-Production%20Ready-d4af37.svg)](#)

AeroDoc is an institutional-grade document ingestion and layout-aware Markdown synthesis engine engineered for **Google Antigravity**, executive workflows, and advanced AI code assistants. Designed with an executive architectural aesthetic inspired by Apple and premier financial platforms, AeroDoc transforms multi-format corporate and technical documentation into pristine, publication-grade GitHub-Flavored Markdown (GFM) with YAML metadata, Antigravity alerts, and zero synthetic AI trace.

---

## 1-Click Deployment to Vercel

AeroDoc is fully optimized for serverless edge deployment on **Vercel** with zero configuration required.

### Option A: 1-Click Instant Deploy
Click the button below to fork and deploy directly to your Vercel account:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FSudhith%2FPDF-TO-.MD)

### Option B: Deploy via Vercel CLI
```bash
# 1. Clone repository
git clone https://github.com/Sudhith/PDF-TO-.MD.git
cd "PDF-TO-.MD"

# 2. Deploy to production
npx vercel --prod
```

### Serverless Architecture on Vercel:
- **Edge Static CDN (`/public`)**: Serves the executive studio frontend (`index.html`, `style.css`, `app.js`) from Vercel's global edge network with sub-millisecond cold start.
- **Python Serverless Runtime (`/api/index.py`)**: Executes high-throughput document AST transformation in AWS Lambda / Amazon Linux containers.
- **Dynamic Routing (`vercel.json`)**: Seamlessly proxies `/api/*` and `/health` requests to the FastAPI ASGI application.
- **Stateless Client-Side In-Memory Downloads**: Generates instant Blob URLs for zero-latency downloads while immediately triggering ephemeral purge on the server.

---

## Universal Multi-Format Ingestion

| Format | Extensions | Processing Mechanism |
| :--- | :--- | :--- |
| **PDF Documents** | `.pdf` | Spatial layout clustering, multi-column topology unrolling, vector tables, and KaTeX math extraction |
| **Microsoft Word** | `.docx`, `.doc` | Native XML AST traversal, style hierarchy mapping, inline tables, callout detection |
| **Tabular Data** | `.csv`, `.tsv` | RFC-4180 streaming parser with GFM pipe-delimited table generator and markdown escaping |
| **Web & Hypertext** | `.html`, `.htm` | Clean DOM subtree normalization, semantics preservation, boilerplate stripping |
| **Plain Text / Logs** | `.txt`, `.text`, `.log` | Monospace formatting, code fence detection, heading inference |
| **Structured Data** | `.json`, `.yaml`, `.rtf` | Formatted code blocks with automated syntax classification |

---

## Executive Design Principles

- **Zero Blue Policy**: Strictly curated monochrome palette of Obsidian Carbon (`#060709`), Titanium Silver (`#e2e8f0`), Slate Chrome (`#94a3b8`), and Platinum Gold (`#d4af37`).
- **Zero Emojis**: 100% replaced by precision 1.5px hairline vector SVGs (Apple SF Symbols / Linear design style).
- **Dual-Engine Blueprint Viewport**: Real-time side-by-side comparison between original document pages/schematics and rendered Antigravity AST.
- **Real-Time Telemetry Matrix**: Live feedback on document classification, readability grade, word count, tables extracted, equations parsed, and execution velocity.

---

## Security & Reliability Guardrails

- **Magic-Byte Stream Inspection**: Enforces true binary header validation (e.g. `%PDF-`) preventing malicious file masquerading.
- **Path Traversal Sanitization**: Strict filename neutralization rejecting `../`, hidden prefixes, and special characters.
- **Sliding-Window Velocity Limiter**: Per-IP sliding window tracking (25 conversions/min) returning `429 Too Many Requests` with RFC `Retry-After`.
- **Ephemeral Post-Download Zeroing**: Immediately overwrites file memory buffers with `b""` and unlinks temporary sessions upon download.
- **Defensive Headers**: Production headers enforced via middleware:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`

---

## Local Development & Self-Hosting

### 1. Run with Uvicorn (FastAPI)
```bash
# Install dependencies
pip install -r requirements.txt

# Start local server
python -m uvicorn aerodoc.web.server:app --host 0.0.0.0 --port 8765
```
Open [http://localhost:8765](http://localhost:8765) in your browser.

### 2. Command Line Interface (CLI)
```bash
# Convert a single document (auto-detects format)
python -m aerodoc.cli convert financial_report.pdf -o output.md

# Convert with Base64 embedded graphics (single self-contained .md)
python -m aerodoc.cli convert research_paper.pdf -o paper.md --embed-images

# Batch convert an entire directory
python -m aerodoc.cli batch ./documents -o ./markdown_archive
```

### 3. Run Test Suite
```bash
pytest -v
```
All 13 unit, security, and multi-format integration tests will verify:
- Lossless AST conversion
- Magic-byte verification
- Sliding-window rate limiter
- DOCX, CSV, HTML, and PDF pipelines
- Ephemeral zero-wipe cleanup

---

## License

MIT License. Designed and engineered for high-consequence enterprise applications and Antigravity pair programming.
