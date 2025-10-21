FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
COPY numba_requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install -r numba_requirements.txt

COPY ./benchmarks ./benchmarks
WORKDIR /app/benchmarks
