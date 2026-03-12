# ZKValue — Railway Deployment Guide

## Architecture on Railway

```
┌─────────────────────────────────────────────────────────┐
│  Railway Project: ZKValue                                │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │
│  │ Postgres │  │  Redis   │  │   Frontend (Next.js)   │ │
│  │ (plugin) │  │ (plugin) │  │   → public domain      │ │
│  └────┬─────┘  └────┬─────┘  │   → proxies /api/*     │ │
│       │              │        └────────────┬───────────┘ │
│       │              │                     │ rewrites    │
│       ▼              ▼                     ▼             │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Backend (FastAPI)                     │   │
│  │              → internal only                      │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│       ┌─────────────┼─────────────┐                     │
│       ▼                           ▼                     │
│  ┌──────────────┐  ┌──────────────────┐                 │
│  │ Celery Worker │  │  Celery Beat     │                 │
│  │ (async tasks) │  │ (scheduled jobs) │                 │
│  └──────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

1. [Railway CLI](https://docs.railway.com/guides/cli) installed
2. GitHub repo pushed (https://github.com/smaan712gb/ZKValue)
3. Railway account with a project created

## Step-by-Step Deployment

### 1. Create Railway Project

```bash
railway login
railway init    # or link to existing project
```

### 2. Add Database Plugins

In the Railway dashboard:
- Click **+ New** → **Database** → **PostgreSQL**
- Click **+ New** → **Database** → **Redis**

### 3. Create Backend Service

In the Railway dashboard:
- Click **+ New** → **GitHub Repo** → Select `ZKValue`
- **Settings**:
  - Root Directory: `backend`
  - Builder: Dockerfile
  - Start Command: (leave empty, railway.toml handles it)
  - Healthcheck Path: `/health`

**Environment Variables** (Settings → Variables):
```
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Then manually replace postgresql:// with postgresql+asyncpg://
REDIS_URL=${{Redis.REDIS_URL}}
SECRET_KEY=<generate-secure-random-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEEPSEEK_API_KEY=<your-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
DEFAULT_LLM_PROVIDER=deepseek
DEFAULT_LLM_MODEL=deepseek-chat
STRIPE_SECRET_KEY=<your-key>
STRIPE_WEBHOOK_SECRET=<your-key>
S3_BUCKET=zkvalue-reports
AWS_ACCESS_KEY=<your-key>
AWS_SECRET_KEY=<your-key>
AWS_REGION=us-east-1
CORS_ORIGINS=["https://your-frontend.up.railway.app"]
APP_NAME=ZKValue
APP_VERSION=1.0.0
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend.up.railway.app
```

**Important**: Do NOT generate a public domain for the backend. Keep it internal-only.

### 4. Create Celery Worker Service

- Click **+ New** → **GitHub Repo** → Select `ZKValue`
- **Settings**:
  - Root Directory: `backend`
  - Builder: Dockerfile
  - Start Command: `celery -A app.workers.celery_app worker --loglevel=info --concurrency=4`
  - No healthcheck needed

**Environment Variables**: Same as Backend (use shared variable group or copy).

### 5. Create Celery Beat Service

- Click **+ New** → **GitHub Repo** → Select `ZKValue`
- **Settings**:
  - Root Directory: `backend`
  - Builder: Dockerfile
  - Start Command: `celery -A app.workers.celery_app beat --loglevel=info`
  - No healthcheck needed

**Environment Variables**: Same as Backend.

### 6. Create Frontend Service

- Click **+ New** → **GitHub Repo** → Select `ZKValue`
- **Settings**:
  - Root Directory: `frontend`
  - Builder: Dockerfile
  - Healthcheck Path: `/`

**Environment Variables**:
```
NEXT_PUBLIC_API_URL=/api/v1
NEXT_PUBLIC_APP_NAME=ZKValue
BACKEND_INTERNAL_URL=http://backend.railway.internal:PORT
```

**Note**: `BACKEND_INTERNAL_URL` uses Railway's private networking. Get the backend's internal hostname from its service settings. The Next.js rewrites in `next.config.ts` will proxy `/api/*` requests to the backend.

**Generate Public Domain**: Click **Settings** → **Networking** → **Generate Domain** (or add custom domain).

### 7. Custom Domain (Optional)

To use a custom domain like `zkvalue.io`:
1. Go to Frontend service → Settings → Networking
2. Add custom domain
3. Update DNS with the CNAME record Railway provides
4. Update `CORS_ORIGINS` and `FRONTEND_URL` in Backend variables

## Environment Variable Groups

Railway supports **shared variables** to avoid duplicating env vars across Backend/Worker/Beat:

1. Go to Project Settings → Shared Variables
2. Add all backend env vars there
3. Reference them in each service

## Database Migration

After first deploy, run migrations via Railway CLI:
```bash
railway run --service backend -- python -c "
import asyncio
from app.core.database import engine
from app.models import *
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(migrate())
"
```

Or use the Railway shell:
```bash
railway shell --service backend
python -c "import asyncio; from app.core.database import engine; from app.models import *; asyncio.run(engine.begin().__aenter__().then(lambda c: c.run_sync(Base.metadata.create_all)))"
```

## Monitoring

- Railway provides built-in logs, metrics, and alerting
- Set `SENTRY_DSN` for error tracking
- Backend healthcheck at `/health` is monitored by Railway

## Cost Estimate

| Service         | Estimated Monthly Cost |
|-----------------|----------------------|
| PostgreSQL      | ~$5-15               |
| Redis           | ~$5-10               |
| Backend         | ~$5-20               |
| Celery Worker   | ~$5-20               |
| Celery Beat     | ~$2-5                |
| Frontend        | ~$5-10               |
| **Total**       | **~$27-80/month**    |

Railway uses usage-based pricing. Costs scale with traffic.
