FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for cache
COPY pyproject.toml .
COPY alembic.ini .

# Install production dependencies
RUN uv sync --no-dev --frozen --no-install-project

# Copy source
COPY app/ app/
COPY migrations/ migrations/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
