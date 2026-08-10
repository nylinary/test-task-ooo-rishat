# --- Build stage: install locked dependencies into .venv with uv ------------
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.0 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# --- Runtime stage ----------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY --from=build /app/.venv /app/.venv
COPY . .

# `collectstatic` needs the settings module but no real secrets - the
# placeholder key never leaves the build step.
RUN DJANGO_SECRET_KEY=collectstatic-build-placeholder python manage.py collectstatic --noinput \
    && chown -R app:app /app

USER app

EXPOSE 8000

ENTRYPOINT ["./docker/entrypoint.sh"]
# Shell form on purpose: Railway injects the port to listen on via $PORT.
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile -
