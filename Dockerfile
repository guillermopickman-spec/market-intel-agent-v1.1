# syntax=docker/dockerfile:1.4
# Pin to 'bookworm' to avoid package name conflicts in Debian 'trixie'
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system dependencies and Poetry with cache mounts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && curl -sSL https://install.python-poetry.org | python3 -

# Copy Poetry configuration and install dependencies with cache mounts
COPY pyproject.toml poetry.lock* ./
# Configure pip timeout (but don't use progress_bar - it can slow things down)
RUN pip config set global.timeout 600
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/pypoetry \
    poetry config installer.max-workers 4 && \
    poetry install --no-interaction --no-ansi --no-root

# Install Playwright and Chromium with cache mount (keeps browser cache between builds)
RUN --mount=type=cache,target=/root/.cache/ms-playwright \
    poetry run playwright install chromium \
    && poetry run playwright install-deps chromium || true

# Copy application code
COPY . .

# Create directory for ChromaDB persistence with proper permissions
RUN mkdir -p /app/chroma_db && chmod 777 /app/chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
