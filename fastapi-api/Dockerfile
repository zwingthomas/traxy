# 1. Build stage: install dependencies
FROM python:3.9-slim AS builder

# Set workdir and ensure logs go to stdout
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       gcc \
       libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your backend source
COPY . .

# 2. Slim runtime image
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.9/site-packages \
                    /usr/local/lib/python3.9/site-packages
# Copy console scripts from builder (for alembic)
COPY --from=builder /usr/local/bin \
                    /usr/local/bin
# Copy app
COPY --from=builder /app /app

# Expose the port
EXPOSE $PORT

# Entrypoint: run migrations then start uvicorn
ENTRYPOINT ["bash", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT"]