FROM python:3.13-slim

WORKDIR /app

# Cache-bust: v2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Create non-root user
RUN groupadd -r zkvalue && useradd -r -g zkvalue -d /app -s /sbin/nologin zkvalue

COPY . .

# Create writable directories for non-root user
RUN mkdir -p /app/storage /app/data && chown -R zkvalue:zkvalue /app/storage /app/data /app

USER zkvalue

EXPOSE 8080

CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
