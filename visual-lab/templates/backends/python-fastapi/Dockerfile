FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Test stage: `docker build --target test ./backend` runs the pytest suite
FROM base AS test
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
RUN python -m pytest -q

FROM base AS runtime
COPY app ./app
RUN useradd --create-home appuser
USER appuser
EXPOSE __API_PORT__
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "__API_PORT__", "--proxy-headers", "--forwarded-allow-ips", "*"]
