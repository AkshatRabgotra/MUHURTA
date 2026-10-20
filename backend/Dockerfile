# ──────────────────────────────────────────────────────────────────────────
# Muhurta Planner – Backend Dockerfile (multi-stage)
# ──────────────────────────────────────────────────────────────────────────

# ── Stage 1: build ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# System deps needed to compile C extensions (asyncpg, pyswisseph, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual-env so we can copy cleanly.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ── Download Swiss Ephemeris data files ──────────────────────────────────
RUN mkdir -p /opt/swe_data \
    && pip install --no-cache-dir pyswisseph \
    && python -c "\
import swisseph as swe; \
import os, urllib.request, zipfile, io; \
url = 'https://www.astro.com/ftp/swisseph/ephe/sweph_18.zip'; \
print(f'Downloading {url} ...'); \
data = urllib.request.urlopen(url).read(); \
zipfile.ZipFile(io.BytesIO(data)).extractall('/opt/swe_data'); \
print('Swiss Ephemeris data extracted to /opt/swe_data')" \
    || echo "WARN: Swiss Ephemeris download failed – ephemeris files can be mounted at runtime."

# ── Stage 2: runtime ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SWE_EPHE_PATH=/opt/swe_data

WORKDIR /app

# Minimal runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual-env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Swiss Ephemeris data
COPY --from=builder /opt/swe_data /opt/swe_data

# Copy application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
