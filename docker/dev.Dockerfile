# Multi-stage Docker build for Python application with Guardrails
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

# UV configuration for optimized builds
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_INSTALL_DIR=/python
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for better caching
RUN uv python install 3.12

# Install runtime dependencies, including Git
RUN apt-get update && apt-get install -y \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better Docker layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy only necessary files for the project installation
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Set the directory for nltk data
ENV NLTK_DATA=/opt/nltk_data

# Download NLTK data (punkt tokenizer and other common data)
RUN --mount=type=cache,target=/root/.cache/nltk \
    uv run python -m nltk.downloader -d /opt/nltk_data punkt stopwords wordnet averaged_perceptron_tagger

# Configure guardrails using build secret
RUN --mount=type=secret,id=GUARDRAILS_API_KEY \
    uv run guardrails configure --token "$(cat /run/secrets/GUARDRAILS_API_KEY)" \
                                --disable-metrics \
                                --enable-remote-inferencing

# Cache both the download and install locations
RUN --mount=type=cache,target=/root/.cache/guardrails \
    --mount=type=cache,target=/root/.guardrails \
    --mount=type=cache,target=/tmp/guardrails-install \
    uv run guardrails hub install hub://guardrails/toxic_language && \
    uv run guardrails hub install hub://guardrails/detect_jailbreak && \
    uv run guardrails hub install hub://guardrails/secrets_present

# Production stage - minimal runtime image
FROM debian:bookworm-slim

# Copy Python installation from builder
COPY --from=builder /python /python

# Set working directory
WORKDIR /app

# Copy application and virtual environment from builder
COPY --from=builder /app /app

# Copy NLTK data from builder
COPY --from=builder /opt/nltk_data /opt/nltk_data

# Copy guardrails config
COPY --from=builder /root/.guardrailsrc /root/.guardrailsrc

# Set PATH to include Python and virtual environment
ENV PATH="/python/bin:/app/.venv/bin:$PATH"
ENV NLTK_DATA=/opt/nltk_data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# FastAPI command
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
