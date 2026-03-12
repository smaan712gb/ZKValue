from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.verification import Verification
from app.api.deps import get_current_user
from app.services.llm.service import LLMService
from app.services.stress_testing.engine import StressTestEngine, SCENARIO_PRESETS

router = APIRouter(prefix="/stress-testing", tags=["Stress Testing"])


class CustomScenario(BaseModel):
    name: str = "Custom Scenario"
    rate_shock_bps: int = Field(0, ge=-500, le=1000)
    default_multiplier: float = Field(1.0, ge=0.1, le=10.0)
    collateral_haircut: float = Field(0.0, ge=0.0, le=0.80)
    description: str = ""


class MonteCarloRequest(BaseModel):
    num_simulations: int = Field(1000, ge=100, le=10000)
    seed: Optional[int] = None


@router.get("/presets")
async def list_scenario_presets():
    """List all available stress test scenario presets."""
    return {
        "presets": {k: {**v} for k, v in SCENARIO_PRESETS.items()},
        "total": len(SCENARIO_PRESETS),
    }


@router.post("/run/{verification_id}")
async def run_stress_test(
    verification_id: str,
    scenario_key: str = Query("all", description="Preset key or 'all'"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run predefined stress scenarios on a completed credit verification."""
    v = await _get_credit_verification(verification_id, user, db)
    loans = v.input_data.get("loans", [])
    if not loans:
        raise HTTPException(status_code=400, detail="No loan data in this verification")

    llm_service = LLMService(db)
    engine = StressTestEngine(llm_service)

    if scenario_key == "all":
        results = engine.run_all_presets(loans)
    elif scenario_key in SCENARIO_PRESETS:
        result = engine.run_scenario(loans, SCENARIO_PRESETS[scenario_key])
        results = {"scenarios": {scenario_key: result}, "scenario_count": 1, "loan_count": len(loans)}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario: {scenario_key}. Use 'all' or one of: {list(SCENARIO_PRESETS.keys())}")

    return {
        "verification_id": verification_id,
        **results,
    }


@router.post("/custom/{verification_id}")
async def run_custom_scenario(
    verification_id: str,
    scenario: CustomScenario,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a custom stress scenario with user-defined parameters."""
    v = await _get_credit_verification(verification_id, user, db)
    loans = v.input_data.get("loans", [])
    if not loans:
        raise HTTPException(status_code=400, detail="No loan data in this verification")

    llm_service = LLMService(db)
    engine = StressTestEngine(llm_service)
    result = engine.run_scenario(loans, scenario.model_dump())

    return {
        "verification_id": verification_id,
        "result": result,
    }


@router.post("/monte-carlo/{verification_id}")
async def run_monte_carlo(
    verification_id: str,
    params: MonteCarloRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run Monte Carlo simulation on a credit portfolio."""
    v = await _get_credit_verification(verification_id, user, db)
    loans = v.input_data.get("loans", [])
    if not loans:
        raise HTTPException(status_code=400, detail="No loan data in this verification")

    llm_service = LLMService(db)
    engine = StressTestEngine(llm_service)
    results = engine.run_monte_carlo(loans, params.num_simulations, params.seed)

    return {
        "verification_id": verification_id,
        **results,
    }


@router.post("/narrative/{verification_id}")
async def generate_stress_narrative(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an LLM-powered narrative analysis of stress test results."""
    v = await _get_credit_verification(verification_id, user, db)
    loans = v.input_data.get("loans", [])
    if not loans:
        raise HTTPException(status_code=400, detail="No loan data in this verification")

    llm_service = LLMService(db)
    engine = StressTestEngine(llm_service)

    # Run all presets + Monte Carlo
    preset_results = engine.run_all_presets(loans)
    mc_results = engine.run_monte_carlo(loans, 1000)

    combined = {
        "scenario_results": preset_results,
        "monte_carlo": mc_results,
        "portfolio_summary": {
            "loan_count": len(loans),
            "total_outstanding": sum(float(l.get("outstanding_balance", l.get("principal", 0))) for l in loans),
        },
    }

    narrative = await engine.generate_stress_narrative(user.organization_id, combined)

    return {
        "verification_id": verification_id,
        "narrative": narrative,
        "scenario_results": preset_results,
        "monte_carlo_summary": mc_results["risk_metrics"],
    }


async def _get_credit_verification(verification_id: str, user: User, db: AsyncSession) -> Verification:
    """Helper to fetch and validate a credit verification."""
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.organization_id == user.organization_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")
    if v.module.value != "private_credit":
        raise HTTPException(status_code=400, detail="Stress testing is only available for private credit verifications")
    return v
