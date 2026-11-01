FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install only the runtime dependencies needed by the API.
COPY pyproject.toml README.md ./

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./

RUN python -m pip install --upgrade pip \
    && python -m pip install .

# Use a non-root account for the application process.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/local_documents \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
