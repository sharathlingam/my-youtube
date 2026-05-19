FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for cache
COPY pyproject.toml .
COPY uv.lock .
COPY alembic.ini .

# Install production dependencies
RUN uv sync --no-dev --frozen --no-install-project

# Copy source
COPY app/ app/
COPY migrations/ migrations/
COPY start.sh .

RUN chmod +x start.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["./start.sh"]
