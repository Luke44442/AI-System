FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip wheel
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgbm1 libasound2 libxrandr2 libxdamage1 libxcomposite1 libxfixes3 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
RUN playwright install chromium --with-deps
RUN groupadd --gid 1001 appgroup && useradd --uid 1001 --gid appgroup --no-create-home --shell /bin/false appuser
COPY app/ ./app/
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
