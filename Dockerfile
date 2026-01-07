# Pin to 'bookworm' to avoid package name conflicts in Debian 'trixie'
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system dependencies and Poetry in one layer, then clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy Poetry configuration and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root \
    && rm -rf /root/.cache/pip/* /root/.cache/poetry/*

# Install Playwright and Chromium, then clean up
RUN poetry run playwright install chromium \
    && poetry run playwright install-deps chromium \
    && rm -rf /root/.cache/ms-playwright/* \
    && rm -rf /tmp/* /var/tmp/*

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
