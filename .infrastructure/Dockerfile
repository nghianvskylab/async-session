ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-alpine AS base

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    PATH="/root/.local/bin:$PATH"

RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    postgresql-libs \
    curl \
    python3-dev

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi

COPY api/ api/
COPY api/migrations/ api/migrations/
COPY alembic.ini alembic.ini
COPY Makefile Makefile

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

