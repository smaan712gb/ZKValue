"""
Production-quality seed script for verifAI / ZKValue platform.

Generates realistic synthetic data across ALL modules for demo/testing.

Usage:
    python -m scripts.seed_production_demo --email smaan@aimadds.com
    python -m scripts.seed_production_demo --email smaan@aimadds.com --database-url postgresql://...
"""

import argparse
import hashlib
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.user import User
from app.models.organization import Organization
from app.models.verification import Verification, VerificationModule, VerificationStatus
from app.models.credit_portfolio import CreditPortfolio
from app.models.ai_asset import AIAsset, AssetType, ValuationMethod
from app.models.blockchain import BlockchainAnchor, ProofAnchorMapping, ChainType, AnchorStatus
from app.models.schedule import VerificationSchedule, DriftAlert, ScheduleFrequency, AlertSeverity, AlertStatus
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.models.audit_log import AuditLog
from app.models.model_registry import ModelUsageRecord, DataLineageEvent, ModelProvider, LineageEventType


# ─── Helpers ──────────────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc)


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def random_past(max_days: int, min_days: int = 0) -> datetime:
    delta = timedelta(
        days=random.randint(min_days, max_days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return NOW - delta


def fake_tx_hash() -> str:
    return "0x" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:64]


def fake_merkle_root() -> str:
    return "0x" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:64]


def fake_contract_address() -> str:
    return "0x" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:40]


def compute_portfolio_metrics(loans):
    total_principal = sum(l["principal"] for l in loans)
    total_balance = sum(l["outstanding_balance"] for l in loans)
    weighted_rate = sum(l["principal"] * l["interest_rate"] for l in loans) / total_principal
    avg_ltv = sum(l.get("ltv_ratio", 0.7) for l in loans) / len(loans)
    return total_principal, total_balance, weighted_rate, avg_ltv


# ═══════════════════════════════════════════════════════════════════════════════
# DATA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

CREDIT_PORTFOLIOS = [
    {
        "portfolio_name": "Meridian Direct Lending Fund III",
        "fund_name": "Meridian Capital Partners",
        "target_nav": 128_500_000,
        "loans": [
            {"loan_id": "MDL-2024-001", "borrower_id": "BRW-7891", "principal": 15000000, "interest_rate": 9.25, "term_months": 60, "origination_date": "2024-03-15", "maturity_date": "2029-03-15", "collateral_value": 22500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 14250000, "ltv_ratio": 0.63, "dscr": 1.85},
            {"loan_id": "MDL-2024-002", "borrower_id": "BRW-3456", "principal": 8500000, "interest_rate": 10.50, "term_months": 48, "origination_date": "2024-05-20", "maturity_date": "2028-05-20", "collateral_value": 12750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 8075000, "ltv_ratio": 0.63, "dscr": 2.10},
            {"loan_id": "MDL-2024-003", "borrower_id": "BRW-5672", "principal": 22000000, "interest_rate": 8.75, "term_months": 72, "origination_date": "2024-01-10", "maturity_date": "2030-01-10", "collateral_value": 30800000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 21340000, "ltv_ratio": 0.69, "dscr": 1.65},
            {"loan_id": "MDL-2024-004", "borrower_id": "BRW-8901", "principal": 5500000, "interest_rate": 11.00, "term_months": 36, "origination_date": "2024-07-01", "maturity_date": "2027-07-01", "collateral_value": 7150000, "collateral_type": "Second Lien", "payment_status": "current", "outstanding_balance": 5280000, "ltv_ratio": 0.74, "dscr": 1.42},
            {"loan_id": "MDL-2024-005", "borrower_id": "BRW-2345", "principal": 12000000, "interest_rate": 9.75, "term_months": 60, "origination_date": "2024-04-15", "maturity_date": "2029-04-15", "collateral_value": 18000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 11400000, "ltv_ratio": 0.63, "dscr": 1.92},
            {"loan_id": "MDL-2024-006", "borrower_id": "BRW-6789", "principal": 18500000, "interest_rate": 8.50, "term_months": 84, "origination_date": "2024-02-28", "maturity_date": "2031-02-28", "collateral_value": 27750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 17945000, "ltv_ratio": 0.65, "dscr": 1.78},
            {"loan_id": "MDL-2024-007", "borrower_id": "BRW-1234", "principal": 7200000, "interest_rate": 10.25, "term_months": 48, "origination_date": "2024-06-10", "maturity_date": "2028-06-10", "collateral_value": 9360000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 6912000, "ltv_ratio": 0.74, "dscr": 1.35},
            {"loan_id": "MDL-2024-008", "borrower_id": "BRW-4567", "principal": 25000000, "interest_rate": 8.25, "term_months": 60, "origination_date": "2024-08-01", "maturity_date": "2029-08-01", "collateral_value": 37500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 24500000, "ltv_ratio": 0.65, "dscr": 2.25},
            {"loan_id": "MDL-2024-009", "borrower_id": "BRW-9012", "principal": 3800000, "interest_rate": 12.00, "term_months": 36, "origination_date": "2024-09-15", "maturity_date": "2027-09-15", "collateral_value": 4940000, "collateral_type": "Unitranche", "payment_status": "current", "outstanding_balance": 3724000, "ltv_ratio": 0.75, "dscr": 1.55},
            {"loan_id": "MDL-2024-010", "borrower_id": "BRW-3451", "principal": 10000000, "interest_rate": 9.50, "term_months": 60, "origination_date": "2024-10-01", "maturity_date": "2029-10-01", "collateral_value": 14000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 9800000, "ltv_ratio": 0.70, "dscr": 1.88},
            {"loan_id": "MDL-2024-011", "borrower_id": "BRW-7823", "principal": 6700000, "interest_rate": 10.75, "term_months": 48, "origination_date": "2024-11-15", "maturity_date": "2028-11-15", "collateral_value": 8710000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 6633000, "ltv_ratio": 0.76, "dscr": 1.62},
            {"loan_id": "MDL-2024-012", "borrower_id": "BRW-5601", "principal": 14000000, "interest_rate": 9.00, "term_months": 72, "origination_date": "2024-03-01", "maturity_date": "2030-03-01", "collateral_value": 21000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 13580000, "ltv_ratio": 0.65, "dscr": 1.95},
        ],
        "covenants": {"max_ltv": 0.80, "min_dscr": 1.20, "max_single_borrower_concentration": 0.20, "min_portfolio_yield": 8.0},
    },
    {
        "portfolio_name": "Atlas Special Situations Fund II",
        "fund_name": "Atlas Credit Management",
        "target_nav": 18_800_000,
        "loans": [
            {"loan_id": "ASS-2024-001", "borrower_id": "BRW-D101", "principal": 4200000, "interest_rate": 14.50, "term_months": 24, "origination_date": "2024-06-01", "maturity_date": "2026-06-01", "collateral_value": 3780000, "collateral_type": "Second Lien", "payment_status": "60_days_late", "outstanding_balance": 4116000, "ltv_ratio": 1.09, "dscr": 0.85},
            {"loan_id": "ASS-2024-002", "borrower_id": "BRW-D102", "principal": 9800000, "interest_rate": 13.00, "term_months": 36, "origination_date": "2024-04-15", "maturity_date": "2027-04-15", "collateral_value": 11760000, "collateral_type": "Senior Secured - First Lien", "payment_status": "30_days_late", "outstanding_balance": 9506000, "ltv_ratio": 0.81, "dscr": 1.05},
            {"loan_id": "ASS-2024-003", "borrower_id": "BRW-D103", "principal": 2100000, "interest_rate": 16.00, "term_months": 18, "origination_date": "2024-08-01", "maturity_date": "2026-02-01", "collateral_value": 1890000, "collateral_type": "Mezzanine", "payment_status": "default", "outstanding_balance": 2100000, "ltv_ratio": 1.11, "dscr": 0.60},
            {"loan_id": "ASS-2024-004", "borrower_id": "BRW-D104", "principal": 7500000, "interest_rate": 12.75, "term_months": 30, "origination_date": "2024-05-20", "maturity_date": "2026-11-20", "collateral_value": 9375000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 7125000, "ltv_ratio": 0.76, "dscr": 1.30},
            {"loan_id": "ASS-2024-005", "borrower_id": "BRW-D105", "principal": 3300000, "interest_rate": 15.25, "term_months": 24, "origination_date": "2024-09-01", "maturity_date": "2026-09-01", "collateral_value": 2970000, "collateral_type": "Unitranche", "payment_status": "90_days_late", "outstanding_balance": 3300000, "ltv_ratio": 1.11, "dscr": 0.45},
        ],
        "covenants": {"max_ltv": 1.20, "min_dscr": 0.80, "max_single_borrower_concentration": 0.35, "min_portfolio_yield": 12.0},
    },
    {
        "portfolio_name": "Cascade Mid-Market Lending Series A",
        "fund_name": "Cascade Capital Advisors",
        "target_nav": 242_500_000,
        "loans": [
            {"loan_id": "CML-2025-001", "borrower_id": "BRW-M201", "principal": 35000000, "interest_rate": 7.75, "term_months": 84, "origination_date": "2025-01-15", "maturity_date": "2032-01-15", "collateral_value": 52500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 34650000, "ltv_ratio": 0.66, "dscr": 2.40},
            {"loan_id": "CML-2025-002", "borrower_id": "BRW-M202", "principal": 20000000, "interest_rate": 8.25, "term_months": 60, "origination_date": "2025-02-01", "maturity_date": "2030-02-01", "collateral_value": 28000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 19800000, "ltv_ratio": 0.71, "dscr": 2.15},
            {"loan_id": "CML-2025-003", "borrower_id": "BRW-M203", "principal": 28000000, "interest_rate": 8.00, "term_months": 72, "origination_date": "2025-01-20", "maturity_date": "2031-01-20", "collateral_value": 39200000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 27720000, "ltv_ratio": 0.71, "dscr": 2.05},
            {"loan_id": "CML-2025-004", "borrower_id": "BRW-M204", "principal": 15000000, "interest_rate": 8.50, "term_months": 60, "origination_date": "2025-02-15", "maturity_date": "2030-02-15", "collateral_value": 21750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 14850000, "ltv_ratio": 0.68, "dscr": 2.30},
            {"loan_id": "CML-2025-005", "borrower_id": "BRW-M205", "principal": 42000000, "interest_rate": 7.50, "term_months": 84, "origination_date": "2025-01-05", "maturity_date": "2032-01-05", "collateral_value": 63000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 41580000, "ltv_ratio": 0.66, "dscr": 2.55},
            {"loan_id": "CML-2025-006", "borrower_id": "BRW-M206", "principal": 18500000, "interest_rate": 8.75, "term_months": 60, "origination_date": "2025-03-01", "maturity_date": "2030-03-01", "collateral_value": 25900000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 18315000, "ltv_ratio": 0.71, "dscr": 2.20},
            {"loan_id": "CML-2025-007", "borrower_id": "BRW-M207", "principal": 12000000, "interest_rate": 9.00, "term_months": 48, "origination_date": "2025-02-20", "maturity_date": "2029-02-20", "collateral_value": 16800000, "collateral_type": "Senior Secured - First Lien", "payment_status": "30_days_late", "outstanding_balance": 11880000, "ltv_ratio": 0.71, "dscr": 1.15},
            {"loan_id": "CML-2025-008", "borrower_id": "BRW-M208", "principal": 50000000, "interest_rate": 7.25, "term_months": 96, "origination_date": "2025-01-10", "maturity_date": "2033-01-10", "collateral_value": 75000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 49500000, "ltv_ratio": 0.66, "dscr": 2.70},
        ],
        "covenants": {"max_ltv": 0.75, "min_dscr": 1.50, "max_single_borrower_concentration": 0.25, "min_portfolio_yield": 7.5},
    },
    {
        "portfolio_name": "Pinnacle Senior Secured Fund I",
        "fund_name": "Pinnacle Asset Management",
        "target_nav": 567_200_000,
        "loans": [
            {"loan_id": "PSS-2024-001", "borrower_id": "BRW-P301", "principal": 55000000, "interest_rate": 6.75, "term_months": 84, "origination_date": "2024-02-01", "maturity_date": "2031-02-01", "collateral_value": 82500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 53900000, "ltv_ratio": 0.65, "dscr": 2.80},
            {"loan_id": "PSS-2024-002", "borrower_id": "BRW-P302", "principal": 40000000, "interest_rate": 7.00, "term_months": 72, "origination_date": "2024-03-15", "maturity_date": "2030-03-15", "collateral_value": 60000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 39200000, "ltv_ratio": 0.65, "dscr": 2.65},
            {"loan_id": "PSS-2024-003", "borrower_id": "BRW-P303", "principal": 72000000, "interest_rate": 6.50, "term_months": 96, "origination_date": "2024-01-20", "maturity_date": "2032-01-20", "collateral_value": 108000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 70560000, "ltv_ratio": 0.65, "dscr": 3.10},
            {"loan_id": "PSS-2024-004", "borrower_id": "BRW-P304", "principal": 28000000, "interest_rate": 7.25, "term_months": 60, "origination_date": "2024-04-10", "maturity_date": "2029-04-10", "collateral_value": 42000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 27440000, "ltv_ratio": 0.65, "dscr": 2.55},
            {"loan_id": "PSS-2024-005", "borrower_id": "BRW-P305", "principal": 45000000, "interest_rate": 6.90, "term_months": 84, "origination_date": "2024-05-01", "maturity_date": "2031-05-01", "collateral_value": 67500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 44100000, "ltv_ratio": 0.65, "dscr": 2.75},
            {"loan_id": "PSS-2024-006", "borrower_id": "BRW-P306", "principal": 33000000, "interest_rate": 7.10, "term_months": 72, "origination_date": "2024-06-15", "maturity_date": "2030-06-15", "collateral_value": 49500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 32340000, "ltv_ratio": 0.65, "dscr": 2.60},
            {"loan_id": "PSS-2024-007", "borrower_id": "BRW-P307", "principal": 60000000, "interest_rate": 6.60, "term_months": 96, "origination_date": "2024-02-15", "maturity_date": "2032-02-15", "collateral_value": 90000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 58800000, "ltv_ratio": 0.65, "dscr": 2.90},
            {"loan_id": "PSS-2024-008", "borrower_id": "BRW-P308", "principal": 22000000, "interest_rate": 7.40, "term_months": 60, "origination_date": "2024-07-01", "maturity_date": "2029-07-01", "collateral_value": 33000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 21560000, "ltv_ratio": 0.65, "dscr": 2.45},
            {"loan_id": "PSS-2024-009", "borrower_id": "BRW-P309", "principal": 50000000, "interest_rate": 6.80, "term_months": 84, "origination_date": "2024-03-01", "maturity_date": "2031-03-01", "collateral_value": 75000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 49000000, "ltv_ratio": 0.65, "dscr": 2.70},
            {"loan_id": "PSS-2024-010", "borrower_id": "BRW-P310", "principal": 38000000, "interest_rate": 7.15, "term_months": 72, "origination_date": "2024-08-15", "maturity_date": "2030-08-15", "collateral_value": 57000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 37240000, "ltv_ratio": 0.65, "dscr": 2.50},
            {"loan_id": "PSS-2024-011", "borrower_id": "BRW-P311", "principal": 65000000, "interest_rate": 6.55, "term_months": 96, "origination_date": "2024-04-01", "maturity_date": "2032-04-01", "collateral_value": 97500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 63700000, "ltv_ratio": 0.65, "dscr": 3.00},
            {"loan_id": "PSS-2024-012", "borrower_id": "BRW-P312", "principal": 18000000, "interest_rate": 7.50, "term_months": 60, "origination_date": "2024-09-01", "maturity_date": "2029-09-01", "collateral_value": 27000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 17640000, "ltv_ratio": 0.65, "dscr": 2.40},
            {"loan_id": "PSS-2024-013", "borrower_id": "BRW-P313", "principal": 48000000, "interest_rate": 6.85, "term_months": 84, "origination_date": "2024-05-15", "maturity_date": "2031-05-15", "collateral_value": 72000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 47040000, "ltv_ratio": 0.65, "dscr": 2.85},
            {"loan_id": "PSS-2024-014", "borrower_id": "BRW-P314", "principal": 30000000, "interest_rate": 7.20, "term_months": 72, "origination_date": "2024-06-01", "maturity_date": "2030-06-01", "collateral_value": 45000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 29400000, "ltv_ratio": 0.65, "dscr": 2.55},
            {"loan_id": "PSS-2024-015", "borrower_id": "BRW-P315", "principal": 25000000, "interest_rate": 7.30, "term_months": 60, "origination_date": "2024-10-01", "maturity_date": "2029-10-01", "collateral_value": 37500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 24500000, "ltv_ratio": 0.65, "dscr": 2.50},
        ],
        "covenants": {"max_ltv": 0.70, "min_dscr": 2.00, "max_single_borrower_concentration": 0.15, "min_portfolio_yield": 6.5},
    },
    {
        "portfolio_name": "Horizon Venture Debt Fund IV",
        "fund_name": "Horizon Growth Capital",
        "target_nav": 45_300_000,
        "loans": [
            {"loan_id": "HVD-2025-001", "borrower_id": "BRW-V401", "principal": 8000000, "interest_rate": 13.50, "term_months": 36, "origination_date": "2025-01-10", "maturity_date": "2028-01-10", "collateral_value": 10400000, "collateral_type": "Senior Secured - First Lien + Warrants", "payment_status": "current", "outstanding_balance": 7840000, "ltv_ratio": 0.75, "dscr": 1.35},
            {"loan_id": "HVD-2025-002", "borrower_id": "BRW-V402", "principal": 5500000, "interest_rate": 14.00, "term_months": 30, "origination_date": "2025-02-01", "maturity_date": "2027-08-01", "collateral_value": 6600000, "collateral_type": "Senior Secured + IP Pledge", "payment_status": "30_days_late", "outstanding_balance": 5390000, "ltv_ratio": 0.82, "dscr": 1.08},
            {"loan_id": "HVD-2025-003", "borrower_id": "BRW-V403", "principal": 12000000, "interest_rate": 12.75, "term_months": 42, "origination_date": "2025-01-20", "maturity_date": "2028-07-20", "collateral_value": 15600000, "collateral_type": "Senior Secured - First Lien + Warrants", "payment_status": "current", "outstanding_balance": 11760000, "ltv_ratio": 0.75, "dscr": 1.45},
            {"loan_id": "HVD-2025-004", "borrower_id": "BRW-V404", "principal": 6500000, "interest_rate": 13.25, "term_months": 36, "origination_date": "2025-03-01", "maturity_date": "2028-03-01", "collateral_value": 7800000, "collateral_type": "Senior Secured + Revenue Share", "payment_status": "current", "outstanding_balance": 6370000, "ltv_ratio": 0.82, "dscr": 1.28},
            {"loan_id": "HVD-2025-005", "borrower_id": "BRW-V405", "principal": 9500000, "interest_rate": 14.50, "term_months": 30, "origination_date": "2025-02-15", "maturity_date": "2027-08-15", "collateral_value": 11400000, "collateral_type": "Senior Secured - First Lien + Warrants", "payment_status": "current", "outstanding_balance": 9310000, "ltv_ratio": 0.82, "dscr": 1.40},
            {"loan_id": "HVD-2025-006", "borrower_id": "BRW-V406", "principal": 4200000, "interest_rate": 15.00, "term_months": 24, "origination_date": "2025-01-05", "maturity_date": "2027-01-05", "collateral_value": 4620000, "collateral_type": "Unitranche + Warrants", "payment_status": "60_days_late", "outstanding_balance": 4158000, "ltv_ratio": 0.90, "dscr": 0.92},
        ],
        "covenants": {"max_ltv": 0.90, "min_dscr": 1.00, "max_single_borrower_concentration": 0.30, "min_portfolio_yield": 12.0},
    },
]

AI_IP_ASSETS = [
    {
        "asset_name": "MedVision-3B Diagnostic Model",
        "asset_type": "model_weights",
        "valuation_method": "cost_approach",
        "estimated_value": 11_760_000,
        "description": "3-billion parameter vision transformer trained on 2.1M de-identified radiology images (CT, MRI, X-ray) for automated diagnostic screening. Achieves 94.2% accuracy on CheXpert benchmark, FDA 510(k) pre-submission filed. Licensed to 12 hospital networks.",
        "training_cost": 4200000,
        "training_compute_hours": 28000,
        "model_parameters": 3000000000,
        "dataset_size_gb": 850,
        "dataset_uniqueness_score": 0.92,
        "monthly_revenue": 380000,
        "monthly_active_users": 2400,
        "benchmark_scores": {"chexpert_auc": 0.942, "mimic_sensitivity": 0.918, "rsna_specificity": 0.961},
        "gpu_type": "NVIDIA H100",
        "gpu_count": 64,
        "cloud_provider": "AWS",
    },
    {
        "asset_name": "FinSentiment-XL NLP Engine",
        "asset_type": "deployed_app",
        "valuation_method": "income_approach",
        "estimated_value": 10_680_000,
        "description": "Real-time financial sentiment analysis engine processing 50K+ earnings calls, SEC filings, and news articles daily. Powers trading signals for 8 hedge funds. Fine-tuned from Llama-3 70B on proprietary dataset of 15M annotated financial documents.",
        "training_cost": 1800000,
        "training_compute_hours": 12000,
        "model_parameters": 70000000000,
        "dataset_size_gb": 320,
        "dataset_uniqueness_score": 0.88,
        "monthly_revenue": 890000,
        "monthly_active_users": 340,
        "inference_cost_per_query": 0.012,
        "benchmark_scores": {"financial_phrasebank": 0.956, "semeval_fin": 0.923, "custom_earnings": 0.941},
        "gpu_type": "NVIDIA A100",
        "gpu_count": 32,
        "cloud_provider": "GCP",
    },
    {
        "asset_name": "RetailGraph Recommendation Dataset",
        "asset_type": "training_data",
        "valuation_method": "market_approach",
        "estimated_value": 4_500_000,
        "description": "Proprietary graph-structured dataset of 480M anonymized purchase interactions across 12M users and 2.8M SKUs from 3 major US retailers (2019-2025). Includes temporal purchasing patterns, cross-category affinity scores, and seasonal decomposition.",
        "training_cost": 750000,
        "dataset_size_gb": 2400,
        "dataset_uniqueness_score": 0.95,
        "monthly_revenue": 125000,
        "monthly_active_users": 45,
        "benchmark_scores": {"ndcg_at_10": 0.412, "hit_rate_at_20": 0.678, "coverage": 0.891},
    },
    {
        "asset_name": "EdgeServe Inference Platform",
        "asset_type": "inference_infra",
        "valuation_method": "income_approach",
        "estimated_value": 6_240_000,
        "description": "On-premise GPU inference cluster (96x NVIDIA L40S) with custom CUDA kernels, TensorRT optimization pipeline, and auto-scaling orchestration. Sub-10ms P99 latency for models up to 13B parameters. Deployed across 3 data centers.",
        "training_cost": 0,
        "training_compute_hours": 0,
        "monthly_revenue": 520000,
        "monthly_active_users": 180,
        "inference_cost_per_query": 0.003,
        "gpu_type": "NVIDIA L40S",
        "gpu_count": 96,
        "cloud_provider": "On-Premise",
    },
    {
        "asset_name": "AutoDrive Perception Model v2",
        "asset_type": "model_weights",
        "valuation_method": "cost_approach",
        "estimated_value": 28_400_000,
        "description": "Multi-modal perception model for autonomous driving combining LiDAR, camera, and radar inputs. 4.8B parameters trained on 12M annotated driving scenes from 6 cities. ASIL-D safety certified. Licensed to 3 OEMs for L3+ highway pilot features.",
        "training_cost": 9500000,
        "training_compute_hours": 85000,
        "model_parameters": 4800000000,
        "dataset_size_gb": 4200,
        "dataset_uniqueness_score": 0.97,
        "monthly_revenue": 1250000,
        "monthly_active_users": 85,
        "benchmark_scores": {"nuscenes_map": 0.724, "waymo_3d_det": 0.681, "kitti_seg": 0.945},
        "gpu_type": "NVIDIA H100",
        "gpu_count": 256,
        "cloud_provider": "AWS",
    },
    {
        "asset_name": "SpeechGen Real-Time TTS",
        "asset_type": "deployed_app",
        "valuation_method": "income_approach",
        "estimated_value": 15_200_000,
        "description": "Low-latency text-to-speech system supporting 42 languages with emotion-aware prosody control. Sub-200ms first-byte latency. Serving 8M daily API calls for customer service automation, audiobook narration, and accessibility tools.",
        "training_cost": 3200000,
        "training_compute_hours": 45000,
        "model_parameters": 1200000000,
        "dataset_size_gb": 680,
        "dataset_uniqueness_score": 0.85,
        "monthly_revenue": 720000,
        "monthly_active_users": 12500,
        "inference_cost_per_query": 0.002,
        "benchmark_scores": {"mos_naturalness": 4.32, "mos_intelligibility": 4.61, "rtf": 0.08},
        "gpu_type": "NVIDIA A100",
        "gpu_count": 48,
        "cloud_provider": "Azure",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def seed_credit_portfolios(db: Session, org_id, user_id) -> list:
    """Create 5 credit portfolios with linked verifications. Returns verification IDs."""
    print("\n[1/9] Seeding credit portfolios...")
    verification_ids = []

    for portfolio_def in CREDIT_PORTFOLIOS:
        # Check idempotency
        existing = db.execute(
            select(CreditPortfolio).where(
                CreditPortfolio.organization_id == org_id,
                CreditPortfolio.portfolio_name == portfolio_def["portfolio_name"],
                CreditPortfolio.is_deleted == False,
            )
        ).scalar_one_or_none()
        if existing:
            print(f"  [skip] {portfolio_def['portfolio_name']} already exists")
            verification_ids.append(existing.verification_id)
            continue

        created = random_past(max_days=90, min_days=1)
        completed = created + timedelta(seconds=random.randint(30, 120))

        loans = portfolio_def["loans"]
        total_principal, total_balance, weighted_rate, avg_ltv = compute_portfolio_metrics(loans)
        nav = portfolio_def["target_nav"]

        # Covenant compliance
        covenants = portfolio_def.get("covenants", {})
        covenant_status = {}
        if covenants:
            covenant_status["max_ltv"] = {
                "limit": covenants.get("max_ltv"),
                "actual": round(avg_ltv, 3),
                "compliant": avg_ltv <= covenants.get("max_ltv", 1.0),
            }
            min_dscr_actual = min(l.get("dscr", 999) for l in loans)
            covenant_status["min_dscr"] = {
                "limit": covenants.get("min_dscr"),
                "actual": round(min_dscr_actual, 2),
                "compliant": min_dscr_actual >= covenants.get("min_dscr", 0),
            }
            max_conc = max(l["principal"] for l in loans) / total_principal
            covenant_status["max_concentration"] = {
                "limit": covenants.get("max_single_borrower_concentration"),
                "actual": round(max_conc, 3),
                "compliant": max_conc <= covenants.get("max_single_borrower_concentration", 1.0),
            }

        input_data = {
            "portfolio_name": portfolio_def["portfolio_name"],
            "fund_name": portfolio_def["fund_name"],
            "loans": loans,
            "covenants": covenants,
        }

        result_data = {
            "portfolio_summary": {
                "total_principal": total_principal,
                "total_outstanding": total_balance,
                "weighted_avg_rate": round(weighted_rate, 2),
                "avg_ltv_ratio": round(avg_ltv, 3),
                "nav_value": nav,
                "loan_count": len(loans),
                "current_loans": sum(1 for l in loans if l["payment_status"] == "current"),
                "delinquent_loans": sum(1 for l in loans if l["payment_status"] != "current"),
            },
            "covenant_compliance": covenant_status,
            "risk_metrics": {
                "concentration_risk": round(max(l["principal"] for l in loans) / total_principal, 3),
                "weighted_avg_dscr": round(sum(l.get("dscr", 1.5) * l["principal"] for l in loans) / total_principal, 2),
                "collateral_coverage": round(sum(l["collateral_value"] for l in loans) / total_balance, 2),
            },
            "executive_summary": (
                f"Portfolio '{portfolio_def['portfolio_name']}' contains {len(loans)} loans with "
                f"total principal of ${total_principal:,.0f}. NAV calculated at ${nav:,.0f}."
            ),
        }

        proof_hash = sha256(json.dumps(input_data, sort_keys=True) + json.dumps(result_data, sort_keys=True))

        v_id = uuid.uuid4()
        verification = Verification(
            id=v_id,
            organization_id=org_id,
            created_by=user_id,
            module=VerificationModule.private_credit,
            status=VerificationStatus.completed,
            input_data=input_data,
            result_data=result_data,
            proof_hash=proof_hash,
            extra_metadata={"portfolio_name": portfolio_def["portfolio_name"], "fund_name": portfolio_def["fund_name"]},
            created_at=created,
            updated_at=completed,
            completed_at=completed,
        )
        db.add(verification)
        db.flush()

        cp = CreditPortfolio(
            id=uuid.uuid4(),
            organization_id=org_id,
            verification_id=v_id,
            portfolio_name=portfolio_def["portfolio_name"],
            fund_name=portfolio_def["fund_name"],
            loan_count=len(loans),
            total_principal=Decimal(str(total_principal)),
            weighted_avg_rate=Decimal(str(round(weighted_rate, 6))),
            avg_ltv_ratio=Decimal(str(round(avg_ltv, 6))),
            nav_value=Decimal(str(nav)),
            covenant_compliance_status=covenant_status,
            created_at=created,
            updated_at=created,
        )
        db.add(cp)
        verification_ids.append(v_id)
        print(f"  [ok] {portfolio_def['portfolio_name']} ({len(loans)} loans, NAV ${nav:,.0f})")

    db.flush()
    return verification_ids


def seed_ai_ip_assets(db: Session, org_id, user_id) -> list:
    """Create 6 AI-IP assets with linked verifications. Returns verification IDs."""
    print("\n[2/9] Seeding AI-IP assets...")
    verification_ids = []

    for asset_def in AI_IP_ASSETS:
        existing = db.execute(
            select(AIAsset).where(
                AIAsset.organization_id == org_id,
                AIAsset.asset_name == asset_def["asset_name"],
                AIAsset.is_deleted == False,
            )
        ).scalar_one_or_none()
        if existing:
            print(f"  [skip] {asset_def['asset_name']} already exists")
            verification_ids.append(existing.verification_id)
            continue

        created = random_past(max_days=90, min_days=1)
        completed = created + timedelta(seconds=random.randint(30, 120))

        asset_type_val = asset_def["asset_type"]
        valuation_method_val = asset_def["valuation_method"]
        estimated_value = asset_def["estimated_value"]
        training_cost = asset_def.get("training_cost", 0)
        monthly_rev = asset_def.get("monthly_revenue", 0)
        annual_rev = monthly_rev * 12
        confidence = round(random.uniform(0.78, 0.95), 4)

        input_data = {k: v for k, v in asset_def.items() if k not in ("valuation_method", "estimated_value")}

        result_data = {
            "valuation_summary": {
                "estimated_value": estimated_value,
                "valuation_method": valuation_method_val,
                "confidence_score": confidence,
                "value_range_low": round(estimated_value * 0.85, 2),
                "value_range_high": round(estimated_value * 1.20, 2),
            },
            "compliance": {
                "ias38_compliant": asset_type_val in ("model_weights", "deployed_app"),
                "asc350_compliant": True,
                "ias38_criteria": {
                    "identifiable": True,
                    "control": True,
                    "future_economic_benefits": monthly_rev > 0,
                    "cost_measurable": training_cost > 0,
                },
            },
            "key_drivers": [
                f"{'Strong' if monthly_rev > 200000 else 'Growing'} revenue stream at ${monthly_rev:,.0f}/month",
                f"Training investment of ${training_cost:,.0f} with {'high' if asset_def.get('dataset_uniqueness_score', 0) > 0.9 else 'moderate'} data moat",
                f"{asset_def.get('monthly_active_users', 0):,} active users across licensed deployments",
            ],
            "executive_summary": (
                f"'{asset_def['asset_name']}' valued at ${estimated_value:,.0f} via "
                f"{valuation_method_val.replace('_', ' ')} with confidence {confidence:.0%}."
            ),
        }

        proof_hash = sha256(json.dumps(input_data, sort_keys=True) + json.dumps(result_data, sort_keys=True))

        v_id = uuid.uuid4()
        verification = Verification(
            id=v_id,
            organization_id=org_id,
            created_by=user_id,
            module=VerificationModule.ai_ip_valuation,
            status=VerificationStatus.completed,
            input_data=input_data,
            result_data=result_data,
            proof_hash=proof_hash,
            extra_metadata={"asset_name": asset_def["asset_name"], "asset_type": asset_type_val},
            created_at=created,
            updated_at=completed,
            completed_at=completed,
        )
        db.add(verification)
        db.flush()

        ai_asset = AIAsset(
            id=uuid.uuid4(),
            organization_id=org_id,
            verification_id=v_id,
            asset_type=AssetType(asset_type_val),
            asset_name=asset_def["asset_name"],
            description=asset_def["description"],
            valuation_method=ValuationMethod(valuation_method_val),
            estimated_value=Decimal(str(estimated_value)),
            confidence_score=Decimal(str(confidence)),
            valuation_inputs=input_data,
            valuation_breakdown=result_data["valuation_summary"],
            ias38_compliant=result_data["compliance"]["ias38_compliant"],
            asc350_compliant=True,
            created_at=created,
            updated_at=created,
        )
        db.add(ai_asset)
        verification_ids.append(v_id)
        print(f"  [ok] {asset_def['asset_name']} (${estimated_value:,.0f}, {valuation_method_val})")

    db.flush()
    return verification_ids


def seed_trend_verifications(db: Session, org_id, user_id) -> list:
    """Create 18 additional verifications spread over 6 months for trend data."""
    print("\n[3/9] Seeding trend verifications...")

    # Check if we already have enough verifications beyond the main ones
    count = db.execute(
        select(Verification).where(
            Verification.organization_id == org_id,
            Verification.is_deleted == False,
        )
    ).scalars().all()
    if len(count) >= 25:
        print(f"  [skip] Already have {len(count)} verifications, skipping trends")
        return [v.id for v in count]

    verification_ids = []
    trend_entries = [
        # (module, status, days_ago, name)
        (VerificationModule.private_credit, VerificationStatus.completed, 170, "Q2 2025 NAV Review - Meridian Fund"),
        (VerificationModule.private_credit, VerificationStatus.completed, 155, "Atlas SSF Restructuring Analysis"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 140, "MedVision Quarterly Revaluation"),
        (VerificationModule.private_credit, VerificationStatus.failed, 130, "Cascade Portfolio Upload - Format Error"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 120, "FinSentiment License Renewal Value"),
        (VerificationModule.private_credit, VerificationStatus.completed, 110, "Pinnacle Fund Monthly Check"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 95, "AutoDrive v2 Post-Training Valuation"),
        (VerificationModule.private_credit, VerificationStatus.completed, 80, "Horizon Venture Debt Re-evaluation"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.failed, 72, "SpeechGen TTS - API Timeout"),
        (VerificationModule.private_credit, VerificationStatus.completed, 60, "Meridian Fund Q3 Covenant Check"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 50, "EdgeServe Platform Capacity Upgrade"),
        (VerificationModule.private_credit, VerificationStatus.completed, 40, "Atlas SSF Recovery Assessment"),
        (VerificationModule.private_credit, VerificationStatus.pending, 5, "Cascade Q1 2026 Pre-Review"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 30, "RetailGraph Dataset Expansion Value"),
        (VerificationModule.private_credit, VerificationStatus.completed, 22, "Pinnacle Fund Quarterly Audit"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.completed, 15, "MedVision FDA Milestone Update"),
        (VerificationModule.ai_ip_valuation, VerificationStatus.pending, 2, "AutoDrive v2.1 Training Completion"),
        (VerificationModule.private_credit, VerificationStatus.completed, 8, "Horizon VD Monthly Monitoring"),
    ]

    for module, status, days_ago, name in trend_entries:
        created = random_past(max_days=days_ago, min_days=max(0, days_ago - 5))

        if module == VerificationModule.private_credit:
            input_data = {
                "portfolio_name": name,
                "review_type": random.choice(["quarterly", "monthly", "ad_hoc"]),
                "loan_count": random.randint(3, 20),
            }
            result_data = {
                "nav_value": random.randint(10_000_000, 600_000_000),
                "covenant_compliance": random.choice(["all_met", "minor_breach", "major_breach"]),
                "risk_score": round(random.uniform(0.1, 0.9), 2),
            } if status == VerificationStatus.completed else None
        else:
            input_data = {
                "asset_name": name,
                "valuation_method": random.choice(["cost_approach", "income_approach", "market_approach"]),
            }
            result_data = {
                "estimated_value": random.randint(1_000_000, 30_000_000),
                "confidence_score": round(random.uniform(0.75, 0.96), 2),
                "compliance_status": "compliant",
            } if status == VerificationStatus.completed else None

        proof_hash = sha256(json.dumps(input_data, sort_keys=True) + str(uuid.uuid4())) if status == VerificationStatus.completed else None
        completed_at = created + timedelta(seconds=random.randint(30, 180)) if status == VerificationStatus.completed else None
        error_msg = "Connection timeout while processing loan tape data" if status == VerificationStatus.failed else None

        v_id = uuid.uuid4()
        v = Verification(
            id=v_id,
            organization_id=org_id,
            created_by=user_id,
            module=module,
            status=status,
            input_data=input_data,
            result_data=result_data,
            proof_hash=proof_hash,
            extra_metadata={"name": name, "source": "scheduled" if "Monthly" in name or "Quarterly" in name else "manual"},
            error_message=error_msg,
            created_at=created,
            updated_at=completed_at or created,
            completed_at=completed_at,
        )
        db.add(v)
        verification_ids.append(v_id)
        status_icon = "ok" if status == VerificationStatus.completed else ("!!" if status == VerificationStatus.failed else "..")
        print(f"  [{status_icon}] {name} ({status.value}, {days_ago}d ago)")

    db.flush()
    return verification_ids


def seed_blockchain_anchors(db: Session, org_id, all_verification_ids: list) -> None:
    """Create 3 blockchain anchors with proof mappings."""
    print("\n[4/9] Seeding blockchain anchors...")

    existing = db.execute(select(BlockchainAnchor)).scalars().all()
    if len(existing) >= 3:
        print(f"  [skip] Already have {len(existing)} anchors")
        return

    # Only use completed verification IDs (the ones with proof hashes)
    completed_v_ids = all_verification_ids[:11]  # portfolios + assets

    chains = [
        (ChainType.polygon, "Polygon PoS", 58_214_832, 25, 12),
        (ChainType.ethereum, "Ethereum Mainnet", 19_845_221, 45_000, 35),
        (ChainType.base, "Base L2", 12_384_109, 8, 3),
    ]

    v_idx = 0
    for chain_type, chain_label, block_num, gas_price, gas_used_k in chains:
        proof_count = random.randint(3, 5)
        proof_hashes_for_anchor = []

        anchor_id = uuid.uuid4()
        anchor_date = random_past(max_days=30, min_days=2)

        # Generate proof hashes for this anchor
        for i in range(proof_count):
            proof_hashes_for_anchor.append(sha256(f"anchor-{anchor_id}-proof-{i}"))

        anchor = BlockchainAnchor(
            id=anchor_id,
            chain=chain_type,
            merkle_root=fake_merkle_root(),
            proof_count=proof_count,
            tx_hash=fake_tx_hash(),
            block_number=block_num + random.randint(0, 10000),
            status=AnchorStatus.confirmed,
            anchor_date=anchor_date,
            proof_hashes=proof_hashes_for_anchor,
            gas_used=gas_used_k * 1000 + random.randint(0, 5000),
            gas_price_gwei=gas_price,
            contract_address=fake_contract_address(),
            created_at=anchor_date,
            updated_at=anchor_date,
        )
        db.add(anchor)
        db.flush()

        # Create proof anchor mappings
        for i in range(proof_count):
            if v_idx < len(completed_v_ids):
                vid = completed_v_ids[v_idx]
                v_idx += 1
            else:
                vid = completed_v_ids[random.randint(0, len(completed_v_ids) - 1)]

            mapping = ProofAnchorMapping(
                id=uuid.uuid4(),
                anchor_id=anchor_id,
                verification_id=vid,
                organization_id=org_id,
                proof_hash=proof_hashes_for_anchor[i],
                merkle_index=i,
                merkle_proof=[sha256(f"sibling-{anchor_id}-{i}-{j}") for j in range(3)],
                created_at=anchor_date,
                updated_at=anchor_date,
            )
            db.add(mapping)

        print(f"  [ok] {chain_label} anchor: {proof_count} proofs, block #{anchor.block_number}")

    db.flush()


def seed_schedules(db: Session, org_id, user_id, verification_ids: list) -> list:
    """Create 3 verification schedules. Returns schedule IDs."""
    print("\n[5/9] Seeding verification schedules...")

    schedule_defs = [
        {
            "name": "Daily Private Credit Health Check",
            "module": "private_credit",
            "frequency": ScheduleFrequency.daily,
            "drift_threshold_pct": Decimal("5.00"),
            "input_data": {
                "check_type": "covenant_monitoring",
                "portfolios": ["Meridian Direct Lending Fund III", "Atlas Special Situations Fund II"],
                "metrics": ["ltv_ratio", "dscr", "payment_status"],
            },
            "metadata": {"priority": "high", "notify_on_breach": True},
            "run_count": 45,
        },
        {
            "name": "Weekly AI-IP Revaluation",
            "module": "ai_ip_valuation",
            "frequency": ScheduleFrequency.weekly,
            "drift_threshold_pct": Decimal("10.00"),
            "input_data": {
                "check_type": "market_revaluation",
                "assets": ["MedVision-3B Diagnostic Model", "FinSentiment-XL NLP Engine", "AutoDrive Perception Model v2"],
                "methods": ["income_approach", "market_approach"],
            },
            "metadata": {"priority": "medium", "include_benchmarks": True},
            "run_count": 12,
        },
        {
            "name": "Monthly Comprehensive Audit",
            "module": "private_credit",
            "frequency": ScheduleFrequency.monthly,
            "drift_threshold_pct": Decimal("15.00"),
            "input_data": {
                "check_type": "full_audit",
                "scope": "all_portfolios_and_assets",
                "include_blockchain_verification": True,
                "include_lineage_report": True,
            },
            "metadata": {"priority": "critical", "compliance_required": True, "report_recipients": ["cfo@meridian.com", "risk@aimadds.com"]},
            "run_count": 3,
        },
    ]

    schedule_ids = []
    for sdef in schedule_defs:
        existing = db.execute(
            select(VerificationSchedule).where(
                VerificationSchedule.organization_id == org_id,
                VerificationSchedule.name == sdef["name"],
                VerificationSchedule.is_deleted == False,
            )
        ).scalar_one_or_none()
        if existing:
            print(f"  [skip] {sdef['name']} already exists")
            schedule_ids.append(existing.id)
            continue

        s_id = uuid.uuid4()
        last_run = random_past(max_days=3, min_days=0)

        if sdef["frequency"] == ScheduleFrequency.daily:
            next_run = NOW + timedelta(hours=random.randint(1, 20))
        elif sdef["frequency"] == ScheduleFrequency.weekly:
            next_run = NOW + timedelta(days=random.randint(1, 6))
        else:
            next_run = NOW + timedelta(days=random.randint(5, 25))

        last_vid = verification_ids[random.randint(0, len(verification_ids) - 1)] if verification_ids else None

        schedule = VerificationSchedule(
            id=s_id,
            organization_id=org_id,
            name=sdef["name"],
            module=sdef["module"],
            frequency=sdef["frequency"],
            input_data=sdef["input_data"],
            extra_metadata=sdef["metadata"],
            is_active=True,
            last_run_at=last_run,
            next_run_at=next_run,
            created_by=user_id,
            drift_threshold_pct=sdef["drift_threshold_pct"],
            last_verification_id=last_vid,
            run_count=sdef["run_count"],
            created_at=random_past(max_days=90, min_days=60),
            updated_at=last_run,
        )
        db.add(schedule)
        schedule_ids.append(s_id)
        print(f"  [ok] {sdef['name']} ({sdef['frequency'].value}, next: {next_run.strftime('%Y-%m-%d %H:%M')} UTC)")

    db.flush()
    return schedule_ids


def seed_drift_alerts(db: Session, org_id, schedule_ids: list, verification_ids: list) -> None:
    """Create 5 drift alerts with varying severities."""
    print("\n[6/9] Seeding drift alerts...")

    existing = db.execute(
        select(DriftAlert).where(
            DriftAlert.organization_id == org_id,
            DriftAlert.is_deleted == False,
        )
    ).scalars().all()
    if len(existing) >= 5:
        print(f"  [skip] Already have {len(existing)} drift alerts")
        return

    alert_defs = [
        {
            "severity": AlertSeverity.critical,
            "status": AlertStatus.active,
            "alert_type": "covenant_violation",
            "message": "Atlas SSF II: LTV ratio breached maximum threshold (1.09 vs 1.20 limit). Borrower BRW-D101 collateral shortfall of $336K.",
            "drift_pct": Decimal("18.2500"),
            "details": {"portfolio": "Atlas Special Situations Fund II", "metric": "ltv_ratio", "current": 1.09, "threshold": 0.85, "loan_id": "ASS-2024-001"},
        },
        {
            "severity": AlertSeverity.critical,
            "status": AlertStatus.acknowledged,
            "alert_type": "nav_drift",
            "message": "Horizon Venture Debt Fund IV: NAV decreased by 12.4% from previous period ($51.7M to $45.3M). Two loans moved to delinquent status.",
            "drift_pct": Decimal("12.4000"),
            "details": {"portfolio": "Horizon Venture Debt Fund IV", "previous_nav": 51700000, "current_nav": 45300000, "delinquent_count": 2},
        },
        {
            "severity": AlertSeverity.warning,
            "status": AlertStatus.active,
            "alert_type": "value_change",
            "message": "FinSentiment-XL NLP Engine: Estimated value decreased by 7.3% due to increased competition in financial NLP market.",
            "drift_pct": Decimal("7.3000"),
            "details": {"asset": "FinSentiment-XL NLP Engine", "previous_value": 11520000, "current_value": 10680000, "driver": "market_competition"},
        },
        {
            "severity": AlertSeverity.warning,
            "status": AlertStatus.resolved,
            "alert_type": "ltv_breach",
            "message": "Cascade Mid-Market: Loan CML-2025-007 DSCR approaching minimum threshold (1.15 vs 1.50 requirement). Watchlist recommended.",
            "drift_pct": Decimal("5.8000"),
            "details": {"portfolio": "Cascade Mid-Market Lending Series A", "loan_id": "CML-2025-007", "dscr": 1.15, "threshold": 1.50},
        },
        {
            "severity": AlertSeverity.info,
            "status": AlertStatus.resolved,
            "alert_type": "value_change",
            "message": "MedVision-3B Diagnostic Model: Value increased by 3.2% following FDA 510(k) submission milestone completion.",
            "drift_pct": Decimal("3.2000"),
            "details": {"asset": "MedVision-3B Diagnostic Model", "previous_value": 11400000, "current_value": 11760000, "driver": "regulatory_milestone"},
        },
    ]

    for i, adef in enumerate(alert_defs):
        schedule_id = schedule_ids[i % len(schedule_ids)]
        vid = verification_ids[i % len(verification_ids)]
        prev_vid = verification_ids[(i + 1) % len(verification_ids)] if i > 0 else None
        created = random_past(max_days=20, min_days=1)

        alert = DriftAlert(
            id=uuid.uuid4(),
            organization_id=org_id,
            schedule_id=schedule_id,
            verification_id=vid,
            previous_verification_id=prev_vid,
            severity=adef["severity"],
            status=adef["status"],
            alert_type=adef["alert_type"],
            message=adef["message"],
            details=adef["details"],
            drift_pct=adef["drift_pct"],
            acknowledged_at=created + timedelta(hours=2) if adef["status"] != AlertStatus.active else None,
            created_at=created,
            updated_at=created,
        )
        db.add(alert)
        sev_label = adef["severity"].value.upper()
        print(f"  [{sev_label[:4]}] {adef['alert_type']}: {adef['message'][:70]}...")

    db.flush()


def seed_notifications(db: Session, org_id, user_id, verification_ids: list) -> None:
    """Create 10 notifications of various types."""
    print("\n[7/9] Seeding notifications...")

    existing = db.execute(
        select(Notification).where(
            Notification.organization_id == org_id,
            Notification.is_deleted == False,
        )
    ).scalars().all()
    if len(existing) >= 10:
        print(f"  [skip] Already have {len(existing)} notifications")
        return

    notif_defs = [
        {
            "type": NotificationType.verification_completed,
            "title": "Verification Complete: Meridian Fund III",
            "message": "Private credit verification for Meridian Direct Lending Fund III completed successfully. NAV: $128.5M. All covenants met.",
            "is_read": True,
            "days_ago": 15,
        },
        {
            "type": NotificationType.drift_alert,
            "title": "CRITICAL: Atlas SSF II Covenant Breach",
            "message": "LTV ratio for Atlas Special Situations Fund II has breached the maximum threshold. Borrower BRW-D101 shows collateral shortfall. Immediate review required.",
            "is_read": True,
            "days_ago": 12,
        },
        {
            "type": NotificationType.covenant_breach,
            "title": "Covenant Warning: Horizon Fund IV",
            "message": "Loan HVD-2025-006 DSCR has fallen below 1.0 (current: 0.92). Payment is 60 days late. Restructuring options should be evaluated.",
            "is_read": True,
            "days_ago": 10,
        },
        {
            "type": NotificationType.verification_completed,
            "title": "AI-IP Valuation: AutoDrive v2",
            "message": "Cost-approach valuation for AutoDrive Perception Model v2 completed. Estimated value: $28.4M with 91% confidence. ASIL-D certification adds significant premium.",
            "is_read": True,
            "days_ago": 8,
        },
        {
            "type": NotificationType.schedule_executed,
            "title": "Daily Health Check Completed",
            "message": "Scheduled daily private credit health check completed for 5 portfolios. 2 items flagged for review: Atlas SSF II (covenant breach), Horizon Fund IV (delinquency).",
            "is_read": False,
            "days_ago": 3,
        },
        {
            "type": NotificationType.usage_limit_warning,
            "title": "API Usage: 80% of Monthly Limit",
            "message": "Your organization has used 80% of the monthly verification limit (8/10). Consider upgrading to Professional plan for unlimited verifications.",
            "is_read": False,
            "days_ago": 2,
        },
        {
            "type": NotificationType.verification_completed,
            "title": "Pinnacle Senior Secured Fund Audit",
            "message": "Monthly comprehensive audit completed for Pinnacle Senior Secured Fund I. All 15 loans performing. NAV: $567.2M. Investment grade quality maintained.",
            "is_read": False,
            "days_ago": 2,
        },
        {
            "type": NotificationType.drift_alert,
            "title": "Value Change: FinSentiment-XL",
            "message": "FinSentiment-XL NLP Engine value decreased by 7.3% from previous assessment. Increased competition in financial NLP market identified as primary driver.",
            "is_read": False,
            "days_ago": 1,
        },
        {
            "type": NotificationType.verification_failed,
            "title": "Verification Failed: SpeechGen TTS",
            "message": "AI-IP valuation for SpeechGen Real-Time TTS failed due to API timeout. The system will retry automatically in 15 minutes. If the issue persists, check provider connectivity.",
            "is_read": False,
            "days_ago": 1,
        },
        {
            "type": NotificationType.verification_completed,
            "title": "Blockchain Anchor Confirmed",
            "message": "Batch of 5 verification proofs anchored to Polygon (block #58,224,832). Transaction confirmed with 128 block confirmations. Merkle root stored on-chain.",
            "is_read": False,
            "days_ago": 0,
        },
    ]

    for ndef in notif_defs:
        created = random_past(max_days=ndef["days_ago"], min_days=max(0, ndef["days_ago"] - 1))
        read_at = created + timedelta(hours=random.randint(1, 6)) if ndef["is_read"] else None
        ref_id = str(verification_ids[random.randint(0, min(len(verification_ids) - 1, 10))]) if verification_ids else None

        notif = Notification(
            id=uuid.uuid4(),
            organization_id=org_id,
            user_id=user_id,
            notification_type=ndef["type"],
            channel=NotificationChannel.in_app,
            title=ndef["title"],
            message=ndef["message"],
            details={"source": "seed_script"},
            is_read=ndef["is_read"],
            read_at=read_at,
            reference_id=ref_id,
            reference_type="verification",
            created_at=created,
            updated_at=created,
        )
        db.add(notif)
        read_icon = "read" if ndef["is_read"] else "NEW "
        print(f"  [{read_icon}] {ndef['type'].value}: {ndef['title'][:60]}")

    db.flush()


def seed_audit_logs(db: Session, org_id, user_id, verification_ids: list) -> None:
    """Create 20 audit log entries spread over the last month."""
    print("\n[8/9] Seeding audit logs...")

    existing = db.execute(
        select(AuditLog).where(AuditLog.organization_id == org_id)
    ).scalars().all()
    if len(existing) >= 20:
        print(f"  [skip] Already have {len(existing)} audit log entries")
        return

    ip_addresses = ["192.168.1.42", "10.0.0.15", "172.16.0.88", "203.0.113.25", "198.51.100.12"]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 Safari/17.3",
        "python-httpx/0.27.0",
        "ZKValue-CLI/1.0.0",
    ]

    log_entries = [
        ("user.login", "user", "Login from Chrome on Windows", 28),
        ("user.login", "user", "Login from Safari on macOS", 27),
        ("settings.update", "organization", "Updated LLM provider to deepseek-chat", 26),
        ("portfolio.upload", "credit_portfolio", "Uploaded Meridian Fund III loan tape (12 loans)", 25),
        ("verification.create", "verification", "Created private credit verification for Meridian Fund III", 24),
        ("verification.complete", "verification", "Completed verification - NAV $128.5M", 24),
        ("portfolio.upload", "credit_portfolio", "Uploaded Atlas SSF II loan tape (5 loans)", 22),
        ("verification.create", "verification", "Created private credit verification for Atlas SSF II", 21),
        ("verification.complete", "verification", "Completed verification - NAV $18.8M, covenant breach detected", 21),
        ("asset.create", "ai_asset", "Created AI-IP asset: MedVision-3B Diagnostic Model", 18),
        ("verification.create", "verification", "Created AI-IP valuation for MedVision-3B", 18),
        ("verification.complete", "verification", "Completed valuation - $11.76M (cost approach)", 18),
        ("schedule.create", "verification_schedule", "Created Daily Private Credit Health Check schedule", 15),
        ("schedule.create", "verification_schedule", "Created Weekly AI-IP Revaluation schedule", 15),
        ("blockchain.anchor", "blockchain_anchor", "Anchored 5 proofs to Polygon (block #58,214,832)", 12),
        ("user.login", "user", "Login via API (python-httpx)", 10),
        ("verification.create", "verification", "Created AI-IP valuation for AutoDrive v2", 8),
        ("verification.complete", "verification", "Completed valuation - $28.4M (cost approach)", 8),
        ("settings.update", "organization", "Enabled webhook notifications for drift alerts", 5),
        ("user.login", "user", "Login from ZKValue CLI", 2),
    ]

    for action, resource_type, description, days_ago in log_entries:
        created = random_past(max_days=days_ago, min_days=max(0, days_ago - 1))
        resource_id = str(verification_ids[random.randint(0, min(len(verification_ids) - 1, 10))]) if "verification" in resource_type else str(uuid.uuid4())

        log = AuditLog(
            id=uuid.uuid4(),
            organization_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"description": description},
            ip_address=random.choice(ip_addresses),
            user_agent=random.choice(user_agents),
            timestamp=created,
            created_at=created,
            updated_at=created,
        )
        db.add(log)
        print(f"  [log] {action}: {description[:65]}")

    db.flush()


def seed_model_usage(db: Session, org_id, verification_ids: list) -> None:
    """Create 15 model usage records showing LLM calls."""
    print("\n[9/9] Seeding model usage records & data lineage...")

    existing_usage = db.execute(
        select(ModelUsageRecord).where(ModelUsageRecord.organization_id == org_id, ModelUsageRecord.is_deleted == False)
    ).scalars().all()
    if len(existing_usage) >= 15:
        print(f"  [skip] Already have {len(existing_usage)} usage records")
        return

    usage_defs = [
        (ModelProvider.deepseek, "deepseek-chat", "classify_asset_type", 2400, 850, 0.35, 1820, "0.0032"),
        (ModelProvider.deepseek, "deepseek-chat", "analyze_loan_tape", 8500, 3200, 0.70, 4250, "0.0117"),
        (ModelProvider.deepseek, "deepseek-chat", "covenant_compliance_check", 4200, 1500, 0.45, 2890, "0.0057"),
        (ModelProvider.deepseek, "deepseek-chat", "generate_executive_summary", 3800, 2800, 0.50, 3100, "0.0066"),
        (ModelProvider.deepseek, "deepseek-chat", "risk_factor_extraction", 6200, 2100, 0.55, 3450, "0.0083"),
        (ModelProvider.openai, "gpt-4o", "valuation_reasoning", 5500, 4200, 0.40, 5800, "0.0485"),
        (ModelProvider.openai, "gpt-4o", "comparable_transaction_analysis", 7800, 3500, 0.35, 6200, "0.0565"),
        (ModelProvider.openai, "gpt-4o-mini", "data_classification", 1200, 600, 0.60, 980, "0.0009"),
        (ModelProvider.anthropic, "claude-sonnet-4-20250514", "regulatory_compliance_check", 9200, 5800, 0.30, 8500, "0.1050"),
        (ModelProvider.anthropic, "claude-sonnet-4-20250514", "ias38_assessment", 6800, 4100, 0.35, 7200, "0.0762"),
        (ModelProvider.deepseek, "deepseek-chat", "anomaly_detection", 3500, 1200, 0.80, 2100, "0.0047"),
        (ModelProvider.deepseek, "deepseek-chat", "portfolio_summary_generation", 4800, 3500, 0.50, 3800, "0.0083"),
        (ModelProvider.openai, "gpt-4o", "benchmark_comparison", 4200, 2800, 0.40, 4500, "0.0350"),
        (ModelProvider.deepseek, "deepseek-chat", "collateral_analysis", 5100, 1800, 0.55, 2950, "0.0069"),
        (ModelProvider.anthropic, "claude-sonnet-4-20250514", "full_audit_report_generation", 12000, 8500, 0.25, 12800, "0.1430"),
    ]

    for i, (provider, model, operation, in_tokens, out_tokens, temp, latency, cost) in enumerate(usage_defs):
        vid = verification_ids[i % len(verification_ids)]
        created = random_past(max_days=30, min_days=0)

        record = ModelUsageRecord(
            id=uuid.uuid4(),
            organization_id=org_id,
            verification_id=vid,
            provider=provider,
            model_name=model,
            model_version="latest",
            operation=operation,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            total_tokens=in_tokens + out_tokens,
            latency_ms=latency,
            temperature=temp,
            max_tokens=8192,
            prompt_hash=sha256(f"prompt-{operation}-{i}"),
            response_hash=sha256(f"response-{operation}-{i}"),
            cost_usd=float(cost),
            success="true",
            created_at=created,
            updated_at=created,
        )
        db.add(record)
        print(f"  [llm] {provider.value}/{model}: {operation} ({in_tokens + out_tokens} tokens, ${cost})")

    db.flush()

    # ── Data Lineage Events ──
    existing_lineage = db.execute(
        select(DataLineageEvent).where(DataLineageEvent.organization_id == org_id, DataLineageEvent.is_deleted == False)
    ).scalars().all()
    if len(existing_lineage) >= 10:
        print(f"  [skip] Already have {len(existing_lineage)} lineage events")
        return

    # Create a pipeline of 10 events across 2 verifications
    pipeline_vid_1 = verification_ids[0]  # A credit portfolio verification
    pipeline_vid_2 = verification_ids[5] if len(verification_ids) > 5 else verification_ids[0]  # An AI-IP verification

    lineage_steps = [
        # Pipeline 1: Private Credit verification
        (pipeline_vid_1, LineageEventType.data_ingestion, 1, "Ingest loan tape CSV (12 loans, 48 fields)", 450, {"format": "CSV", "rows": 12, "columns": 48, "file_size_mb": 2.4}),
        (pipeline_vid_1, LineageEventType.preprocessing, 2, "Normalize and validate loan data fields", 320, {"validations_passed": 12, "validations_failed": 0, "fields_normalized": 15}),
        (pipeline_vid_1, LineageEventType.llm_classification, 3, "Classify loan risk tiers via DeepSeek", 2890, {"model": "deepseek-chat", "classifications": {"low_risk": 9, "medium_risk": 2, "high_risk": 1}}),
        (pipeline_vid_1, LineageEventType.computation, 4, "Calculate portfolio metrics (NAV, LTV, DSCR)", 180, {"metrics_computed": ["nav", "weighted_avg_rate", "avg_ltv", "concentration_risk"]}),
        (pipeline_vid_1, LineageEventType.proof_generation, 5, "Generate SHA-256 computation proof", 95, {"proof_type": "sha256", "input_size_bytes": 14520}),
        # Pipeline 2: AI-IP Valuation
        (pipeline_vid_2, LineageEventType.data_ingestion, 1, "Ingest asset metadata and financial data", 280, {"fields": 18, "attachments": 3}),
        (pipeline_vid_2, LineageEventType.llm_analysis, 2, "Analyze comparable transactions via GPT-4o", 6200, {"model": "gpt-4o", "comparables_found": 8, "relevance_scores": [0.92, 0.88, 0.85, 0.81, 0.76, 0.72, 0.68, 0.61]}),
        (pipeline_vid_2, LineageEventType.valuation, 3, "Compute cost-approach valuation", 420, {"method": "cost_approach", "components": ["training_cost", "data_cost", "compute_cost", "ip_premium"]}),
        (pipeline_vid_2, LineageEventType.proof_generation, 4, "Generate SHA-256 computation proof", 88, {"proof_type": "sha256", "input_size_bytes": 8240}),
        (pipeline_vid_2, LineageEventType.report_generation, 5, "Generate PDF valuation report", 3500, {"pages": 12, "charts": 4, "tables": 6}),
    ]

    parent_ids = {}  # Track parent event IDs per verification
    for vid, event_type, step, transformation, duration, details in lineage_steps:
        created = random_past(max_days=15, min_days=5)
        event_id = uuid.uuid4()

        parent_id = parent_ids.get((vid, step - 1))

        event = DataLineageEvent(
            id=event_id,
            organization_id=org_id,
            verification_id=vid,
            event_type=event_type,
            step_order=step,
            input_hash=sha256(f"lineage-input-{vid}-{step}"),
            output_hash=sha256(f"lineage-output-{vid}-{step}"),
            transformation=transformation,
            details=details,
            duration_ms=duration,
            parent_event_id=parent_id,
            created_at=created,
            updated_at=created,
        )
        db.add(event)
        parent_ids[(vid, step)] = event_id
        print(f"  [dag] Step {step}: {transformation[:60]}")

    db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Seed production demo data for verifAI / ZKValue")
    parser.add_argument("--email", default="smaan@aimadds.com", help="Email of user to seed data for")
    parser.add_argument("--database-url", default=None, help="Database URL (falls back to DATABASE_URL env var)")
    args = parser.parse_args()

    # Resolve database URL
    db_url = args.database_url or os.environ.get("DATABASE_URL", "")
    if not db_url:
        # Try loading from the app config
        try:
            from app.core.config import settings
            db_url = settings.DATABASE_URL
        except Exception:
            pass

    if not db_url:
        print("ERROR: No database URL provided. Use --database-url or set DATABASE_URL env var.")
        sys.exit(1)

    # Convert async URL to sync
    sync_url = db_url.replace("+asyncpg", "").replace("postgresql+aiopg", "postgresql")
    if sync_url.startswith("postgres://"):
        sync_url = sync_url.replace("postgres://", "postgresql://", 1)

    print(f"=" * 70)
    print(f"  verifAI / ZKValue Production Demo Seed")
    print(f"  Target user: {args.email}")
    print(f"  Database: {sync_url.split('@')[-1] if '@' in sync_url else '(local)'}")
    print(f"=" * 70)

    engine = create_engine(sync_url, echo=False)

    with Session(engine) as db:
        # Find user
        user = db.execute(select(User).where(User.email == args.email)).scalar_one_or_none()
        if not user:
            print(f"\nERROR: No user found with email '{args.email}'.")
            print("  Register at http://localhost/register first, or use --email <existing_email>")
            sys.exit(1)

        org_id = user.organization_id
        user_id = user.id
        print(f"\nUser: {user.full_name} ({user.email})")
        print(f"Org:  {org_id}")
        print(f"Role: {user.role.value}")

        # Seed all modules
        credit_v_ids = seed_credit_portfolios(db, org_id, user_id)
        ai_v_ids = seed_ai_ip_assets(db, org_id, user_id)
        trend_v_ids = seed_trend_verifications(db, org_id, user_id)

        all_v_ids = credit_v_ids + ai_v_ids + trend_v_ids

        seed_blockchain_anchors(db, org_id, all_v_ids)
        schedule_ids = seed_schedules(db, org_id, user_id, all_v_ids)
        seed_drift_alerts(db, org_id, schedule_ids, all_v_ids)
        seed_notifications(db, org_id, user_id, all_v_ids)
        seed_audit_logs(db, org_id, user_id, all_v_ids)
        seed_model_usage(db, org_id, all_v_ids)

        db.commit()

    print(f"\n{'=' * 70}")
    print("  Seed complete!")
    print(f"  - 5 credit portfolios (46 loans total)")
    print(f"  - 6 AI-IP assets")
    print(f"  - 18 trend verifications")
    print(f"  - 3 blockchain anchors with proof mappings")
    print(f"  - 3 verification schedules")
    print(f"  - 5 drift alerts")
    print(f"  - 10 notifications")
    print(f"  - 20 audit log entries")
    print(f"  - 15 model usage records")
    print(f"  - 10 data lineage events")
    print(f"{'=' * 70}")
    print("  Refresh your dashboard to see the data.")


if __name__ == "__main__":
    main()
