FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml ./
COPY src/ ./src/
COPY configs/ ./configs/

RUN pip install -e .

ENV PYTHONPATH=/app/src

EXPOSE 8080

CMD ["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8080"]
