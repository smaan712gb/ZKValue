"""
ZKValue — End-to-End Production Test Suite
Uses realistic financial data modeled after Lending Club / private credit portfolios.
"""
import asyncio
import random
import string
import sys
import time
from datetime import datetime, timedelta
import httpx

BASE = "http://localhost:8000/api/v1"
TIMEOUT = 60.0

# ---------------------------------------------------------------------------
# Realistic test data generators
# ---------------------------------------------------------------------------

def _rand_id(prefix: str, n: int = 6) -> str:
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=n))}"


def generate_lending_club_style_portfolio(num_loans: int = 25) -> dict:
    """Generate a realistic private credit portfolio modeled on Lending Club data."""
    collateral_types = ["real_estate", "equipment", "inventory", "receivables", "securities"]
    statuses = ["current"] * 18 + ["delinquent"] * 4 + ["default"] * 2 + ["unknown"] * 1
    borrower_ratings = ["AAA", "AA", "A", "BBB", "BB+", "BB", "B+", "B", "CCC"]

    loans = []
    for i in range(num_loans):
        principal = round(random.uniform(250_000, 15_000_000), 2)
        rate = round(random.uniform(0.035, 0.145), 4)
        term = random.choice([12, 18, 24, 36, 48, 60])
        origination = datetime.now() - timedelta(days=random.randint(30, 720))
        maturity = origination + timedelta(days=term * 30)
        collateral_val = round(principal * random.uniform(1.1, 2.5), 2)
        outstanding = round(principal * random.uniform(0.4, 1.0), 2)
        status = random.choice(statuses)

        loans.append({
            "loan_id": _rand_id("LC"),
            "borrower_id": _rand_id("BRW"),
            "principal": principal,
            "interest_rate": rate,
            "term_months": term,
            "origination_date": origination.strftime("%Y-%m-%d"),
            "maturity_date": maturity.strftime("%Y-%m-%d"),
            "collateral_value": collateral_val,
            "collateral_type": random.choice(collateral_types),
            "payment_status": status,
            "outstanding_balance": outstanding,
            "ltv_ratio": round(outstanding / collateral_val, 4),
            "dscr": round(random.uniform(0.8, 3.5), 2),
        })

    return {
        "portfolio_name": "Meridian Capital Direct Lending Fund III",
        "fund_name": "Meridian DLF-III LP",
        "loans": loans,
        "covenants": {
            "dscr_min": 1.25,
            "leverage_max": 4.0,
            "concentration_limit": 0.15,
        },
    }


def generate_mid_market_portfolio(num_loans: int = 15) -> dict:
    """Generate a mid-market leveraged lending portfolio."""
    loans = []
    sectors = ["healthcare", "technology", "manufacturing", "consumer", "energy", "telecom"]
    for i in range(num_loans):
        principal = round(random.uniform(5_000_000, 50_000_000), 2)
        rate = round(random.uniform(0.06, 0.12), 4)
        term = random.choice([36, 48, 60, 72, 84])
        origination = datetime.now() - timedelta(days=random.randint(60, 540))
        maturity = origination + timedelta(days=term * 30)
        collateral_val = round(principal * random.uniform(1.2, 3.0), 2)
        outstanding = round(principal * random.uniform(0.5, 0.95), 2)
        statuses = ["current"] * 12 + ["delinquent"] * 2 + ["default"] * 1

        loans.append({
            "loan_id": _rand_id("MM"),
            "borrower_id": _rand_id("ENT"),
            "principal": principal,
            "interest_rate": rate,
            "term_months": term,
            "origination_date": origination.strftime("%Y-%m-%d"),
            "maturity_date": maturity.strftime("%Y-%m-%d"),
            "collateral_value": collateral_val,
            "collateral_type": random.choice(["real_estate", "equipment", "enterprise_value"]),
            "payment_status": random.choice(statuses),
            "outstanding_balance": outstanding,
            "dscr": round(random.uniform(1.0, 4.0), 2),
        })

    return {
        "portfolio_name": f"Blackrock Mid-Market Credit Fund II",
        "fund_name": "BR-MMCF-II LP",
        "loans": loans,
        "covenants": {
            "dscr_min": 1.50,
            "leverage_max": 3.5,
            "concentration_limit": 0.20,
        },
    }


def generate_distressed_portfolio(num_loans: int = 10) -> dict:
    """Generate a distressed / special situations portfolio with high default rates."""
    loans = []
    for i in range(num_loans):
        principal = round(random.uniform(1_000_000, 25_000_000), 2)
        rate = round(random.uniform(0.10, 0.22), 4)
        term = random.choice([12, 18, 24, 36])
        origination = datetime.now() - timedelta(days=random.randint(180, 900))
        maturity = origination + timedelta(days=term * 30)
        collateral_val = round(principal * random.uniform(0.6, 1.8), 2)
        outstanding = round(principal * random.uniform(0.7, 1.0), 2)
        # High default/delinquency rates for distressed
        statuses = ["current"] * 3 + ["delinquent"] * 4 + ["default"] * 3

        loans.append({
            "loan_id": _rand_id("DST"),
            "borrower_id": _rand_id("DIS"),
            "principal": principal,
            "interest_rate": rate,
            "term_months": term,
            "origination_date": origination.strftime("%Y-%m-%d"),
            "maturity_date": maturity.strftime("%Y-%m-%d"),
            "collateral_value": collateral_val,
            "collateral_type": random.choice(["real_estate", "equipment", "receivables"]),
            "payment_status": random.choice(statuses),
            "outstanding_balance": outstanding,
            "dscr": round(random.uniform(0.5, 1.8), 2),
        })

    return {
        "portfolio_name": "Cerberus Special Situations Fund IV",
        "fund_name": "CSS-IV LP",
        "loans": loans,
        "covenants": {
            "dscr_min": 1.0,
            "leverage_max": 6.0,
            "concentration_limit": 0.25,
        },
    }


def generate_ai_ip_datasets() -> list[dict]:
    """Generate realistic AI/IP asset valuation inputs."""
    return [
        {
            "asset_name": "MedVision Diagnostic AI",
            "asset_type": "deployed_app",
            "description": "FDA-cleared AI diagnostic tool for radiology — identifies 14 pathologies from chest X-rays with 97.3% accuracy. Deployed across 340 hospitals, processing 2.1M scans/month.",
            "cloud_provider": "AWS",
            "training_compute_hours": 45000,
            "training_cost": 1_850_000,
            "dataset_size_gb": 2400,
            "dataset_uniqueness_score": 0.92,
            "model_parameters": 890_000_000,
            "benchmark_scores": {"CheXpert_AUC": 0.973, "MIMIC_F1": 0.951, "NIH_Accuracy": 0.968},
            "monthly_revenue": 4_200_000,
            "monthly_active_users": 12_500,
            "inference_cost_per_query": 0.08,
            "gpu_type": "A100",
            "gpu_count": 32,
        },
        {
            "asset_name": "FinSentiment LLM v3",
            "asset_type": "model_weights",
            "description": "Fine-tuned 13B parameter LLM for financial sentiment analysis and earnings call summarization. Trained on 15 years of SEC filings, earnings transcripts, and analyst reports.",
            "cloud_provider": "GCP",
            "training_compute_hours": 28000,
            "training_cost": 980_000,
            "dataset_size_gb": 850,
            "dataset_uniqueness_score": 0.88,
            "model_parameters": 13_000_000_000,
            "benchmark_scores": {"FinBERT_F1": 0.94, "FiQA_Sentiment": 0.91, "Earnings_ROUGE": 0.87},
            "monthly_revenue": 890_000,
            "monthly_active_users": 3_200,
            "inference_cost_per_query": 0.12,
            "gpu_type": "H100",
            "gpu_count": 8,
        },
        {
            "asset_name": "GlobalTrade Shipping Dataset",
            "asset_type": "training_data",
            "description": "Proprietary dataset of 450M+ global shipping container movements (2015-2025) with real-time AIS data, port congestion metrics, and commodity flow patterns. Used for supply chain prediction models.",
            "dataset_size_gb": 12_000,
            "dataset_uniqueness_score": 0.96,
            "monthly_revenue": 320_000,
        },
        {
            "asset_name": "AutoPilot Edge Inference Platform",
            "asset_type": "inference_infra",
            "description": "Edge AI inference platform for autonomous vehicle perception. 200+ edge nodes processing LiDAR + camera fusion at 30fps with <10ms latency. Deployed in 5 OEM partnerships.",
            "cloud_provider": "Azure",
            "gpu_type": "A100",
            "gpu_count": 200,
            "training_compute_hours": 120_000,
            "training_cost": 4_500_000,
            "monthly_revenue": 2_100_000,
            "monthly_active_users": 45_000,
            "inference_cost_per_query": 0.002,
        },
    ]


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

class E2ETestRunner:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE, timeout=TIMEOUT, follow_redirects=True)
        self.token = None
        self.results = []
        self.verification_ids = []

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _record(self, name: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        self.results.append((name, status, detail))
        icon = "+" if passed else "!"
        print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))

    def test_auth(self):
        print("\n=== 1. AUTHENTICATION ===")

        # Register new org
        ts = int(time.time()) % 100000
        r = self.client.post("/auth/register", json={
            "email": f"test{ts}@meridian-capital.com",
            "password": "M3ridian$ecure2026!",
            "full_name": "Test Portfolio Manager",
            "org_name": f"Meridian Capital Test {ts}",
        })
        self._record("Register new org", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            self.token = r.json()["access_token"]

        # Login
        r = self.client.post("/auth/login", json={
            "email": f"test{ts}@meridian-capital.com",
            "password": "M3ridian$ecure2026!",
        })
        self._record("Login", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            self.token = r.json()["access_token"]

        # Get profile
        r = self.client.get("/auth/me", headers=self._headers())
        self._record("Get profile", r.status_code == 200)

        # Invite user
        r = self.client.post("/auth/invite", headers=self._headers(), json={
            "email": f"analyst{ts}@meridian-capital.com",
            "full_name": "Junior Analyst",
            "role": "analyst",
        })
        self._record("Invite team member", r.status_code == 200, f"HTTP {r.status_code}")

    def test_credit_verifications(self):
        print("\n=== 2. PRIVATE CREDIT VERIFICATIONS ===")

        portfolios = [
            ("Lending Club Style (25 loans)", generate_lending_club_style_portfolio(25)),
            ("Mid-Market (15 loans)", generate_mid_market_portfolio(15)),
            ("Distressed (10 loans)", generate_distressed_portfolio(10)),
        ]

        for name, portfolio in portfolios:
            r = self.client.post("/verifications", headers=self._headers(), json={
                "module": "private_credit",
                "input_data": portfolio,
            })
            if r.status_code == 200:
                vid = r.json()["id"]
                self.verification_ids.append(vid)
                self._record(f"Submit: {name}", True, f"id={vid[:8]}...")
            else:
                self._record(f"Submit: {name}", False, f"HTTP {r.status_code}: {r.text[:100]}")

    def test_ai_ip_verifications(self):
        print("\n=== 3. AI/IP ASSET VALUATIONS ===")

        for asset in generate_ai_ip_datasets():
            r = self.client.post("/verifications", headers=self._headers(), json={
                "module": "ai_ip_valuation",
                "input_data": asset,
            })
            if r.status_code == 200:
                vid = r.json()["id"]
                self.verification_ids.append(vid)
                self._record(f"Submit: {asset['asset_name']}", True, f"id={vid[:8]}...")
            else:
                self._record(f"Submit: {asset['asset_name']}", False, f"HTTP {r.status_code}: {r.text[:100]}")

    def wait_for_processing(self):
        print(f"\n=== 4. WAITING FOR CELERY PROCESSING ({len(self.verification_ids)} tasks) ===")
        max_wait = 180  # 3 minutes
        start = time.time()

        while time.time() - start < max_wait:
            completed = 0
            failed = 0
            pending = 0
            errors = 0
            for vid in self.verification_ids:
                r = self.client.get(f"/verifications/{vid}", headers=self._headers())
                if r.status_code == 200:
                    s = r.json()["status"]
                    if s == "completed":
                        completed += 1
                    elif s == "failed":
                        failed += 1
                    else:
                        pending += 1
                else:
                    errors += 1

            elapsed = int(time.time() - start)
            extra = f" | HTTP errors: {errors}" if errors else ""
            print(f"  [{elapsed}s] Completed: {completed} | Failed: {failed} | Pending: {pending}{extra}")

            if pending == 0 and errors == 0:
                break
            time.sleep(8)

        self._record("All verifications processed", completed > 0 and pending == 0, f"{completed} completed, {failed} failed")

    def test_verification_results(self):
        print("\n=== 5. VERIFICATION RESULTS ===")

        for vid in self.verification_ids:
            r = self.client.get(f"/verifications/{vid}", headers=self._headers())
            if r.status_code == 200:
                v = r.json()
                has_proof = bool(v.get("proof_hash"))
                has_result = bool(v.get("result_data"))
                has_cert = bool(v.get("proof_certificate_url"))
                module = v["module"]
                status = v["status"]

                detail = f"{module} | proof={'Y' if has_proof else 'N'} | cert={'Y' if has_cert else 'N'}"
                if v.get("error_message"):
                    detail += f" | err={v['error_message'][:60]}"
                self._record(f"Result {vid[:8]}", status == "completed" and has_proof, detail)

    def test_stress_testing(self):
        print("\n=== 6. STRESS TESTING ===")

        # Get presets
        r = self.client.get("/stress-testing/presets", headers=self._headers())
        self._record("Get presets", r.status_code == 200)

        # Run stress test on first credit verification
        credit_vids = [v for v in self.verification_ids[:3]]
        if credit_vids:
            vid = credit_vids[0]
            r = self.client.post(f"/stress-testing/run/{vid}", headers=self._headers(), json={
                "scenario": "interest_rate_shock",
                "severity": "severe",
            })
            self._record("Interest rate shock", r.status_code == 200, f"HTTP {r.status_code}")

            r = self.client.post(f"/stress-testing/monte-carlo/{vid}", headers=self._headers(), json={
                "num_simulations": 500,
            })
            self._record("Monte Carlo (500 sims)", r.status_code == 200, f"HTTP {r.status_code}")

    def test_regulatory(self):
        print("\n=== 7. REGULATORY REPORTS ===")

        r = self.client.get("/regulatory/form-pf", headers=self._headers())
        self._record("Form PF report", r.status_code == 200)

        r = self.client.get("/regulatory/aifmd", headers=self._headers())
        self._record("AIFMD report", r.status_code == 200)

        r = self.client.post("/regulatory/narrative/form-pf", headers=self._headers(), json={})
        self._record("AI narrative (Form PF)", r.status_code == 200, f"HTTP {r.status_code}")

        r = self.client.post("/regulatory/narrative/aifmd", headers=self._headers(), json={})
        self._record("AI narrative (AIFMD)", r.status_code == 200, f"HTTP {r.status_code}")

    def test_analytics(self):
        print("\n=== 8. ANALYTICS & DASHBOARD ===")

        endpoints = [
            ("Overview", "/analytics/overview"),
            ("Verification trends", "/analytics/verification-trends"),
            ("Processing stats", "/analytics/processing-stats"),
            ("Portfolio performance", "/analytics/portfolio-performance"),
            ("Asset type breakdown", "/analytics/asset-type-breakdown"),
            ("Dashboard stats", "/dashboard/stats"),
            ("Recent activity", "/dashboard/recent-activity"),
        ]
        for name, path in endpoints:
            r = self.client.get(path, headers=self._headers())
            self._record(name, r.status_code == 200)

    def test_blockchain(self):
        print("\n=== 9. BLOCKCHAIN ===")

        r = self.client.get("/blockchain/anchors", headers=self._headers())
        self._record("List anchors", r.status_code == 200)

        if self.verification_ids:
            r = self.client.get(f"/verifications/{self.verification_ids[0]}", headers=self._headers())
            if r.status_code == 200:
                proof_hash = r.json().get("proof_hash", "")
                if proof_hash:
                    r2 = self.client.get(f"/blockchain/verify/{proof_hash}", headers=self._headers())
                    self._record("Verify proof on-chain", r2.status_code == 200, f"HTTP {r2.status_code}")

    def test_nl_query(self):
        print("\n=== 10. NATURAL LANGUAGE QUERY ===")

        queries = [
            "How many verifications were completed today?",
            "What is the total NAV across all portfolios?",
            "Show me verifications with high default rates",
        ]
        for q in queries:
            r = self.client.post("/nl-query", headers=self._headers(), json={"question": q})
            self._record(f'NL: "{q[:45]}..."', r.status_code == 200, f"HTTP {r.status_code}")

        r = self.client.get("/nl-query/suggestions", headers=self._headers())
        self._record("NL suggestions", r.status_code == 200)

    def test_model_registry(self):
        print("\n=== 11. MODEL REGISTRY ===")

        r = self.client.get("/model-registry/stats", headers=self._headers())
        self._record("Model stats", r.status_code == 200)

        if self.verification_ids:
            r = self.client.get(f"/model-registry/lineage/{self.verification_ids[0]}", headers=self._headers())
            self._record("Data lineage", r.status_code == 200)

    def test_schedules_notifications(self):
        print("\n=== 12. SCHEDULES & NOTIFICATIONS ===")

        r = self.client.get("/schedules", headers=self._headers())
        self._record("List schedules", r.status_code == 200)

        r = self.client.get("/schedules/alerts", headers=self._headers())
        self._record("List alerts", r.status_code == 200)

        r = self.client.get("/notifications", headers=self._headers())
        self._record("List notifications", r.status_code == 200)

        r = self.client.get("/notifications/unread", headers=self._headers())
        self._record("Unread count", r.status_code == 200)

    def test_org_and_billing(self):
        print("\n=== 13. ORGANIZATION & BILLING ===")

        r = self.client.get("/organizations/current", headers=self._headers())
        self._record("Get organization", r.status_code == 200)

        r = self.client.get("/organizations/current/members", headers=self._headers())
        self._record("List members", r.status_code == 200)

        r = self.client.get("/billing/current-plan", headers=self._headers())
        self._record("Current plan", r.status_code == 200)

    def test_audit(self):
        print("\n=== 14. AUDIT LOG ===")

        r = self.client.get("/audit/logs", headers=self._headers())
        self._record("Audit logs", r.status_code == 200)

        r = self.client.get("/audit/export", headers=self._headers())
        self._record("Audit export", r.status_code == 200)

    def print_summary(self):
        print("\n" + "=" * 70)
        print("  ZKValue E2E PRODUCTION TEST SUMMARY")
        print("=" * 70)
        passed = sum(1 for _, s, _ in self.results if s == "PASS")
        failed = sum(1 for _, s, _ in self.results if s == "FAIL")
        total = len(self.results)
        print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"  Pass rate: {passed/total*100:.1f}%")

        if failed:
            print(f"\n  FAILURES:")
            for name, status, detail in self.results:
                if status == "FAIL":
                    print(f"    - {name}: {detail}")

        print("=" * 70)
        return failed == 0

    def run_all(self):
        print("=" * 70)
        print("  ZKValue — E2E Production Test Suite")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.test_auth()
        self.test_credit_verifications()
        self.test_ai_ip_verifications()
        self.wait_for_processing()
        self.test_verification_results()
        self.test_stress_testing()
        self.test_regulatory()
        self.test_analytics()
        self.test_blockchain()
        self.test_nl_query()
        self.test_model_registry()
        self.test_schedules_notifications()
        self.test_org_and_billing()
        self.test_audit()

        return self.print_summary()


if __name__ == "__main__":
    runner = E2ETestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
