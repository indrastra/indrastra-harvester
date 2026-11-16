FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY backend ./backend
COPY migrations ./migrations

RUN apt-get update && apt-get upgrade -y \
    && apt-get purge -y python3-setuptools \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip "setuptools>=78.1.1" \
    && find /usr/local/lib/python3.12/ensurepip/_bundled -type f -name "setuptools-*.whl" -delete \
    && find /usr/local/lib/python3.12 -iname "setuptools-70.3.0*" -exec rm -rf {} + \
    && python -c "import setuptools; assert tuple(map(int, setuptools.__version__.split('.')[:3])) >= (78, 1, 1)" \
    && pip install . \
    && groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
