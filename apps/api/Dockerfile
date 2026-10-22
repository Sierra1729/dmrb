FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy packages and code
COPY packages/ ./packages/
COPY specs/ ./specs/
COPY reference/ ./reference/
COPY templates/ ./templates/
COPY apps/api/ ./apps/api/

ENV PYTHONPATH="/app/packages:/app/apps/api/src"

WORKDIR /app/apps/api/src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
