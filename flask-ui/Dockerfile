# ─────────────────────────────────────────────────────────────
# Stage 1: Build Tailwind CSS
# ─────────────────────────────────────────────────────────────
FROM node:18-alpine AS tailwind-builder

# Switch into a known workdir
WORKDIR /app

# Copy only package files & install—enables caching
COPY package*.json ./
RUN npm ci

# Copy all frontend source
COPY . .

# Build Tailwind CSS
RUN npm run build:css 

# Clean up node_modules to keep the build context small
RUN rm -rf node_modules

# ─────────────────────────────────────────────────────────────
# Stage 2: Python runtime for Flask UI
# ─────────────────────────────────────────────────────────────
FROM python:3.9-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    API_BASE_URL=https://traxy-backend-378890077459.us-central1.run.app

# Install any OS-level deps your requirements might need
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask app code & the freshly built CSS
COPY --from=tailwind-builder /app /app

# Expose the Cloud Run port
EXPOSE $PORT

# Gunicorn entrypoint
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]