# # Stage 1: Build the app and install dependencies
# FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# WORKDIR /app

# # Set UV environment variables following uv best practices
# ENV UV_COMPILE_BYTECODE=1
# ENV UV_LINK_MODE=copy
# # Disable Python downloads to use system interpreter (matches final image)
# ENV UV_PYTHON_DOWNLOADS=0

# # Install dependencies using bind mounts for optimal caching
# RUN --mount=type=cache,target=/root/.cache/uv \
#     --mount=type=bind,source=uv.lock,target=uv.lock \
#     --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#     uv sync --locked --no-install-project --no-dev

# # Copy source code and install the project (including guardrails)
# COPY . /app
# RUN --mount=type=cache,target=/root/.cache/uv \
#     uv sync --locked --no-dev

# # Install Guardrails Hub validators after guardrails is available
# ARG GUARDRAILS_HUB_API_KEY
# RUN if [ -z "$GUARDRAILS_HUB_API_KEY" ]; then \
#         echo "ERROR: GUARDRAILS_HUB_API_KEY build arg is required" && exit 1; \
#     fi && \
#     echo "Configuring Guardrails..." && \
#     /app/.venv/bin/guardrails configure --token "$GUARDRAILS_HUB_API_KEY" --disable-metrics --enable-remote-inferencing

# RUN --mount=type=cache,target=/root/.cache/guardrails \
#     echo "Installing toxic_language validator..." && \
#     /app/.venv/bin/guardrails hub install hub://guardrails/toxic_language

# RUN --mount=type=cache,target=/root/.cache/guardrails \
#     echo "Installing detect_jailbreak validator..." && \
#     /app/.venv/bin/guardrails hub install hub://guardrails/detect_jailbreak

# RUN --mount=type=cache,target=/root/.cache/guardrails \
#     echo "Installing secrets_present validator..." && \
#     /app/.venv/bin/guardrails hub install hub://guardrails/secrets_present && \
#     echo "Guardrails setup complete!"

# # Aggressive cleanup to reduce image size
# RUN find /app -type d \( \
#         -name "__pycache__" -o \
#         -name "*.dist-info" -o \
#         -name "*.egg-info" -o \
#         -name "tests" -o \
#         -name "test" -o \
#         -name "docs" -o \
#         -name "examples" -o \
#         -name ".pytest_cache" -o \
#         -name ".git" -o \
#         -name ".github" -o \
#         -name "node_modules" \
#     \) -exec rm -rf {} + 2>/dev/null || true && \
#     find /app -type f \( \
#         -name "*.pyc" -o \
#         -name "*.pyo" -o \
#         -name "*.pyd" -o \
#         -name "*.so" -o \
#         -name "*.a" -o \
#         -name "*.la" -o \
#         -name "*.o" -o \
#         -name "*.c" -o \
#         -name "*.cpp" -o \
#         -name "*.h" -o \
#         -name "*.hpp" -o \
#         -name "*.md" -o \
#         -name "*.rst" -o \
#         -name "*.txt" -o \
#         -name "LICENSE*" -o \
#         -name "CHANGELOG*" -o \
#         -name "README*" -o \
#         -name ".DS_Store" -o \
#         -name "Makefile" \
#     \) -delete 2>/dev/null || true && \
#     # Remove unnecessary pip files
#     rm -rf /app/.venv/lib/python*/site-packages/pip* 2>/dev/null || true && \
#     rm -rf /app/.venv/lib/python*/site-packages/setuptools* 2>/dev/null || true && \
#     rm -rf /app/.venv/lib/python*/site-packages/wheel* 2>/dev/null || true && \
#     # Remove test files from installed packages
#     find /app/.venv -name "test*" -type d -exec rm -rf {} + 2>/dev/null || true && \
#     find /app/.venv -name "*test*" -name "*.py" -delete 2>/dev/null || true && \
#     # Clean up guardrails cache if any
#     rm -rf ~/.cache/guardrails 2>/dev/null || true

# # Stage 2: Final runtime image without uv
# FROM python:3.12-slim-bookworm AS runtime

# # Create non-root user for security
# RUN groupadd -r appuser && useradd -r -g appuser appuser

# WORKDIR /app

# # Install only runtime system dependencies
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#         ca-certificates \
#         && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# # Copy ONLY the virtual environment and source code (not the entire /app directory)
# COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
# COPY --from=builder --chown=appuser:appuser /app/src /app/src

# # Set environment variables for production
# ENV PATH="/app/.venv/bin:$PATH"
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONDONTWRITEBYTECODE=1

# # Switch to non-root user
# USER appuser

# # Health check for container orchestration
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# # Expose port
# EXPOSE 8000

# # Use exec form for production
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]


# Stage 1: Build the app and install dependencies
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Set UV environment variables following uv best practices
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

# Install dependencies using bind mounts for optimal caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy source code and install the project (including guardrails)
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Install Guardrails Hub validators after guardrails is available
ARG GUARDRAILS_HUB_API_KEY
RUN if [ -z "$GUARDRAILS_HUB_API_KEY" ]; then \
        echo "ERROR: GUARDRAILS_HUB_API_KEY build arg is required" && exit 1; \
    fi && \
    echo "Configuring Guardrails..." && \
    /app/.venv/bin/guardrails configure --token "$GUARDRAILS_HUB_API_KEY" --disable-metrics --enable-remote-inferencing

RUN --mount=type=cache,target=/root/.cache/guardrails \
    echo "Installing toxic_language validator..." && \
    /app/.venv/bin/guardrails hub install hub://guardrails/toxic_language

RUN --mount=type=cache,target=/root/.cache/guardrails \
    echo "Installing detect_jailbreak validator..." && \
    /app/.venv/bin/guardrails hub install hub://guardrails/detect_jailbreak

RUN --mount=type=cache,target=/root/.cache/guardrails \
    echo "Installing secrets_present validator..." && \
    /app/.venv/bin/guardrails hub install hub://guardrails/secrets_present && \
    echo "Guardrails setup complete!"

# Aggressive cleanup to reduce image size
RUN find /app -type d \( \
        -name "__pycache__" -o \
        -name "*.dist-info" -o \
        -name "*.egg-info" -o \
        -name "tests" -o \
        -name "test" -o \
        -name "docs" -o \
        -name "examples" -o \
        -name ".pytest_cache" -o \
        -name ".git" -o \
        -name ".github" -o \
        -name "node_modules" \
    \) -exec rm -rf {} + 2>/dev/null || true && \
    find /app -type f \( \
        -name "*.pyc" -o \
        -name "*.pyo" -o \
        -name "*.pyd" -o \
        -name "*.so" -o \
        -name "*.a" -o \
        -name "*.la" -o \
        -name "*.o" -o \
        -name "*.c" -o \
        -name "*.cpp" -o \
        -name "*.h" -o \
        -name "*.hpp" -o \
        -name "*.md" -o \
        -name "*.rst" -o \
        -name "*.txt" -o \
        -name "LICENSE*" -o \
        -name "CHANGELOG*" -o \
        -name "README*" -o \
        -name ".DS_Store" -o \
        -name "Makefile" \
    \) -delete 2>/dev/null || true && \
    # Remove unnecessary pip files
    rm -rf /app/.venv/lib/python*/site-packages/pip* 2>/dev/null || true && \
    rm -rf /app/.venv/lib/python*/site-packages/setuptools* 2>/dev/null || true && \
    rm -rf /app/.venv/lib/python*/site-packages/wheel* 2>/dev/null || true && \
    # Remove test files from installed packages
    find /app/.venv -name "test*" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -name "*test*" -name "*.py" -delete 2>/dev/null || true && \
    # Clean up guardrails cache if any
    rm -rf ~/.cache/guardrails 2>/dev/null || true

# Stage 2: Final runtime image without uv
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy ONLY the virtual environment and source code (not the entire /app directory)
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment variables for production
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Use exec form for production
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
