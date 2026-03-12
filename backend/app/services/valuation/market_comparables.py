import json
import logging
from typing import Dict, Any, List
from uuid import UUID
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError

logger = logging.getLogger(__name__)

# Recent AI M&A comparable transactions (updated periodically)
AI_MA_COMPARABLES = [
    {"company": "DeepMind", "acquirer": "Google", "year": 2014, "value_usd": 500_000_000, "asset_type": "model_weights", "employees": 75},
    {"company": "Kensho", "acquirer": "S&P Global", "year": 2018, "value_usd": 550_000_000, "asset_type": "deployed_app", "employees": 120},
    {"company": "DataRobot", "acquirer": "Private", "year": 2021, "value_usd": 6_200_000_000, "asset_type": "deployed_app", "employees": 1000},
    {"company": "Mosaic ML", "acquirer": "Databricks", "year": 2023, "value_usd": 1_300_000_000, "asset_type": "inference_infra", "employees": 60},
    {"company": "Inflection AI", "acquirer": "Microsoft", "year": 2024, "value_usd": 650_000_000, "asset_type": "model_weights", "employees": 70},
    {"company": "Character.ai", "acquirer": "Google", "year": 2024, "value_usd": 2_500_000_000, "asset_type": "deployed_app", "employees": 120},
    {"company": "Adept AI", "acquirer": "Amazon", "year": 2024, "value_usd": 650_000_000, "asset_type": "model_weights", "employees": 50},
    {"company": "Scale AI", "acquirer": "Private", "year": 2024, "value_usd": 14_000_000_000, "asset_type": "training_data", "employees": 800},
    {"company": "Wiz", "acquirer": "Google", "year": 2025, "value_usd": 32_000_000_000, "asset_type": "deployed_app", "employees": 1500},
]

# Benchmark multiples by asset type
BENCHMARK_MULTIPLES = {
    "training_data": {"cost_multiple": 3.0, "revenue_multiple": 8.0, "description": "Premium for proprietary, curated datasets"},
    "model_weights": {"cost_multiple": 5.0, "revenue_multiple": 15.0, "description": "High premium for frontier model capabilities"},
    "inference_infra": {"cost_multiple": 2.0, "revenue_multiple": 6.0, "description": "Valued primarily on efficiency and throughput"},
    "deployed_app": {"cost_multiple": 8.0, "revenue_multiple": 12.0, "description": "Revenue-generating applications command highest multiples"},
}


class MarketComparablesService:
    """Market comparable analysis for AI-IP valuations."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def find_comparables(self, asset_type: str, estimated_value: float) -> List[Dict[str, Any]]:
        """Find relevant comparable transactions."""
        # Filter by asset type first
        type_matches = [c for c in AI_MA_COMPARABLES if c["asset_type"] == asset_type]

        # If not enough type matches, include all
        if len(type_matches) < 3:
            type_matches = AI_MA_COMPARABLES

        # Sort by value proximity to the estimated value
        type_matches.sort(key=lambda c: abs(c["value_usd"] - estimated_value))

        return type_matches[:5]

    def get_benchmark_multiples(self, asset_type: str) -> Dict[str, Any]:
        """Get benchmark valuation multiples for an asset type."""
        return BENCHMARK_MULTIPLES.get(asset_type, BENCHMARK_MULTIPLES["model_weights"])

    def calculate_market_implied_value(
        self, asset_type: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate market-implied valuation using comparable multiples."""
        benchmarks = self.get_benchmark_multiples(asset_type)

        # Cost-based market value
        training_cost = input_data.get("training_cost", 0)
        compute_hours = input_data.get("training_compute_hours", 0)
        cost_base = max(training_cost, compute_hours * 2.0)  # $2/GPU-hr average
        cost_implied = cost_base * benchmarks["cost_multiple"]

        # Revenue-based market value
        monthly_revenue = input_data.get("monthly_revenue", 0)
        revenue_implied = monthly_revenue * 12 * benchmarks["revenue_multiple"] if monthly_revenue > 0 else 0

        # Weighted average (prefer revenue if available)
        if revenue_implied > 0 and cost_implied > 0:
            market_value = revenue_implied * 0.7 + cost_implied * 0.3
            confidence = 0.85
        elif revenue_implied > 0:
            market_value = revenue_implied
            confidence = 0.80
        elif cost_implied > 0:
            market_value = cost_implied
            confidence = 0.65
        else:
            market_value = 0
            confidence = 0.30

        return {
            "market_implied_value": round(market_value, 2),
            "cost_implied_value": round(cost_implied, 2),
            "revenue_implied_value": round(revenue_implied, 2),
            "cost_multiple_used": benchmarks["cost_multiple"],
            "revenue_multiple_used": benchmarks["revenue_multiple"],
            "confidence": confidence,
            "methodology_note": benchmarks["description"],
        }

    async def generate_comparable_analysis(
        self, org_id: UUID, asset_data: Dict[str, Any], estimated_value: float
    ) -> Dict[str, Any]:
        """Use LLM to generate a detailed comparable market analysis."""
        asset_type = asset_data.get("asset_type", "model_weights")
        comparables = self.find_comparables(asset_type, estimated_value)
        market_value = self.calculate_market_implied_value(asset_type, asset_data)
        benchmarks = self.get_benchmark_multiples(asset_type)

        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an M&A advisor specializing in AI company valuations. "
                    "Generate a comparable market analysis in JSON format:\n"
                    "1. analysis_summary: 1-2 paragraph summary of how the valuation compares to market\n"
                    "2. comparable_commentary: analysis of each comparable transaction's relevance\n"
                    "3. valuation_range: {low, mid, high} range based on comparables\n"
                    "4. premium_discount_factors: factors that would command premium or discount vs comps\n"
                    "5. market_positioning: where this asset sits in the competitive landscape\n"
                    "6. confidence_level: high/medium/low with reasoning\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Asset details:\n{json.dumps(asset_data, indent=2, default=str)}\n\n"
                    f"Our estimated value: ${estimated_value:,.2f}\n\n"
                    f"Comparable transactions:\n{json.dumps(comparables, indent=2)}\n\n"
                    f"Market implied value: {json.dumps(market_value, indent=2)}\n\n"
                    f"Benchmark multiples: {json.dumps(benchmarks, indent=2)}"
                ),
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3, max_tokens=3000)
            llm_analysis = _extract_json(response)
        except Exception as e:
            logger.error(f"Comparable analysis generation failed: {e}")
            llm_analysis = {"analysis_summary": "Comparable analysis could not be generated."}

        return {
            "comparables": comparables,
            "market_implied_value": market_value,
            "benchmarks": benchmarks,
            "llm_analysis": llm_analysis,
        }
