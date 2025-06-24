# Multi-stage Docker build for Python application with Guardrails
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

# Build arguments for secrets (passed at build time)
ARG GUARDRAILS_API_KEY

# UV configuration for optimized builds
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_INSTALL_DIR=/python
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for better caching
RUN uv python install 3.12

WORKDIR /app

# Install dependencies first (better Docker layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy the entire project
COPY . /app

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Production stage - minimal runtime image
FROM debian:bookworm-slim

# Create app user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Install runtime dependencies, including Git
RUN apt-get update && apt-get install -y \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python installation from builder
COPY --from=builder --chown=app:app /python /python

# Copy application and virtual environment from builder
COPY --from=builder --chown=app:app /app /app

# Switch to app user
USER app

# Set working directory
WORKDIR /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Configure guardrails as the app user with the API key from build arg or env
ARG GUARDRAILS_API_KEY
ENV GUARDRAILS_API_KEY=${GUARDRAILS_API_KEY}

# Configure guardrails and install validators as the app user
RUN if [ -n "$GUARDRAILS_API_KEY" ]; then \
        /app/.venv/bin/guardrails configure --token $GUARDRAILS_API_KEY --disable-metrics --enable-remote-inferencing && \
        /app/.venv/bin/guardrails hub install hub://guardrails/toxic_language && \
        /app/.venv/bin/guardrails hub install hub://guardrails/detect_jailbreak && \
        /app/.venv/bin/guardrails hub install hub://guardrails/secrets_present; \
    else \
        echo "GUARDRAILS_API_KEY not provided, skipping guardrails setup"; \
    fi

# Expose port (adjust as needed)
EXPOSE 8000

# Default command - adjust based on your FastAPI app structure
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
