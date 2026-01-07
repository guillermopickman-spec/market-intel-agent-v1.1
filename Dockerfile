# Pin to 'bookworm' to avoid package name conflicts in Debian 'trixie'
FROM python:3.11-slim-bookworm

# 1. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 2. Install core system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/*

# 3. Copy Poetry configuration
COPY pyproject.toml poetry.lock* ./

# 4. Install Python dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# 5. Install Playwright and dependencies (required for Docker/Linux)
# Install Chromium browser first, then system dependencies
RUN poetry run playwright install chromium && \
    poetry run playwright install-deps chromium

# 6. Copy application code
COPY . .

# 7. Create directory for ChromaDB persistence with proper permissions
RUN mkdir -p /app/chroma_db && \
    chmod 777 /app/chroma_db

# 8. Expose port
EXPOSE 8000

# 9. Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 10. Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]