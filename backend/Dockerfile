FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY backend/pyproject.toml ./

# Install dependencies with uv (no venv, system install)
RUN uv pip install --system --no-cache \
    fastapi \
    "uvicorn[standard]" \
    python-multipart \
    pyyaml \
    "datacontract-cli[parquet]"

# Copy source
COPY backend/main.py ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
