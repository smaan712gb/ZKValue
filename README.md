# ZKValue

**Cryptographic Proof Layer for Opaque Alternative Assets**

ZKValue provides verifiable computation infrastructure for alternative asset valuation — enabling fund administrators, asset managers, and auditors to independently verify private credit portfolios and AI/IP asset valuations with cryptographic proofs, LLM-powered analysis, and optional blockchain anchoring.

---

## Why ZKValue

Alternative assets — private credit, AI intellectual property, model weights, proprietary datasets — lack transparent pricing. NAV calculations depend on opaque models, manual spreadsheets, and trust-based workflows. ZKValue replaces trust with verification:

- **Cryptographic Proofs** — Every valuation produces a SHA-256 computation proof with Merkle tree anchoring
- **AI-Powered Analysis** — Multi-provider LLM reasoning (DeepSeek, OpenAI, Anthropic) for portfolio risk assessment, anomaly detection, and executive report generation
- **Regulatory Compliance** — Automated SEC Form PF, AIFMD Annex IV reporting with IAS 38 and ASC 350 compliance checking
- **Blockchain Anchoring** — Optional on-chain settlement of proof hashes (Polygon, Ethereum, Base)

---

## Modules

### Private Credit
Upload loan tapes (CSV/JSON/Excel), run portfolio verification, covenant compliance checking, concentration risk analysis, and stress testing. Generate LP-ready executive reports with AI-driven risk narratives.

### AI-IP Valuation
Classify and value AI assets (training data, model weights, inference infrastructure, deployed applications) using cost, market, and income approaches. Automated IAS 38 intangible asset and ASC 350 goodwill compliance checks.

### Stress Testing
Predefined scenarios (interest rate shock, credit deterioration, liquidity crisis) and custom Monte Carlo simulations across portfolio parameters.

### Regulatory Reporting
Generate SEC Form PF and AIFMD Annex IV submissions with LLM-generated compliance narratives and structured data exports.

### Document AI
Parse financial documents (PDF, Excel, CSV) with structured data extraction for automated ingestion into verification workflows.

### Natural Language Queries
Ask questions about your portfolios and assets in plain English — the LLM translates to data queries and returns contextual answers.

---

## Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   Next.js   │────▶│    FastAPI Backend    │────▶│  PostgreSQL  │
│  Frontend   │     │  (Gunicorn/Uvicorn)  │     │              │
└─────────────┘     └──────────┬───────────┘     └──────────────┘
                               │
                    ┌──────────┴───────────┐
                    │                      │
              ┌─────▼─────┐        ┌───────▼──────┐
              │   Redis    │        │ Celery Worker │
              │  (Broker)  │        │  + Beat       │
              └────────────┘        └───────┬──────┘
                                            │
                              ┌─────────────┼─────────────┐
                              │             │             │
                        ┌─────▼───┐   ┌─────▼───┐  ┌─────▼──────┐
                        │ DeepSeek│   │ OpenAI  │  │ Anthropic  │
                        │   LLM   │   │   LLM   │  │    LLM     │
                        └─────────┘   └─────────┘  └────────────┘
```

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Recharts, Zustand |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2, Alembic |
| Task Queue | Celery + Redis (worker + beat scheduler) |
| Database | PostgreSQL 16 |
| LLM | DeepSeek (default), OpenAI, Anthropic — configurable per org |
| Blockchain | Web3.py — Polygon/Ethereum/Base (optional) |
| Payments | Stripe (checkout, webhooks, plan management) |
| PDF | ReportLab (certificates), LLM-generated executive reports |
| Storage | AWS S3 (production) / local filesystem (development) |
| Proxy | Nginx with TLS termination, security headers, rate limiting |
| Monitoring | Sentry (optional), structured logging (structlog) |

---

## Quick Start (Development)

```bash
# 1. Clone
git clone https://github.com/smaan712gb/ZKValue.git
cd ZKValue

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 3. Start all services
docker compose up --build

# 4. Run migrations
docker compose exec backend alembic upgrade head

# Access:
#   Frontend  → http://localhost:3000
#   API Docs  → http://localhost:8000/docs
#   API       → http://localhost:8000/api/v1
```

---

## Production Deployment

```bash
# 1. Configure production environment
cp backend/.env.production.example backend/.env
# Fill in all production values (DATABASE_URL, SECRET_KEY, API keys, etc.)
# Set ENVIRONMENT=production

# 2. Place TLS certificates
cp your-fullchain.pem nginx/ssl/fullchain.pem
cp your-privkey.pem nginx/ssl/privkey.pem

# 3. Deploy
./scripts/deploy.sh
```

The deploy script runs pre-flight checks (validates secrets, env vars, SSL certs), builds production images, runs database migrations, and starts all services behind the nginx reverse proxy.

### Production Hardening Included

- **Gunicorn** with 4 Uvicorn workers (not `--reload`)
- **Nginx** reverse proxy with TLS 1.2/1.3, HSTS, CSP, rate limiting
- **Non-root** container users
- **API docs disabled** in production (`/docs`, `/redoc`, `/openapi.json` return 404)
- **JSON structured logging** for log aggregation
- **CORS validation** — rejects localhost origins in production
- **Health checks** on all services with restart policies
- **Celery Beat** for scheduled tasks (recurring verifications, cleanup, monthly reports)
- **Resource limits** on all containers

---

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/register` | User registration with org creation |
| `POST /api/v1/auth/login` | JWT authentication |
| `POST /api/v1/credit/verify` | Submit credit portfolio for verification |
| `POST /api/v1/ai-ip/valuations` | Create AI/IP asset valuation |
| `GET /api/v1/dashboard/stats` | Dashboard KPIs and recent activity |
| `GET /api/v1/analytics/overview` | Trends, performance, asset breakdown |
| `POST /api/v1/stress-testing/run` | Run stress test scenarios |
| `POST /api/v1/regulatory/generate` | Generate Form PF / AIFMD reports |
| `POST /api/v1/blockchain/anchor` | Anchor proof hash on-chain |
| `POST /api/v1/nl-query/ask` | Natural language data queries |
| `GET /api/v1/audit/logs` | Audit trail with export |
| `GET /health` | Service health check |

Full API documentation available at `/docs` (development mode only).

---

## Environment Variables

See [backend/.env.production.example](backend/.env.production.example) for the complete list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string |
| `SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `DEEPSEEK_API_KEY` | Yes* | DeepSeek LLM API key |
| `OPENAI_API_KEY` | Yes* | OpenAI API key |
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key |
| `STRIPE_SECRET_KEY` | Prod | Stripe billing key |
| `SENTRY_DSN` | No | Error tracking |
| `BLOCKCHAIN_RPC_URL` | No | On-chain anchoring (simulation if unset) |

*At least one LLM provider key is required in production.

---

## Testing

```bash
# Run the E2E production test suite
docker compose exec backend python -m pytest tests/e2e_production_test.py -v
```

The E2E suite covers 14 test sections: authentication, credit verifications (3 portfolio types), AI-IP valuations (4 asset scenarios), stress testing, regulatory reports, analytics, blockchain anchoring, NL queries, model registry, schedules, notifications, billing, and audit logs.

---

## License

Proprietary. All rights reserved.
