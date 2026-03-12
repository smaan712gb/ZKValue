from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime


class AssetTypeEnum(str, Enum):
    training_data = "training_data"
    model_weights = "model_weights"
    inference_infra = "inference_infra"
    deployed_app = "deployed_app"


class VerificationCreate(BaseModel):
    module: Literal["private_credit", "ai_ip_valuation"]
    input_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class VerificationResponse(BaseModel):
    id: str
    organization_id: str
    created_by: str
    module: str
    status: str
    input_data: Dict[str, Any]
    result_data: Optional[Dict[str, Any]] = None
    proof_hash: Optional[str] = None
    proof_certificate_url: Optional[str] = None
    report_url: Optional[str] = None
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CreditVerificationInput(BaseModel):
    portfolio_name: str
    fund_name: str
    loans: List[Dict[str, Any]]
    covenants: Optional[Dict[str, Any]] = None


class LoanEntry(BaseModel):
    loan_id: str
    borrower_id: str
    principal: float
    interest_rate: float
    term_months: int
    origination_date: str
    maturity_date: str
    collateral_value: float
    collateral_type: str
    payment_status: str
    outstanding_balance: float
    ltv_ratio: Optional[float] = None
    dscr: Optional[float] = None


class AIIPValuationInput(BaseModel):
    asset_name: str
    asset_type: AssetTypeEnum
    description: str
    cloud_provider: Optional[str] = None
    training_compute_hours: Optional[float] = None
    training_cost: Optional[float] = None
    dataset_size_gb: Optional[float] = None
    dataset_uniqueness_score: Optional[float] = None
    model_parameters: Optional[int] = None
    benchmark_scores: Optional[Dict[str, float]] = None
    monthly_revenue: Optional[float] = None
    monthly_active_users: Optional[int] = None
    inference_cost_per_query: Optional[float] = None
    gpu_type: Optional[str] = None
    gpu_count: Optional[int] = None


class ProofCertificate(BaseModel):
    verification_id: str
    algorithm: str
    inputs_hash: str
    outputs_hash: str
    computation_hash: str
    proof_hash: str
    timestamp: datetime
    block_attestation: Optional[str] = None


class CreditPortfolioResponse(BaseModel):
    id: str
    organization_id: str
    verification_id: str
    portfolio_name: str
    fund_name: str
    loan_count: int
    total_principal: float
    weighted_avg_rate: float
    avg_ltv_ratio: float
    nav_value: float
    covenant_compliance_status: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AIAssetResponse(BaseModel):
    id: str
    organization_id: str
    verification_id: str
    asset_type: str
    asset_name: str
    description: Optional[str] = None
    valuation_method: str
    estimated_value: float
    confidence_score: float
    valuation_inputs: Dict[str, Any]
    valuation_breakdown: Dict[str, Any]
    ias38_compliant: bool
    asc350_compliant: bool
    created_at: datetime

    model_config = {"from_attributes": True}
