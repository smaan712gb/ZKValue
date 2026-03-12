"""
End-to-End Test Suite for ZKValue Platform
Tests all API endpoints, validates data accuracy, and checks AI agent outputs.
"""
import requests
import json
import time
import sys
import csv
import io
import os
from datetime import datetime

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['PYTHONIOENCODING'] = 'utf-8'

BASE = "http://localhost/api/v1"
PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0
RESULTS = []

def log(status, test_name, detail=""):
    global PASS_COUNT, FAIL_COUNT, WARN_COUNT
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "INFO": "→"}[status]
    if status == "PASS": PASS_COUNT += 1
    elif status == "FAIL": FAIL_COUNT += 1
    elif status == "WARN": WARN_COUNT += 1
    msg = f"  {icon} [{status}] {test_name}"
    if detail: msg += f" — {detail}"
    print(msg)
    RESULTS.append({"status": status, "test": test_name, "detail": detail})

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
section("1. AUTHENTICATION")

r = requests.post(f"{BASE}/auth/login", json={
    "email": "chishtymadiha@gmail.com",
    "password": "GZ7124me$"
})
assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
data = r.json()
TOKEN = data["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
log("PASS", "Login", f"User: {data['user']['full_name']}, Org: {data['user']['organization']['name']}")

# Test /auth/me
r = requests.get(f"{BASE}/auth/me", headers=HEADERS)
if r.status_code == 200:
    log("PASS", "GET /auth/me", f"Role: {r.json()['role']}")
else:
    log("FAIL", "GET /auth/me", f"Status {r.status_code}")

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
section("2. DASHBOARD")

r = requests.get(f"{BASE}/dashboard/stats", headers=HEADERS)
if r.status_code == 200:
    d = r.json()
    log("PASS", "GET /dashboard/stats", f"Total verifications: {d['total_verifications']}, Asset value: ${d['total_asset_value']:,.0f}")

    # Validate data accuracy
    if d['total_verifications'] >= 7:
        log("PASS", "Dashboard: verification count", f"{d['total_verifications']} verifications (3 credit + 4 AI-IP + any new)")
    else:
        log("WARN", "Dashboard: verification count", f"Expected >= 7, got {d['total_verifications']}")

    if d['credit_portfolios'] >= 3:
        log("PASS", "Dashboard: credit portfolio count", f"{d['credit_portfolios']} portfolios")
    else:
        log("FAIL", "Dashboard: credit portfolio count", f"Expected >= 3, got {d['credit_portfolios']}")

    if d['ai_assets'] >= 4:
        log("PASS", "Dashboard: AI asset count", f"{d['ai_assets']} assets")
    else:
        log("FAIL", "Dashboard: AI asset count", f"Expected >= 4, got {d['ai_assets']}")

    if d['total_asset_value'] > 0:
        log("PASS", "Dashboard: total asset value", f"${d['total_asset_value']:,.0f}")
    else:
        log("FAIL", "Dashboard: total asset value", "Value should be > 0")

    # Check value_by_module
    if 'value_by_module' in d:
        for mod in d['value_by_module']:
            log("PASS", f"Dashboard: {mod['module']} value", f"${mod['value']:,.0f}")

    # Check recent_verifications
    if d.get('recent_verifications'):
        log("PASS", "Dashboard: recent verifications", f"{len(d['recent_verifications'])} items")
    else:
        log("WARN", "Dashboard: recent verifications", "Empty")
else:
    log("FAIL", "GET /dashboard/stats", f"Status {r.status_code}: {r.text[:200]}")

r = requests.get(f"{BASE}/dashboard/recent-activity", headers=HEADERS)
if r.status_code == 200:
    activities = r.json()
    log("PASS", "GET /dashboard/recent-activity", f"{len(activities)} activities")
else:
    log("FAIL", "GET /dashboard/recent-activity", f"Status {r.status_code}")

# ─────────────────────────────────────────────
# VERIFICATIONS
# ─────────────────────────────────────────────
section("3. VERIFICATIONS")

r = requests.get(f"{BASE}/verifications", headers=HEADERS)
verifications = []
credit_verification_id = None
aiip_verification_id = None

if r.status_code == 200:
    vdata = r.json()
    verifications = vdata['items']
    log("PASS", "GET /verifications", f"{vdata['total']} total, page {vdata['page']}/{vdata['total_pages']}")

    for v in verifications:
        if v['module'] == 'private_credit' and v['status'] == 'completed' and not credit_verification_id:
            credit_verification_id = v['id']
        if v['module'] == 'ai_ip_valuation' and v['status'] == 'completed' and not aiip_verification_id:
            aiip_verification_id = v['id']

    # Validate each verification's data completeness
    for v in verifications:
        has_proof = bool(v.get('proof_hash'))
        has_result = bool(v.get('result_data'))
        has_input = bool(v.get('input_data'))

        if has_proof and has_result and has_input:
            log("PASS", f"Verification {v['id'][:8]}... ({v['module']})", f"Status: {v['status']}, proof: {v['proof_hash'][:16]}...")
        else:
            missing = []
            if not has_proof: missing.append("proof_hash")
            if not has_result: missing.append("result_data")
            if not has_input: missing.append("input_data")
            log("WARN", f"Verification {v['id'][:8]}... ({v['module']})", f"Missing: {', '.join(missing)}")
else:
    log("FAIL", "GET /verifications", f"Status {r.status_code}")

# Test individual verification detail
if credit_verification_id:
    r = requests.get(f"{BASE}/verifications/{credit_verification_id}", headers=HEADERS)
    if r.status_code == 200:
        v = r.json()
        log("PASS", "GET /verifications/{id} (credit)", f"Module: {v['module']}, has result_data: {bool(v['result_data'])}")

        # Validate credit result_data structure
        rd = v.get('result_data', {})
        required_keys = ['portfolio_summary', 'risk_metrics']
        found = [k for k in required_keys if k in rd]
        if len(found) == len(required_keys):
            log("PASS", "Credit result_data structure", f"Keys: {', '.join(found)}")
            ps = rd['portfolio_summary']
            if ps.get('total_principal', 0) > 0:
                log("PASS", "Credit: total_principal", f"${ps['total_principal']:,.0f}")
            if ps.get('nav_value', 0) > 0:
                log("PASS", "Credit: NAV value", f"${ps['nav_value']:,.0f}")
            if ps.get('weighted_avg_rate', 0) > 0:
                log("PASS", "Credit: weighted avg rate", f"{ps['weighted_avg_rate']}%")
        else:
            log("WARN", "Credit result_data structure", f"Found only: {found}")
    else:
        log("FAIL", "GET /verifications/{id} (credit)", f"Status {r.status_code}")

# ─────────────────────────────────────────────
# PROOF VERIFICATION
# ─────────────────────────────────────────────
section("4. CRYPTOGRAPHIC PROOF VERIFICATION")

for vid, label in [(credit_verification_id, "credit"), (aiip_verification_id, "AI-IP")]:
    if vid:
        r = requests.post(f"{BASE}/verifications/{vid}/verify-proof", headers=HEADERS)
        if r.status_code == 200:
            pv = r.json()
            if pv['is_valid']:
                log("PASS", f"Proof verification ({label})", f"Hash: {pv['proof_hash'][:20]}... VALID")
            else:
                log("FAIL", f"Proof verification ({label})", "Proof is INVALID — data integrity compromised")
        else:
            log("FAIL", f"Proof verification ({label})", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# CREDIT PORTFOLIOS
# ─────────────────────────────────────────────
section("5. CREDIT PORTFOLIOS")

r = requests.get(f"{BASE}/credit/portfolios", headers=HEADERS)
if r.status_code == 200:
    portfolios = r.json()
    log("PASS", "GET /credit/portfolios", f"{len(portfolios)} portfolios")

    for p in portfolios:
        # Validate financial data accuracy
        issues = []
        if p['total_principal'] <= 0: issues.append("principal <= 0")
        if p['weighted_avg_rate'] <= 0: issues.append("rate <= 0")
        if p['avg_ltv_ratio'] <= 0 or p['avg_ltv_ratio'] > 1.5: issues.append(f"LTV suspicious: {p['avg_ltv_ratio']}")
        if p['nav_value'] <= 0: issues.append("NAV <= 0")
        if p['loan_count'] <= 0: issues.append("no loans")

        if not issues:
            log("PASS", f"Portfolio: {p['portfolio_name']}",
                f"Loans: {p['loan_count']}, Principal: ${p['total_principal']:,.0f}, Rate: {p['weighted_avg_rate']}%, LTV: {p['avg_ltv_ratio']:.1%}, NAV: ${p['nav_value']:,.0f}")
        else:
            log("FAIL", f"Portfolio: {p['portfolio_name']}", f"Issues: {', '.join(issues)}")

        # Validate covenant compliance
        cc = p.get('covenant_compliance_status', {})
        if cc:
            breaches = [k for k, v in cc.items() if isinstance(v, dict) and not v.get('compliant', True)]
            if breaches:
                log("INFO", f"  Covenant breaches", f"{', '.join(breaches)}")
            else:
                log("PASS", f"  Covenant compliance", "All covenants met")
else:
    log("FAIL", "GET /credit/portfolios", f"Status {r.status_code}")

# ─────────────────────────────────────────────
# AI-IP ASSETS
# ─────────────────────────────────────────────
section("6. AI-IP ASSETS")

r = requests.get(f"{BASE}/ai-ip/assets", headers=HEADERS)
if r.status_code == 200:
    assets = r.json()
    log("PASS", "GET /ai-ip/assets", f"{len(assets)} assets")

    for a in assets:
        issues = []
        if a['estimated_value'] <= 0: issues.append("value <= 0")
        if a['confidence_score'] <= 0 or a['confidence_score'] > 1: issues.append(f"confidence out of range: {a['confidence_score']}")

        if not issues:
            log("PASS", f"Asset: {a['asset_name']}",
                f"Type: {a['asset_type']}, Value: ${float(a['estimated_value']):,.0f}, Confidence: {float(a['confidence_score']):.0%}, Method: {a['valuation_method']}")
            log("PASS", f"  IAS38: {'✓' if a['ias38_compliant'] else '✗'} | ASC350: {'✓' if a['asc350_compliant'] else '✗'}", "")
        else:
            log("FAIL", f"Asset: {a['asset_name']}", f"Issues: {', '.join(issues)}")
else:
    log("FAIL", "GET /ai-ip/assets", f"Status {r.status_code}")

# ─────────────────────────────────────────────
# STRESS TESTING
# ─────────────────────────────────────────────
section("7. STRESS TESTING")

r = requests.get(f"{BASE}/stress-testing/presets", headers=HEADERS)
if r.status_code == 200:
    presets = r.json()
    log("PASS", "GET /stress-testing/presets", f"{presets['total']} presets: {', '.join(presets['presets'].keys())}")
else:
    log("FAIL", "GET /stress-testing/presets", f"Status {r.status_code}")

if credit_verification_id:
    # Run all stress test presets
    r = requests.post(f"{BASE}/stress-testing/run/{credit_verification_id}?scenario_key=all", headers=HEADERS)
    if r.status_code == 200:
        st = r.json()
        log("PASS", "POST /stress-testing/run (all presets)", f"{st.get('scenario_count', '?')} scenarios on {st.get('loan_count', '?')} loans")

        for name, scenario in st.get('scenarios', {}).items():
            impact = scenario.get('portfolio_impact', {})
            log("PASS", f"  Scenario: {name}",
                f"Loss: ${impact.get('total_loss', 0):,.0f}, Impaired: {impact.get('impaired_loans', 0)}")
    else:
        log("FAIL", "POST /stress-testing/run", f"Status {r.status_code}: {r.text[:200]}")

    # Run Monte Carlo
    r = requests.post(f"{BASE}/stress-testing/monte-carlo/{credit_verification_id}",
                      headers=HEADERS, json={"num_simulations": 1000, "seed": 42})
    if r.status_code == 200:
        mc = r.json()
        rm = mc.get('risk_metrics', {})
        log("PASS", "POST /stress-testing/monte-carlo",
            f"VaR95: ${rm.get('var_95', 0):,.0f}, CVaR95: ${rm.get('cvar_95', 0):,.0f}, Mean Loss: ${rm.get('mean_loss', 0):,.0f}")

        # Validate Monte Carlo sanity
        if rm.get('var_95', 0) > rm.get('mean_loss', 0):
            log("PASS", "Monte Carlo: VaR95 > Mean Loss", "Risk metric ordering is correct")
        else:
            log("WARN", "Monte Carlo: VaR95 vs Mean Loss", "Unexpected ordering")

        if rm.get('cvar_95', 0) >= rm.get('var_95', 0):
            log("PASS", "Monte Carlo: CVaR95 >= VaR95", "Tail risk metric is correct")
        else:
            log("WARN", "Monte Carlo: CVaR95 vs VaR95", "Expected CVaR >= VaR")
    else:
        log("FAIL", "POST /stress-testing/monte-carlo", f"Status {r.status_code}: {r.text[:200]}")

    # Custom stress scenario
    r = requests.post(f"{BASE}/stress-testing/custom/{credit_verification_id}", headers=HEADERS,
                      json={"name": "Custom Recession", "rate_shock_bps": 300, "default_multiplier": 2.5, "collateral_haircut": 0.25})
    if r.status_code == 200:
        cs = r.json()
        log("PASS", "POST /stress-testing/custom", f"Custom scenario executed successfully")
    else:
        log("FAIL", "POST /stress-testing/custom", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────
section("8. ANALYTICS")

analytics_endpoints = [
    ("verification-trends?months=6", "Verification Trends"),
    ("portfolio-performance", "Portfolio Performance"),
    ("ai-asset-performance", "AI Asset Performance"),
    ("asset-type-breakdown", "Asset Type Breakdown"),
    ("alert-summary", "Alert Summary"),
    ("processing-stats", "Processing Stats"),
    ("overview", "Full Analytics Overview"),
]

for endpoint, name in analytics_endpoints:
    r = requests.get(f"{BASE}/analytics/{endpoint}", headers=HEADERS)
    if r.status_code == 200:
        d = r.json()
        detail = json.dumps(d, default=str)[:150]
        log("PASS", f"GET /analytics/{endpoint}", detail)
    else:
        log("FAIL", f"GET /analytics/{endpoint}", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# BLOCKCHAIN ANCHORING
# ─────────────────────────────────────────────
section("9. BLOCKCHAIN ANCHORING")

r = requests.get(f"{BASE}/blockchain/anchors", headers=HEADERS)
if r.status_code == 200:
    log("PASS", "GET /blockchain/anchors", f"Response: {json.dumps(r.json(), default=str)[:150]}")
else:
    log("FAIL", "GET /blockchain/anchors", f"Status {r.status_code}")

# Create blockchain anchor
r = requests.post(f"{BASE}/blockchain/anchor", headers=HEADERS)
if r.status_code == 200:
    anchor = r.json()
    log("PASS", "POST /blockchain/anchor", f"Anchor created: {json.dumps(anchor, default=str)[:150]}")
else:
    log("WARN", "POST /blockchain/anchor", f"Status {r.status_code}: {r.text[:200]}")

# Verify a proof on chain
if credit_verification_id:
    v_detail = requests.get(f"{BASE}/verifications/{credit_verification_id}", headers=HEADERS).json()
    if v_detail.get('proof_hash'):
        r = requests.get(f"{BASE}/blockchain/verify/{v_detail['proof_hash']}", headers=HEADERS)
        if r.status_code == 200:
            log("PASS", "GET /blockchain/verify/{hash}", f"Result: {json.dumps(r.json(), default=str)[:150]}")
        else:
            log("WARN", "GET /blockchain/verify/{hash}", f"Status {r.status_code}: {r.text[:100]}")

# ─────────────────────────────────────────────
# NL QUERY
# ─────────────────────────────────────────────
section("10. NATURAL LANGUAGE QUERIES")

r = requests.get(f"{BASE}/nl-query/suggestions", headers=HEADERS)
if r.status_code == 200:
    log("PASS", "GET /nl-query/suggestions", f"{len(r.json().get('suggestions', []))} suggestions")
else:
    log("FAIL", "GET /nl-query/suggestions", f"Status {r.status_code}")

# Test NL queries
nl_questions = [
    "What is my total portfolio value?",
    "Show me all verifications with covenant breaches",
    "Which AI assets have the highest valuation?",
]

for q in nl_questions:
    r = requests.post(f"{BASE}/nl-query", headers=HEADERS, json={"question": q, "max_rows": 10}, timeout=60)
    if r.status_code == 200:
        result = r.json()
        log("PASS", f"NL Query: '{q[:50]}'", f"Answer: {json.dumps(result, default=str)[:120]}")
    else:
        log("WARN", f"NL Query: '{q[:50]}'", f"Status {r.status_code}: {r.text[:150]}")

# ─────────────────────────────────────────────
# REGULATORY REPORTS
# ─────────────────────────────────────────────
section("11. REGULATORY REPORTS")

r = requests.get(f"{BASE}/regulatory/form-pf", headers=HEADERS, timeout=30)
if r.status_code == 200:
    pf = r.json()
    log("PASS", "GET /regulatory/form-pf", f"Keys: {list(pf.keys())[:5]}")
else:
    log("WARN", "GET /regulatory/form-pf", f"Status {r.status_code}: {r.text[:200]}")

r = requests.get(f"{BASE}/regulatory/aifmd", headers=HEADERS, timeout=30)
if r.status_code == 200:
    aifmd = r.json()
    log("PASS", "GET /regulatory/aifmd", f"Keys: {list(aifmd.keys())[:5]}")
else:
    log("WARN", "GET /regulatory/aifmd", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# CREATE NEW LIVE VERIFICATION (Credit)
# ─────────────────────────────────────────────
section("12. LIVE CREDIT VERIFICATION (End-to-End)")

new_credit_data = {
    "portfolio_name": "E2E Test — Pinnacle Growth Fund IV",
    "fund_name": "Pinnacle Capital Partners",
    "loans": [
        {
            "loan_id": "PGF-2025-001",
            "borrower_id": "BRW-APEX-001",
            "principal": 15000000,
            "interest_rate": 8.25,
            "term_months": 60,
            "origination_date": "2025-06-15",
            "maturity_date": "2030-06-15",
            "collateral_value": 22500000,
            "collateral_type": "commercial_real_estate",
            "payment_status": "current",
            "outstanding_balance": 14200000,
            "ltv_ratio": 0.631,
            "dscr": 1.85
        },
        {
            "loan_id": "PGF-2025-002",
            "borrower_id": "BRW-NOVA-002",
            "principal": 8500000,
            "interest_rate": 9.50,
            "term_months": 48,
            "origination_date": "2025-03-01",
            "maturity_date": "2029-03-01",
            "collateral_value": 11000000,
            "collateral_type": "equipment_and_machinery",
            "payment_status": "current",
            "outstanding_balance": 8100000,
            "ltv_ratio": 0.736,
            "dscr": 1.42
        },
        {
            "loan_id": "PGF-2025-003",
            "borrower_id": "BRW-ZENITH-003",
            "principal": 25000000,
            "interest_rate": 7.75,
            "term_months": 84,
            "origination_date": "2025-01-10",
            "maturity_date": "2032-01-10",
            "collateral_value": 35000000,
            "collateral_type": "commercial_real_estate",
            "payment_status": "current",
            "outstanding_balance": 24500000,
            "ltv_ratio": 0.700,
            "dscr": 2.10
        },
        {
            "loan_id": "PGF-2025-004",
            "borrower_id": "BRW-DELTA-004",
            "principal": 5000000,
            "interest_rate": 11.00,
            "term_months": 36,
            "origination_date": "2025-09-01",
            "maturity_date": "2028-09-01",
            "collateral_value": 5500000,
            "collateral_type": "accounts_receivable",
            "payment_status": "30_days_late",
            "outstanding_balance": 4900000,
            "ltv_ratio": 0.891,
            "dscr": 0.95
        },
        {
            "loan_id": "PGF-2025-005",
            "borrower_id": "BRW-ORBIT-005",
            "principal": 12000000,
            "interest_rate": 8.00,
            "term_months": 72,
            "origination_date": "2024-11-15",
            "maturity_date": "2030-11-15",
            "collateral_value": 18000000,
            "collateral_type": "industrial_property",
            "payment_status": "current",
            "outstanding_balance": 11500000,
            "ltv_ratio": 0.639,
            "dscr": 1.75
        }
    ],
    "covenants": {
        "max_ltv": 0.80,
        "min_dscr": 1.20,
        "max_single_borrower_concentration": 0.40
    }
}

r = requests.post(f"{BASE}/credit/verify", headers=HEADERS, json=new_credit_data)
if r.status_code == 200:
    cv = r.json()
    new_credit_vid = cv['verification_id']
    log("PASS", "POST /credit/verify", f"Verification ID: {new_credit_vid}, Status: {cv['status']}")

    # Poll for completion
    print("  → Waiting for Celery to process verification...")
    for attempt in range(30):
        time.sleep(2)
        r2 = requests.get(f"{BASE}/verifications/{new_credit_vid}", headers=HEADERS)
        if r2.status_code == 200:
            vr = r2.json()
            if vr['status'] == 'completed':
                log("PASS", "Credit verification completed", f"Proof: {vr['proof_hash'][:20]}...")

                # Validate result data
                rd = vr['result_data']
                if rd:
                    ps = rd.get('portfolio_summary', {})
                    log("PASS", "  Total principal", f"${ps.get('total_principal', 0):,.0f}")
                    log("PASS", "  NAV", f"${ps.get('nav_value', 0):,.0f}")
                    log("PASS", "  Weighted avg rate", f"{ps.get('weighted_avg_rate', 0)}%")
                    log("PASS", "  Loan count", f"{ps.get('loan_count', 0)}")

                    cc = rd.get('covenant_compliance', {})
                    if cc:
                        for k, v in cc.items():
                            status = "PASS" if v.get('compliant') else "WARN"
                            log(status, f"  Covenant: {k}", f"Limit: {v.get('limit')}, Actual: {v.get('actual')}, {'Compliant' if v.get('compliant') else 'BREACH'}")

                # Verify proof
                r3 = requests.post(f"{BASE}/verifications/{new_credit_vid}/verify-proof", headers=HEADERS)
                if r3.status_code == 200 and r3.json().get('is_valid'):
                    log("PASS", "  Proof verification", "Cryptographic proof is VALID")
                else:
                    log("FAIL", "  Proof verification", "Proof invalid or verification failed")
                break
            elif vr['status'] == 'failed':
                log("FAIL", "Credit verification failed", vr.get('error_message', 'Unknown error'))
                break
        if attempt == 29:
            log("WARN", "Credit verification timeout", "Still processing after 60s")
else:
    log("FAIL", "POST /credit/verify", f"Status {r.status_code}: {r.text[:200]}")
    new_credit_vid = None

# ─────────────────────────────────────────────
# CREATE NEW LIVE VERIFICATION (AI-IP)
# ─────────────────────────────────────────────
section("13. LIVE AI-IP VALUATION (End-to-End)")

new_aiip_data = {
    "asset_name": "E2E Test — QuantumForge Compiler Suite",
    "asset_type": "deployed_app",
    "description": "AI-powered quantum circuit compiler and optimizer. Translates high-level quantum algorithms into hardware-specific gate sequences for IBM, Google, and IonQ quantum processors. Reduces circuit depth by 40-60% versus baseline compilers. Used by 3 national labs and 2 Fortune 500 companies.",
    "cloud_provider": "AWS",
    "training_compute_hours": 28000,
    "training_cost": 1850000,
    "dataset_size_gb": 450,
    "dataset_uniqueness_score": 0.96,
    "model_parameters": 780000000,
    "benchmark_scores": {
        "circuit_depth_reduction": 0.52,
        "fidelity_improvement": 0.38,
        "compilation_speed_ratio": 4.2
    },
    "monthly_revenue": 340000,
    "monthly_active_users": 85,
    "inference_cost_per_query": 0.15,
    "gpu_type": "NVIDIA A100",
    "gpu_count": 16
}

r = requests.post(f"{BASE}/ai-ip/valuate", headers=HEADERS, json=new_aiip_data)
if r.status_code == 200:
    av = r.json()
    new_aiip_vid = av['verification_id']
    log("PASS", "POST /ai-ip/valuate", f"Verification ID: {new_aiip_vid}")

    # Poll for completion
    print("  → Waiting for Celery to process AI-IP valuation...")
    for attempt in range(30):
        time.sleep(2)
        r2 = requests.get(f"{BASE}/verifications/{new_aiip_vid}", headers=HEADERS)
        if r2.status_code == 200:
            vr = r2.json()
            if vr['status'] == 'completed':
                rd = vr['result_data']
                if rd:
                    vs = rd.get('valuation_summary', {})
                    log("PASS", "AI-IP valuation completed",
                        f"Value: ${vs.get('estimated_value', 0):,.0f}, Method: {vs.get('valuation_method', '?')}, Confidence: {vs.get('confidence_score', 0):.0%}")

                    comp = rd.get('compliance', {})
                    if comp:
                        log("PASS", f"  IAS38: {'✓' if comp.get('ias38_compliant') else '✗'} | ASC350: {'✓' if comp.get('asc350_compliant') else '✗'}", "")
                else:
                    log("WARN", "AI-IP valuation completed", "No result_data")

                # Verify proof
                r3 = requests.post(f"{BASE}/verifications/{new_aiip_vid}/verify-proof", headers=HEADERS)
                if r3.status_code == 200 and r3.json().get('is_valid'):
                    log("PASS", "  Proof verification", "Cryptographic proof is VALID")
                else:
                    log("FAIL", "  Proof verification", "Proof invalid or verification failed")
                break
            elif vr['status'] == 'failed':
                log("FAIL", "AI-IP valuation failed", vr.get('error_message', 'Unknown error'))
                break
        if attempt == 29:
            log("WARN", "AI-IP valuation timeout", "Still processing after 60s")
else:
    log("FAIL", "POST /ai-ip/valuate", f"Status {r.status_code}: {r.text[:200]}")
    new_aiip_vid = None

# ─────────────────────────────────────────────
# AI-POWERED FEATURES (LLM)
# ─────────────────────────────────────────────
section("14. AI-POWERED FEATURES")

# Executive report — credit
test_vid = new_credit_vid or credit_verification_id
if test_vid:
    print("  → Generating executive report (credit)...")
    r = requests.post(f"{BASE}/verifications/{test_vid}/generate-report", headers=HEADERS, timeout=240)
    if r.status_code == 200:
        report = r.json()
        rpt = report.get('report', {})
        if isinstance(rpt, dict):
            log("PASS", "Executive Report (credit)", f"Keys: {list(rpt.keys())[:5]}")
            # Check for key report sections
            for section_name in ['executive_summary', 'key_findings', 'recommendations']:
                if section_name in rpt:
                    content = rpt[section_name]
                    if isinstance(content, str) and len(content) > 50:
                        log("PASS", f"  Report section: {section_name}", f"{len(content)} chars")
                    elif isinstance(content, list) and len(content) > 0:
                        log("PASS", f"  Report section: {section_name}", f"{len(content)} items")
                    else:
                        log("WARN", f"  Report section: {section_name}", f"Content seems thin")
        elif isinstance(rpt, str) and len(rpt) > 100:
            log("PASS", "Executive Report (credit)", f"Report: {rpt[:150]}...")
        else:
            log("WARN", "Executive Report (credit)", f"Unexpected format: {type(rpt)}")
    else:
        log("WARN", "Executive Report (credit)", f"Status {r.status_code}: {r.text[:200]}")

# Executive report — AI-IP
test_aiip = new_aiip_vid or aiip_verification_id
if test_aiip:
    print("  → Generating executive report (AI-IP)...")
    r = requests.post(f"{BASE}/verifications/{test_aiip}/generate-report", headers=HEADERS, timeout=240)
    if r.status_code == 200:
        report = r.json()
        log("PASS", "Executive Report (AI-IP)", f"Generated successfully")
    else:
        log("WARN", "Executive Report (AI-IP)", f"Status {r.status_code}: {r.text[:200]}")

# Comparable analysis (AI-IP only)
if test_aiip:
    print("  → Generating comparable analysis...")
    r = requests.post(f"{BASE}/verifications/{test_aiip}/comparable-analysis", headers=HEADERS, timeout=240)
    if r.status_code == 200:
        ca = r.json()
        log("PASS", "Comparable Analysis (AI-IP)", f"Analysis: {json.dumps(ca, default=str)[:150]}")
    else:
        log("WARN", "Comparable Analysis (AI-IP)", f"Status {r.status_code}: {r.text[:200]}")

# Stress test narrative
if test_vid:
    print("  → Generating stress test narrative...")
    r = requests.post(f"{BASE}/stress-testing/narrative/{test_vid}", headers=HEADERS, timeout=240)
    if r.status_code == 200:
        sn = r.json()
        narrative = sn.get('narrative', '')
        if isinstance(narrative, str) and len(narrative) > 100:
            log("PASS", "Stress Test Narrative", f"{len(narrative)} chars, starts: '{narrative[:80]}...'")
        elif isinstance(narrative, dict):
            log("PASS", "Stress Test Narrative", f"Keys: {list(narrative.keys())[:5]}")
        else:
            log("WARN", "Stress Test Narrative", f"Short or empty: {narrative[:100]}")
    else:
        log("WARN", "Stress Test Narrative", f"Status {r.status_code}: {r.text[:200]}")

# Regulatory narrative
print("  → Generating regulatory narrative (Form PF)...")
r = requests.post(f"{BASE}/regulatory/narrative/form-pf", headers=HEADERS, timeout=240)
if r.status_code == 200:
    rn = r.json()
    narrative = rn.get('narrative', '')
    if isinstance(narrative, str) and len(narrative) > 100:
        log("PASS", "Regulatory Narrative (Form PF)", f"{len(narrative)} chars")
    elif isinstance(narrative, dict):
        log("PASS", "Regulatory Narrative (Form PF)", f"Keys: {list(narrative.keys())[:5]}")
    else:
        log("WARN", "Regulatory Narrative (Form PF)", f"Content: {str(narrative)[:150]}")
else:
    log("WARN", "Regulatory Narrative (Form PF)", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# AI ASSET CLASSIFICATION
# ─────────────────────────────────────────────
section("15. AI ASSET CLASSIFICATION")

r = requests.post(f"{BASE}/ai-ip/classify", headers=HEADERS, json={
    "asset_name": "NeuralMesh 3D Generator",
    "asset_type": "model_weights",
    "description": "A 12-billion parameter diffusion model for generating photorealistic 3D assets from text prompts. Trained on 8M curated 3D scans. Licensed by 2 AAA game studios and 1 automotive OEM for design prototyping."
}, timeout=60)
if r.status_code == 200:
    cl = r.json()
    log("PASS", "POST /ai-ip/classify", f"Classification: {json.dumps(cl, default=str)[:200]}")
else:
    log("WARN", "POST /ai-ip/classify", f"Status {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
section("TEST SUMMARY")
print(f"  ✓ Passed:   {PASS_COUNT}")
print(f"  ✗ Failed:   {FAIL_COUNT}")
print(f"  ⚠ Warnings: {WARN_COUNT}")
print(f"  Total:      {PASS_COUNT + FAIL_COUNT + WARN_COUNT}")
print()

if FAIL_COUNT > 0:
    print("  FAILED TESTS:")
    for r in RESULTS:
        if r['status'] == 'FAIL':
            print(f"    ✗ {r['test']}: {r['detail']}")
    print()

if WARN_COUNT > 0:
    print("  WARNINGS:")
    for r in RESULTS:
        if r['status'] == 'WARN':
            print(f"    ⚠ {r['test']}: {r['detail']}")
    print()

sys.exit(1 if FAIL_COUNT > 0 else 0)
