# ---------- build stage ----------
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Устанавливаем системные зависимости для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --no-dev

# ---------- runtime stage ----------
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ENV PATH="/app/.venv/bin:$PATH"


WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src ./src

# Запуск
CMD ["python", "-m", "src.main"]