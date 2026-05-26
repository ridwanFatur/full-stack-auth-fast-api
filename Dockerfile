# Stage 1: export dependencies using uv
FROM ghcr.io/astral-sh/uv:latest AS uv

FROM python:3.12-slim AS builder

# Copy the uv binary from the official image
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (layer cached separately from source code)
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the source code
COPY . .

RUN uv sync --frozen --no-dev


# Stage 2: production image
FROM python:3.12-slim AS runtime

# Create a non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app

# Copy the installed environment and application from builder
COPY --from=builder --chown=appuser:appgroup /app /app

USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
