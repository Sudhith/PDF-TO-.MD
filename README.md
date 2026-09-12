# AeroDoc: Lossless Intelligent PDF-to-Markdown Engine

AeroDoc is an intelligent, layout-aware PDF-to-Markdown engine and interactive Web Studio engineered specifically for **Antigravity** and modern AI coding environments. It converts complex PDFs—including multi-column scientific papers, engineering manuals, mathematical equations, formatted tables, code listings, and graphics—into clean, structured GitHub-Flavored Markdown (GFM) with YAML metadata, Antigravity callout alerts, and zero synthetic AI conversational artifacts.

---

## Key Features

- **100% Lossless Content Guarantee**: Every word, table cell, footnote, figure, and page boundary is preserved.
- **Dynamic Multi-Column Topology Unrolling**: Automatically detects 2-column or 3-column layouts and orders reading blocks naturally (eliminates cross-column text interleaving).
- **GFM Table Recognition**: Extracts clean tabular data directly into markdown tables with pipe formatting and escaping.
- **Antigravity Alert Conversion**: Automatically recognizes notes, warnings, tips, and cautions and converts them to standard Antigravity alerts (`> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!CAUTION]`).
- **KaTeX Math Engine**: Translates mathematical symbols and formulas into inline `$ ... $` and display `$$ ... $$` blocks.
- **Embedded or Bundled Figures**: Choose between standalone single-file `.md` (with inline Base64 graphics) or bundled assets directory.
- **Unique Dynamic Filenames**: Each download receives a timestamped, cryptographically tagged unique filename.
- **Immediate Post-Download Ephemeral Purge**: Automatically zeros and purges temporary files on the server immediately after download.
- **Hardened Security Layer**: Magic-byte (`%PDF-`) verification, 50MB file size ceiling, and strict path traversal defenses.
- **Sliding-Window Rate Limiting**: Per-IP velocity tracking preventing server abuse with automatic `Retry-After` headers.
- **High-Voltage Bright UI (Zero Blue)**: Electric Neon Lime, Solar Gold, and Neon Fuchsia obsidian dark studio.

---

## How to Use AeroDoc

### 1. Launch the Interactive Web Studio
```bash
python -m aerodoc.cli serve --port 8765
```
Open `http://localhost:8765` in your browser.

#### Studio Workflow:
1. **Document Ingestion**: Drag and drop any `.pdf` document into the upload zone, or click **Load Sample Test PDF** to test with the built-in quantum architecture benchmark document.
2. **Parameters**: Toggle options such as **Embed Images (Base64)** for single-file standalone markdown, **Multi-Column Unrolling**, or **KaTeX Math Engine**.
3. **Convert**: Click **Convert to Markdown** or press `Ctrl + Enter`.
4. **Inspect & Verify**: Use the split pane to inspect original PDF pages side-by-side with live formatted Markdown, KaTeX math formulas, and code syntax highlighting.
5. **Export**: Click **Download .MD** or **Copy**. The temporary file on the server is zeroed and wiped immediately after transmission.

---

### 2. Command Line Interface (CLI)

#### Convert a Single PDF
```bash
python -m aerodoc.cli convert document.pdf -o output.md
```

#### Convert to a 100% Self-Contained Standalone .md (Embed Images as Base64)
```bash
python -m aerodoc.cli convert document.pdf -o standalone.md --embed-images
```

#### Batch Convert an Entire Directory
```bash
python -m aerodoc.cli batch ./input_folder -o ./output_folder
```

---

## Architecture & Security Audit

- **Typed Exceptions**:
  - `InvalidPDFMagicByteError` (HTTP 415)
  - `OversizedFileError` (HTTP 413)
  - `EncryptedPDFError` (HTTP 422)
  - `CorruptedPDFError` (HTTP 400)
  - `RateLimitExceededError` (HTTP 429)
- **Defensive Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1`, `Referrer-Policy: strict-origin-when-cross-origin`.
- **Zero-Trace Sanitization**: Guarantees zero synthetic AI conversational chatter in converted `.md` artifacts.
