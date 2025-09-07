FROM python:3.12-slim

# Avoid interactive tzdata, speed up installs
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (curl for healthchecks, and minimal build/runtime libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Build arg to toggle dev dependencies
ARG ENVIRONMENT=prod

# Install Python dependencies first (leverage layer caching)
COPY requirements/ /app/requirements/
RUN pip install --upgrade pip \
    && if [ "$ENVIRONMENT" = "dev" ]; then \
         pip install -r /app/requirements/requirements_dev.txt; \
       else \
         pip install -r /app/requirements/requirements.txt; \
       fi \
    && python -m spacy download en_core_web_sm

# Copy application code
COPY src /app/src
COPY README.md /app/README.md

# Create runtime dirs (persisted via volumes in docker-compose)
RUN mkdir -p /app/chroma_db /app/output /app/raw_pdfs

# Default command is a shell; use docker compose run for tasks
CMD ["bash"]
