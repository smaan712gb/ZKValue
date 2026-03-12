#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# ZKValue Production Deployment Script
# ============================================================
# Usage:
#   ./scripts/deploy.sh              # Full deploy
#   ./scripts/deploy.sh --build-only # Build images only
#   ./scripts/deploy.sh --migrate    # Run DB migrations only
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/backend/.env"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Pre-flight checks ---
preflight() {
    log_info "Running pre-flight checks..."

    if ! command -v docker &>/dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! docker compose version &>/dev/null; then
        log_error "Docker Compose v2 is not installed"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        log_error "Missing $ENV_FILE — copy from backend/.env.production.example"
        exit 1
    fi

    # Validate required env vars
    local required_vars=(DATABASE_URL SECRET_KEY STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET)
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=.\+" "$ENV_FILE" 2>/dev/null; then
            log_error "Missing or empty: $var in $ENV_FILE"
            exit 1
        fi
    done

    # Check at least one LLM key
    if ! grep -q "^DEEPSEEK_API_KEY=.\+" "$ENV_FILE" 2>/dev/null && \
       ! grep -q "^OPENAI_API_KEY=.\+" "$ENV_FILE" 2>/dev/null && \
       ! grep -q "^ANTHROPIC_API_KEY=.\+" "$ENV_FILE" 2>/dev/null; then
        log_error "At least one LLM API key is required (DEEPSEEK/OPENAI/ANTHROPIC)"
        exit 1
    fi

    # Check ENVIRONMENT=production
    if ! grep -q "^ENVIRONMENT=production" "$ENV_FILE" 2>/dev/null; then
        log_warn "ENVIRONMENT is not set to 'production' in $ENV_FILE"
    fi

    # Check SSL certificates
    if [ ! -f "$PROJECT_DIR/nginx/ssl/fullchain.pem" ] || [ ! -f "$PROJECT_DIR/nginx/ssl/privkey.pem" ]; then
        log_warn "SSL certificates not found in nginx/ssl/"
        log_warn "Place fullchain.pem and privkey.pem for HTTPS"
        log_warn "For testing, generate self-signed certs:"
        log_warn "  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\"
        log_warn "    -keyout nginx/ssl/privkey.pem -out nginx/ssl/fullchain.pem \\"
        log_warn "    -subj '/CN=localhost'"
    fi

    log_info "Pre-flight checks passed"
}

# --- Build ---
build() {
    log_info "Building production images..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    log_info "Build complete"
}

# --- Migrate ---
migrate() {
    log_info "Running database migrations..."
    docker compose -f "$COMPOSE_FILE" run --rm backend \
        alembic upgrade head
    log_info "Migrations complete"
}

# --- Deploy ---
deploy() {
    log_info "Starting production services..."
    docker compose -f "$COMPOSE_FILE" up -d
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check health
    local services=("zkvalue-postgres" "zkvalue-redis" "zkvalue-backend" "zkvalue-nginx")
    for svc in "${services[@]}"; do
        if docker ps --filter "name=$svc" --filter "status=running" -q | grep -q .; then
            log_info "  ✓ $svc is running"
        else
            log_error "  ✗ $svc is NOT running"
            docker compose -f "$COMPOSE_FILE" logs "$svc" --tail=20
        fi
    done

    echo ""
    log_info "============================================"
    log_info "  ZKValue deployed successfully!"
    log_info "  HTTPS: https://$(grep FRONTEND_URL "$ENV_FILE" | cut -d= -f2- | sed 's|https://||')"
    log_info "  Health: curl -k https://localhost/health"
    log_info "============================================"
}

# --- Main ---
case "${1:-}" in
    --build-only)
        preflight
        build
        ;;
    --migrate)
        preflight
        migrate
        ;;
    *)
        preflight
        build
        migrate
        deploy
        ;;
esac
