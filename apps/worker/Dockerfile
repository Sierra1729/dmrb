FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . celery redis

COPY packages/ ./packages/
COPY specs/ ./specs/
COPY reference/ ./reference/
COPY templates/ ./templates/
COPY apps/worker/ ./apps/worker/

ENV PYTHONPATH="/app/packages:/app/apps/api/src:/app/apps/worker/src"

WORKDIR /app/apps/worker/src

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
