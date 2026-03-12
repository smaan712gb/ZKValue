import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification
from app.models.ai_asset import AIAsset, AssetType, ValuationMethod
from app.services.llm.service import LLMService
from app.services.valuation.market_comparables import MarketComparablesService

logger = logging.getLogger(__name__)

# Market benchmarks for comparable analysis
COMPUTE_COST_PER_GPU_HOUR = {
    "H100": 3.50,
    "A100": 2.00,
    "V100": 0.80,
    "default": 1.50,
}

DATA_UNIQUENESS_MULTIPLIER = {
    "public": 1.0,
    "curated": 2.5,
    "proprietary": 5.0,
    "exclusive": 10.0,
}

REVENUE_MULTIPLE_BY_STAGE = {
    "pre_revenue": 0,
    "early": 15,
    "growth": 12,
    "mature": 8,
}


class AIIPValuationService:
    def __init__(self, session: AsyncSession, llm_service: LLMService):
        self.session = session
        self.llm_service = llm_service
        self.market_comparables = MarketComparablesService(llm_service)

    async def process_verification(self, verification: Verification) -> Dict[str, Any]:
        """Process a full AI-IP valuation verification."""
        input_data = verification.input_data
        org_id = verification.organization_id

        # Step 1: Classify the asset using LLM
        classification = await self.llm_service.classify_asset(
            org_id, input_data.get("description", "")
        )

        # Step 2: Calculate valuation based on asset type
        asset_type = classification.get("asset_type", input_data.get("asset_type", "model_weights"))
        valuation_method = classification.get("valuation_method", "cost_approach")

        valuation_result = await self._calculate_valuation(
            asset_type, valuation_method, input_data
        )

        # Step 3: Market comparable analysis
        market_analysis = self.market_comparables.calculate_market_implied_value(asset_type, input_data)
        comparables = self.market_comparables.find_comparables(asset_type, valuation_result["estimated_value"])

        # Step 4: Check compliance
        ias38_compliant = self._check_ias38_compliance(asset_type, input_data)
        asc350_compliant = self._check_asc350_compliance(asset_type, input_data)

        # Step 5: Store the asset record
        asset = AIAsset(
            organization_id=verification.organization_id,
            verification_id=verification.id,
            asset_type=AssetType(asset_type),
            asset_name=input_data.get("asset_name", "Unnamed Asset"),
            description=input_data.get("description", ""),
            valuation_method=ValuationMethod(valuation_method),
            estimated_value=valuation_result["estimated_value"],
            confidence_score=valuation_result["confidence_score"],
            valuation_inputs=input_data,
            valuation_breakdown=valuation_result["breakdown"],
            ias38_compliant=ias38_compliant,
            asc350_compliant=asc350_compliant,
        )
        self.session.add(asset)

        return {
            "asset_type": asset_type,
            "asset_name": input_data.get("asset_name", "Unnamed Asset"),
            "valuation_method": valuation_method,
            "estimated_value": valuation_result["estimated_value"],
            "confidence_score": valuation_result["confidence_score"],
            "valuation_breakdown": valuation_result["breakdown"],
            "ias38_compliant": ias38_compliant,
            "asc350_compliant": asc350_compliant,
            "classification": classification,
            "market_analysis": market_analysis,
            "comparables": comparables[:5],
        }

    async def _calculate_valuation(
        self, asset_type: str, method: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate valuation based on asset type and method."""
        calculators = {
            "training_data": self._value_training_data,
            "model_weights": self._value_model_weights,
            "inference_infra": self._value_inference_infra,
            "deployed_app": self._value_deployed_app,
        }
        calculator = calculators.get(asset_type, self._value_model_weights)
        return calculator(input_data)

    def _value_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value training data using cost approach (replacement cost)."""
        dataset_size_gb = data.get("dataset_size_gb", 100)
        training_cost = data.get("training_cost", 0)
        uniqueness = data.get("dataset_uniqueness_score", 0.5)

        # Base cost: collection + curation + storage
        collection_cost = dataset_size_gb * 50  # $50/GB for data collection
        curation_cost = dataset_size_gb * 200  # $200/GB for curation and annotation
        storage_cost = dataset_size_gb * 0.50 * 12  # Annual storage cost

        base_cost = collection_cost + curation_cost + storage_cost
        if training_cost > 0:
            base_cost = max(base_cost, training_cost)

        # Apply uniqueness multiplier (0-1 score mapped to multiplier)
        if uniqueness > 0.8:
            multiplier = DATA_UNIQUENESS_MULTIPLIER["exclusive"]
        elif uniqueness > 0.5:
            multiplier = DATA_UNIQUENESS_MULTIPLIER["proprietary"]
        elif uniqueness > 0.3:
            multiplier = DATA_UNIQUENESS_MULTIPLIER["curated"]
        else:
            multiplier = DATA_UNIQUENESS_MULTIPLIER["public"]

        estimated_value = base_cost * multiplier
        confidence = min(0.95, 0.6 + uniqueness * 0.3)

        return {
            "estimated_value": round(estimated_value, 2),
            "confidence_score": round(confidence, 3),
            "breakdown": {
                "collection_cost": round(collection_cost, 2),
                "curation_cost": round(curation_cost, 2),
                "storage_cost": round(storage_cost, 2),
                "base_cost": round(base_cost, 2),
                "uniqueness_multiplier": multiplier,
                "method": "cost_approach",
            },
        }

    def _value_model_weights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value model weights using cost approach (reproduction cost)."""
        compute_hours = data.get("training_compute_hours", 1000)
        training_cost = data.get("training_cost", 0)
        model_params = data.get("model_parameters", 0)
        gpu_type = data.get("gpu_type", "default")

        # Compute cost
        gpu_rate = COMPUTE_COST_PER_GPU_HOUR.get(gpu_type, COMPUTE_COST_PER_GPU_HOUR["default"])
        compute_cost = compute_hours * gpu_rate

        # R&D overhead (engineering, experimentation, failed runs)
        rd_overhead = compute_cost * 3.5  # Industry standard: 3.5x compute for total R&D

        # Model complexity premium based on parameters
        complexity_premium = 1.0
        if model_params > 100_000_000_000:  # >100B
            complexity_premium = 2.5
        elif model_params > 10_000_000_000:  # >10B
            complexity_premium = 1.8
        elif model_params > 1_000_000_000:  # >1B
            complexity_premium = 1.4

        base_cost = max(compute_cost + rd_overhead, training_cost) if training_cost > 0 else compute_cost + rd_overhead
        estimated_value = base_cost * complexity_premium
        confidence = min(0.95, 0.7 + (0.1 if training_cost > 0 else 0) + (0.1 if compute_hours > 100 else 0))

        return {
            "estimated_value": round(estimated_value, 2),
            "confidence_score": round(confidence, 3),
            "breakdown": {
                "compute_cost": round(compute_cost, 2),
                "rd_overhead": round(rd_overhead, 2),
                "complexity_premium": complexity_premium,
                "base_cost": round(base_cost, 2),
                "gpu_rate_per_hour": gpu_rate,
                "method": "cost_approach",
            },
        }

    def _value_inference_infra(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value inference infrastructure using income approach."""
        gpu_count = data.get("gpu_count", 8)
        gpu_type = data.get("gpu_type", "default")
        monthly_revenue = data.get("monthly_revenue", 0)
        inference_cost = data.get("inference_cost_per_query", 0.01)

        # Hardware replacement cost
        gpu_prices = {"H100": 35000, "A100": 15000, "V100": 5000, "default": 10000}
        hardware_value = gpu_count * gpu_prices.get(gpu_type, gpu_prices["default"])

        # If revenue data available, use income approach
        if monthly_revenue > 0:
            annual_revenue = monthly_revenue * 12
            # Apply earnings multiple for inference SaaS
            estimated_value = annual_revenue * 3  # 3x annual revenue for infra
            confidence = 0.88
        else:
            # Fall back to cost approach
            estimated_value = hardware_value * 1.5  # 1.5x for software + optimization
            confidence = 0.75

        return {
            "estimated_value": round(estimated_value, 2),
            "confidence_score": round(confidence, 3),
            "breakdown": {
                "hardware_value": round(hardware_value, 2),
                "gpu_count": gpu_count,
                "gpu_type": gpu_type,
                "monthly_revenue": monthly_revenue,
                "method": "income_approach" if monthly_revenue > 0 else "cost_approach",
            },
        }

    def _value_deployed_app(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value deployed application using income approach."""
        monthly_revenue = data.get("monthly_revenue", 0)
        monthly_active_users = data.get("monthly_active_users", 0)
        training_cost = data.get("training_cost", 0)

        if monthly_revenue > 0:
            annual_revenue = monthly_revenue * 12
            # SaaS multiples based on growth
            revenue_multiple = 10  # Default SaaS multiple
            estimated_value = annual_revenue * revenue_multiple
            confidence = 0.85
        elif monthly_active_users > 0:
            # Value per user approach
            value_per_user = 150  # Average for AI-powered B2B SaaS
            estimated_value = monthly_active_users * value_per_user
            confidence = 0.70
        elif training_cost > 0:
            # Fall back to cost + premium
            estimated_value = training_cost * 5
            confidence = 0.55
        else:
            estimated_value = 0
            confidence = 0.30

        return {
            "estimated_value": round(estimated_value, 2),
            "confidence_score": round(confidence, 3),
            "breakdown": {
                "monthly_revenue": monthly_revenue,
                "annual_revenue": monthly_revenue * 12 if monthly_revenue else 0,
                "monthly_active_users": monthly_active_users,
                "revenue_multiple": 10 if monthly_revenue > 0 else 0,
                "method": "income_approach",
            },
        }

    @staticmethod
    def _check_ias38_compliance(asset_type: str, data: Dict[str, Any]) -> bool:
        """Check IAS 38 Intangible Asset Standard compliance."""
        # IAS 38 requires: identifiable, control, future economic benefits
        has_identifiable = bool(data.get("asset_name"))
        has_control = asset_type in ["training_data", "model_weights", "deployed_app"]
        has_economic_benefit = (
            data.get("monthly_revenue", 0) > 0
            or data.get("training_cost", 0) > 0
            or data.get("training_compute_hours", 0) > 0
        )
        return has_identifiable and has_control and has_economic_benefit

    @staticmethod
    def _check_asc350_compliance(asset_type: str, data: Dict[str, Any]) -> bool:
        """Check ASC 350 Goodwill and Other Intangible Assets compliance."""
        # ASC 350: finite vs indefinite life, amortization requirements
        has_useful_life = asset_type in ["training_data", "model_weights", "inference_infra"]
        has_measurement = (
            data.get("training_cost", 0) > 0
            or data.get("monthly_revenue", 0) > 0
        )
        return has_useful_life and has_measurement
