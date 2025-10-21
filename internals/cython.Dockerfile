FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG OPTFLAGS="-O3"
ENV CFLAGS="${OPTFLAGS}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
COPY cython_requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install -r cython_requirements.txt

COPY ./benchmarks ./benchmarks
WORKDIR /app/benchmarks

COPY ./build_cython_variants.sh /usr/local/bin/build_cython_variants.sh
RUN chmod +x /usr/local/bin/build_cython_variants.sh

RUN /usr/local/bin/build_cython_variants.sh /app/benchmarks
