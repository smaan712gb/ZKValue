FROM python:3.13-slim

WORKDIR /app

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

# Create storage directory
RUN mkdir -p /app/storage && chown -R zkvalue:zkvalue /app/storage

USER zkvalue

EXPOSE 8000

# Production: gunicorn with uvicorn workers
# Override CMD in docker-compose.yml for development (uvicorn --reload)
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
