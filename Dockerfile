# ============================================================
# Dockerfile — Production-ready Flask CTF Platform
# Multi-stage: builder stage installs deps; runtime is slim
# Non-root user for security
# ============================================================

# -- Stage 1: Builder --
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# -- Stage 2: Runtime --
FROM python:3.11-slim AS runtime

# Security: run as non-root
RUN useradd -m -u 1000 ctfuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy app source
COPY . .

# Create required directories with correct permissions
RUN mkdir -p instance app/static/uploads && \
    chown -R ctfuser:ctfuser /app

USER ctfuser

# Environment
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/auth/login')"

# Gunicorn entrypoint: 4 workers, graceful timeout
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", \
     "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", \
     "run:app"]
