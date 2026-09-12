# Multi-stage production Dockerfile for AeroDoc
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production runner stage
FROM python:3.13-slim

WORKDIR /app

# Install runtime libraries for MuPDF and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed wheels/packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY aerodoc ./aerodoc
COPY README.md pyproject.toml ./

# Run as non-root user for enterprise security
RUN useradd -m -u 1001 aerodoc && \
    chown -R aerodoc:aerodoc /app
USER aerodoc

ENV HOST=0.0.0.0
ENV PORT=8765
ENV PYTHONUNBUFFERED=1

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8765/ || exit 1

CMD ["uvicorn", "aerodoc.web.server:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "2"]
