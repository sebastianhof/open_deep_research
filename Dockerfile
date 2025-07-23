# Use uv's Python base image
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy all necessary files for the build
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
COPY tests/ tests/

# Install dependencies (including the local package)
RUN uv sync --frozen --no-cache

# Expose port
EXPOSE 8080

# Run application
CMD ["uv", "run", "uvicorn", "src.agent:app", "--host", "0.0.0.0", "--port", "8080"]