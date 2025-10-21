FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python setup_cython.py build_ext --inplace
RUN useradd -m -u 1000 benchmark && chown -R benchmark:benchmark /app
USER benchmark
ENV PYTHONMALLOC=malloc
