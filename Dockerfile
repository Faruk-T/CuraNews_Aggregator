# CuraNews Aggregator — API image (Issue #20 / G20)
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.1.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock README.md ./
COPY src ./src
COPY web ./web
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN poetry install --only main --no-ansi \
    && python -m spacy download en_core_web_sm

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=50s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["python", "scripts/docker_entrypoint.py"]
