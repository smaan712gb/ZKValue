"""
Seed realistic demo data for ZKValue platform testing.
Run inside the backend container:
  docker exec zkvalue-backend python scripts/seed_demo_data.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy import select, text
from app.core.database import async_session_factory
from app.models.user import User
from app.models.verification import Verification, VerificationModule, VerificationStatus
from app.models.credit_portfolio import CreditPortfolio
from app.models.ai_asset import AIAsset
from app.services.verification.proof import ProofService
import json
import hashlib
import random


# ═══════════════════════════════════════════════════════════
# REALISTIC PRIVATE CREDIT PORTFOLIOS
# ═══════════════════════════════════════════════════════════

CREDIT_PORTFOLIOS = [
    {
        "portfolio_name": "Meridian Direct Lending Fund III — Q4 2025",
        "fund_name": "Meridian Capital Partners",
        "loans": [
            {"loan_id": "MDL-2024-001", "borrower_id": "BRW-7891", "principal": 15000000, "interest_rate": 9.25, "term_months": 60, "origination_date": "2024-03-15", "maturity_date": "2029-03-15", "collateral_value": 22500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 14250000, "ltv_ratio": 0.63, "dscr": 1.85},
            {"loan_id": "MDL-2024-002", "borrower_id": "BRW-3456", "principal": 8500000, "interest_rate": 10.50, "term_months": 48, "origination_date": "2024-05-20", "maturity_date": "2028-05-20", "collateral_value": 12750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 8075000, "ltv_ratio": 0.63, "dscr": 2.10},
            {"loan_id": "MDL-2024-003", "borrower_id": "BRW-5672", "principal": 22000000, "interest_rate": 8.75, "term_months": 72, "origination_date": "2024-01-10", "maturity_date": "2030-01-10", "collateral_value": 30800000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 21340000, "ltv_ratio": 0.69, "dscr": 1.65},
            {"loan_id": "MDL-2024-004", "borrower_id": "BRW-8901", "principal": 5500000, "interest_rate": 11.00, "term_months": 36, "origination_date": "2024-07-01", "maturity_date": "2027-07-01", "collateral_value": 7150000, "collateral_type": "Second Lien", "payment_status": "current", "outstanding_balance": 5280000, "ltv_ratio": 0.74, "dscr": 1.42},
            {"loan_id": "MDL-2024-005", "borrower_id": "BRW-2345", "principal": 12000000, "interest_rate": 9.75, "term_months": 60, "origination_date": "2024-04-15", "maturity_date": "2029-04-15", "collateral_value": 18000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 11400000, "ltv_ratio": 0.63, "dscr": 1.92},
            {"loan_id": "MDL-2024-006", "borrower_id": "BRW-6789", "principal": 18500000, "interest_rate": 8.50, "term_months": 84, "origination_date": "2024-02-28", "maturity_date": "2031-02-28", "collateral_value": 27750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 17945000, "ltv_ratio": 0.65, "dscr": 1.78},
            {"loan_id": "MDL-2024-007", "borrower_id": "BRW-1234", "principal": 7200000, "interest_rate": 10.25, "term_months": 48, "origination_date": "2024-06-10", "maturity_date": "2028-06-10", "collateral_value": 9360000, "collateral_type": "Senior Secured - First Lien", "payment_status": "30_days_late", "outstanding_balance": 6912000, "ltv_ratio": 0.74, "dscr": 1.15},
            {"loan_id": "MDL-2024-008", "borrower_id": "BRW-4567", "principal": 25000000, "interest_rate": 8.25, "term_months": 60, "origination_date": "2024-08-01", "maturity_date": "2029-08-01", "collateral_value": 37500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 24500000, "ltv_ratio": 0.65, "dscr": 2.25},
            {"loan_id": "MDL-2024-009", "borrower_id": "BRW-9012", "principal": 3800000, "interest_rate": 12.00, "term_months": 36, "origination_date": "2024-09-15", "maturity_date": "2027-09-15", "collateral_value": 4940000, "collateral_type": "Unitranche", "payment_status": "current", "outstanding_balance": 3724000, "ltv_ratio": 0.75, "dscr": 1.55},
            {"loan_id": "MDL-2024-010", "borrower_id": "BRW-3451", "principal": 10000000, "interest_rate": 9.50, "term_months": 60, "origination_date": "2024-10-01", "maturity_date": "2029-10-01", "collateral_value": 14000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 9800000, "ltv_ratio": 0.70, "dscr": 1.88},
            {"loan_id": "MDL-2024-011", "borrower_id": "BRW-7823", "principal": 6700000, "interest_rate": 10.75, "term_months": 48, "origination_date": "2024-11-15", "maturity_date": "2028-11-15", "collateral_value": 8710000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 6633000, "ltv_ratio": 0.76, "dscr": 1.62},
            {"loan_id": "MDL-2024-012", "borrower_id": "BRW-5601", "principal": 14000000, "interest_rate": 9.00, "term_months": 72, "origination_date": "2024-03-01", "maturity_date": "2030-03-01", "collateral_value": 21000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 13580000, "ltv_ratio": 0.65, "dscr": 1.95},
        ],
        "covenants": {"max_ltv": 0.80, "min_dscr": 1.20, "max_single_borrower_concentration": 0.20, "min_portfolio_yield": 8.0},
    },
    {
        "portfolio_name": "Atlas Special Situations Fund II — Distressed",
        "fund_name": "Atlas Credit Management",
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
        "portfolio_name": "Cascade Mid-Market Lending — Series A",
        "fund_name": "Cascade Capital Advisors",
        "loans": [
            {"loan_id": "CML-2025-001", "borrower_id": "BRW-M201", "principal": 35000000, "interest_rate": 7.75, "term_months": 84, "origination_date": "2025-01-15", "maturity_date": "2032-01-15", "collateral_value": 52500000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 34650000, "ltv_ratio": 0.66, "dscr": 2.40},
            {"loan_id": "CML-2025-002", "borrower_id": "BRW-M202", "principal": 20000000, "interest_rate": 8.25, "term_months": 60, "origination_date": "2025-02-01", "maturity_date": "2030-02-01", "collateral_value": 28000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 19800000, "ltv_ratio": 0.71, "dscr": 2.15},
            {"loan_id": "CML-2025-003", "borrower_id": "BRW-M203", "principal": 28000000, "interest_rate": 8.00, "term_months": 72, "origination_date": "2025-01-20", "maturity_date": "2031-01-20", "collateral_value": 39200000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 27720000, "ltv_ratio": 0.71, "dscr": 2.05},
            {"loan_id": "CML-2025-004", "borrower_id": "BRW-M204", "principal": 15000000, "interest_rate": 8.50, "term_months": 60, "origination_date": "2025-02-15", "maturity_date": "2030-02-15", "collateral_value": 21750000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 14850000, "ltv_ratio": 0.68, "dscr": 2.30},
            {"loan_id": "CML-2025-005", "borrower_id": "BRW-M205", "principal": 42000000, "interest_rate": 7.50, "term_months": 84, "origination_date": "2025-01-05", "maturity_date": "2032-01-05", "collateral_value": 63000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 41580000, "ltv_ratio": 0.66, "dscr": 2.55},
            {"loan_id": "CML-2025-006", "borrower_id": "BRW-M206", "principal": 18500000, "interest_rate": 8.75, "term_months": 60, "origination_date": "2025-03-01", "maturity_date": "2030-03-01", "collateral_value": 25900000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 18315000, "ltv_ratio": 0.71, "dscr": 2.20},
            {"loan_id": "CML-2025-007", "borrower_id": "BRW-M207", "principal": 12000000, "interest_rate": 9.00, "term_months": 48, "origination_date": "2025-02-20", "maturity_date": "2029-02-20", "collateral_value": 16800000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 11880000, "ltv_ratio": 0.71, "dscr": 1.95},
            {"loan_id": "CML-2025-008", "borrower_id": "BRW-M208", "principal": 50000000, "interest_rate": 7.25, "term_months": 96, "origination_date": "2025-01-10", "maturity_date": "2033-01-10", "collateral_value": 75000000, "collateral_type": "Senior Secured - First Lien", "payment_status": "current", "outstanding_balance": 49500000, "ltv_ratio": 0.66, "dscr": 2.70},
        ],
        "covenants": {"max_ltv": 0.75, "min_dscr": 1.50, "max_single_borrower_concentration": 0.25, "min_portfolio_yield": 7.5},
    },
]


# ═══════════════════════════════════════════════════════════
# REALISTIC AI-IP ASSETS
# ═══════════════════════════════════════════════════════════

AI_IP_ASSETS = [
    {
        "asset_name": "MedVision-3B Diagnostic Model",
        "asset_type": "model_weights",
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
        "description": "Real-time financial sentiment analysis engine processing 50K+ earnings calls, SEC filings, and news articles daily. Powers trading signals for 8 hedge funds. Fine-tuned from Llama-3 70B on proprietary dataset of 15M annotated financial documents with entity-level sentiment scoring.",
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
        "description": "Proprietary graph-structured dataset of 480M anonymized purchase interactions across 12M users and 2.8M SKUs from 3 major US retailers (2019-2025). Includes temporal purchasing patterns, cross-category affinity scores, and seasonal decomposition. Licensed non-exclusively to 4 ML teams.",
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
        "description": "On-premise GPU inference cluster (96x NVIDIA L40S) with custom CUDA kernels, TensorRT optimization pipeline, and auto-scaling orchestration layer. Sub-10ms P99 latency for models up to 13B parameters. Deployed across 3 data centers serving 2.1M daily inference requests.",
        "training_cost": 0,
        "training_compute_hours": 0,
        "monthly_revenue": 520000,
        "monthly_active_users": 180,
        "inference_cost_per_query": 0.003,
        "gpu_type": "NVIDIA L40S",
        "gpu_count": 96,
        "cloud_provider": "On-Premise",
    },
]


def compute_portfolio_metrics(loans):
    total_principal = sum(l["principal"] for l in loans)
    total_balance = sum(l["outstanding_balance"] for l in loans)
    weighted_rate = sum(l["principal"] * l["interest_rate"] for l in loans) / total_principal
    avg_ltv = sum(l.get("ltv_ratio", 0.7) for l in loans) / len(loans)
    nav = total_balance * 0.985  # Small discount
    return total_principal, total_balance, weighted_rate, avg_ltv, nav


async def seed():
    async with async_session_factory() as db:
        # Get the first user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("ERROR: No user found. Register an account first at http://localhost/register")
            return

        print(f"Seeding data for user: {user.email} (org: {user.organization_id})")
        org_id = user.organization_id
        user_id = user.id
        now = datetime.now(timezone.utc)
        proof_service = ProofService(db)

        # ── Credit Portfolios ──
        for i, portfolio in enumerate(CREDIT_PORTFOLIOS):
            created = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))
            completed = created + timedelta(minutes=random.randint(2, 8))

            input_data = {
                "portfolio_name": portfolio["portfolio_name"],
                "fund_name": portfolio["fund_name"],
                "loans": portfolio["loans"],
                "covenants": portfolio.get("covenants"),
            }

            total_principal, total_balance, weighted_rate, avg_ltv, nav = compute_portfolio_metrics(portfolio["loans"])

            # Check covenant compliance
            covenants = portfolio.get("covenants", {})
            covenant_status = {}
            if covenants:
                covenant_status["max_ltv"] = {"limit": covenants.get("max_ltv"), "actual": round(avg_ltv, 3), "compliant": avg_ltv <= covenants.get("max_ltv", 1.0)}
                min_dscr_actual = min(l.get("dscr", 999) for l in portfolio["loans"])
                covenant_status["min_dscr"] = {"limit": covenants.get("min_dscr"), "actual": round(min_dscr_actual, 2), "compliant": min_dscr_actual >= covenants.get("min_dscr", 0)}
                max_conc = max(l["principal"] for l in portfolio["loans"]) / total_principal
                covenant_status["max_concentration"] = {"limit": covenants.get("max_single_borrower_concentration"), "actual": round(max_conc, 3), "compliant": max_conc <= covenants.get("max_single_borrower_concentration", 1.0)}

            result_data = {
                "portfolio_summary": {
                    "total_principal": total_principal,
                    "total_outstanding": total_balance,
                    "weighted_avg_rate": round(weighted_rate, 2),
                    "avg_ltv_ratio": round(avg_ltv, 3),
                    "nav_value": round(nav, 2),
                    "loan_count": len(portfolio["loans"]),
                    "current_loans": sum(1 for l in portfolio["loans"] if l["payment_status"] == "current"),
                    "delinquent_loans": sum(1 for l in portfolio["loans"] if l["payment_status"] != "current"),
                },
                "covenant_compliance": covenant_status,
                "risk_metrics": {
                    "concentration_risk": round(max(l["principal"] for l in portfolio["loans"]) / total_principal, 3),
                    "weighted_avg_dscr": round(sum(l.get("dscr", 1.5) * l["principal"] for l in portfolio["loans"]) / total_principal, 2),
                    "collateral_coverage": round(sum(l["collateral_value"] for l in portfolio["loans"]) / total_balance, 2),
                },
                "executive_summary": f"Portfolio '{portfolio['portfolio_name']}' contains {len(portfolio['loans'])} loans with total principal of ${total_principal:,.0f}. NAV calculated at ${nav:,.0f} with weighted average rate of {weighted_rate:.2f}%. Overall covenant compliance is {'maintained' if all(v.get('compliant', True) for v in covenant_status.values()) else 'in breach on one or more metrics'}.",
            }

            proof = proof_service.create_computation_proof(input_data, result_data, "private_credit")

            verification = Verification(
                id=uuid4(),
                organization_id=org_id,
                created_by=user_id,
                module=VerificationModule.private_credit,
                status=VerificationStatus.completed,
                input_data=input_data,
                result_data=result_data,
                proof_hash=proof["proof_hash"],
                metadata={"portfolio_name": portfolio["portfolio_name"], "fund_name": portfolio["fund_name"]},
                created_at=created,
                completed_at=completed,
            )
            db.add(verification)
            await db.flush()

            cp = CreditPortfolio(
                id=uuid4(),
                organization_id=org_id,
                verification_id=verification.id,
                portfolio_name=portfolio["portfolio_name"],
                fund_name=portfolio["fund_name"],
                loan_count=len(portfolio["loans"]),
                total_principal=total_principal,
                weighted_avg_rate=round(weighted_rate, 2),
                avg_ltv_ratio=round(avg_ltv, 3),
                nav_value=round(nav, 2),
                covenant_compliance_status=covenant_status,
                created_at=created,
            )
            db.add(cp)
            print(f"  ✓ Credit: {portfolio['portfolio_name']} ({len(portfolio['loans'])} loans, ${total_principal:,.0f})")

        # ── AI-IP Assets ──
        valuation_methods = ["cost_approach", "market_approach", "income_approach", "income_approach"]
        for i, asset in enumerate(AI_IP_ASSETS):
            created = now - timedelta(days=random.randint(1, 20), hours=random.randint(0, 23))
            completed = created + timedelta(minutes=random.randint(3, 10))

            input_data = {k: v for k, v in asset.items()}
            # proof generated after result_data below

            # Calculate realistic valuations
            training_cost = asset.get("training_cost", 0)
            monthly_rev = asset.get("monthly_revenue", 0)
            annual_rev = monthly_rev * 12

            if valuation_methods[i] == "cost_approach":
                estimated_value = training_cost * 2.8
            elif valuation_methods[i] == "market_approach":
                estimated_value = annual_rev * 8.5
            else:
                estimated_value = annual_rev * 6.2 + training_cost * 1.5

            confidence = round(random.uniform(0.78, 0.95), 2)

            result_data = {
                "valuation_summary": {
                    "estimated_value": round(estimated_value, 2),
                    "valuation_method": valuation_methods[i],
                    "confidence_score": confidence,
                    "value_range_low": round(estimated_value * 0.85, 2),
                    "value_range_high": round(estimated_value * 1.20, 2),
                },
                "compliance": {
                    "ias38_compliant": asset["asset_type"] in ["model_weights", "deployed_app"],
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
                    f"Training investment of ${training_cost:,.0f} with {'high' if asset.get('dataset_uniqueness_score', 0) > 0.9 else 'moderate'} data moat",
                    f"{asset.get('monthly_active_users', 0):,} active users across licensed deployments",
                ],
                "executive_summary": f"'{asset['asset_name']}' is valued at ${estimated_value:,.0f} using {valuation_methods[i].replace('_', ' ')}. The asset demonstrates {'strong' if confidence > 0.85 else 'moderate'} commercial viability with ${annual_rev:,.0f} annual revenue.",
            }

            proof = proof_service.create_computation_proof(input_data, result_data, "ai_ip_valuation")

            verification = Verification(
                id=uuid4(),
                organization_id=org_id,
                created_by=user_id,
                module=VerificationModule.ai_ip_valuation,
                status=VerificationStatus.completed,
                input_data=input_data,
                result_data=result_data,
                proof_hash=proof["proof_hash"],
                metadata={"asset_name": asset["asset_name"], "asset_type": asset["asset_type"]},
                created_at=created,
                completed_at=completed,
            )
            db.add(verification)
            await db.flush()

            ai_asset = AIAsset(
                id=uuid4(),
                organization_id=org_id,
                verification_id=verification.id,
                asset_type=asset["asset_type"],
                asset_name=asset["asset_name"],
                description=asset["description"],
                valuation_method=valuation_methods[i],
                estimated_value=round(estimated_value, 2),
                confidence_score=confidence,
                valuation_inputs=input_data,
                valuation_breakdown=result_data["valuation_summary"],
                ias38_compliant=result_data["compliance"]["ias38_compliant"],
                asc350_compliant=result_data["compliance"]["asc350_compliant"],
                created_at=created,
            )
            db.add(ai_asset)
            print(f"  ✓ AI-IP: {asset['asset_name']} (${estimated_value:,.0f}, {valuation_methods[i]})")

        await db.commit()
        print(f"\n✅ Seeded {len(CREDIT_PORTFOLIOS)} credit portfolios + {len(AI_IP_ASSETS)} AI-IP assets")
        print("   Refresh http://localhost/dashboard to see the data")


if __name__ == "__main__":
    asyncio.run(seed())
