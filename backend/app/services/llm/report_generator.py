import json
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Advanced LLM-powered report generation using DeepSeek Reasoner for deep analysis."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def generate_credit_executive_report(
        self, org_id: UUID, verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive credit portfolio executive report."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior credit analyst at a Big 4 firm preparing an LP quarterly report. "
                    "Generate a comprehensive analysis with the following sections in JSON format:\n"
                    "1. executive_summary: 2-3 paragraph executive overview\n"
                    "2. portfolio_health: overall health assessment (excellent/good/fair/poor) with reasoning\n"
                    "3. risk_factors: list of identified risks with severity (high/medium/low) and mitigation\n"
                    "4. covenant_narrative: human-readable covenant compliance narrative\n"
                    "5. recommendations: list of actionable recommendations\n"
                    "6. outlook: forward-looking statement on portfolio trajectory\n"
                    "7. key_metrics_commentary: commentary on key financial metrics\n"
                    "Use professional language suitable for institutional LPs and fund boards."
                ),
            },
            {
                "role": "user",
                "content": f"Generate executive report for this credit portfolio verification:\n\n{json.dumps(verification_data, indent=2, default=str)}",
            },
        ]

        try:
            # Use reasoning model for deep analysis if available
            is_reasoning_model = model in ["deepseek-reasoner", "o1", "o1-mini"]
            if is_reasoning_model:
                response = await provider.reason(messages, model=model)
            else:
                response = await provider.chat(messages, model=model, temperature=0.3, max_tokens=4096)
            return _extract_json(response)
        except LLMProcessingError:
            raise
        except Exception as e:
            logger.error(f"Credit executive report generation failed: {e}")
            raise LLMProcessingError(f"Credit executive report failed: {e}")

    async def generate_aiip_executive_report(
        self, org_id: UUID, verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive AI-IP valuation executive report."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior AI-IP valuation expert preparing a board-ready report. "
                    "Generate a comprehensive valuation analysis in JSON format with:\n"
                    "1. executive_summary: 2-3 paragraph overview of the valuation\n"
                    "2. asset_classification: detailed reasoning for the asset type classification\n"
                    "3. valuation_narrative: human-readable explanation of how the value was determined\n"
                    "4. market_context: how this valuation compares to market benchmarks\n"
                    "5. risk_factors: list of risks with severity and impact on valuation\n"
                    "6. compliance_narrative: IAS 38 and ASC 350 compliance explanation\n"
                    "7. recommendations: actionable recommendations for value preservation/growth\n"
                    "8. sensitivity_analysis: how the valuation changes with key assumption changes (+/-20%)\n"
                    "Use language suitable for VC due diligence, M&A advisory, and tax authorities."
                ),
            },
            {
                "role": "user",
                "content": f"Generate executive report for this AI-IP valuation:\n\n{json.dumps(verification_data, indent=2, default=str)}",
            },
        ]

        try:
            is_reasoning_model = model in ["deepseek-reasoner", "o1", "o1-mini"]
            if is_reasoning_model:
                response = await provider.reason(messages, model=model)
            else:
                response = await provider.chat(messages, model=model, temperature=0.3, max_tokens=4096)
            return _extract_json(response)
        except LLMProcessingError:
            raise
        except Exception as e:
            logger.error(f"AI-IP executive report generation failed: {e}")
            raise LLMProcessingError(f"AI-IP executive report failed: {e}")

    async def generate_drift_analysis(
        self, org_id: UUID, current_data: Dict[str, Any], previous_data: Dict[str, Any], module: str
    ) -> Dict[str, Any]:
        """Generate LLM analysis of why values drifted between verifications."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a risk analyst investigating value changes between verification periods. "
                    "Compare the two verification results and provide analysis in JSON format:\n"
                    "1. drift_summary: concise summary of what changed\n"
                    "2. likely_causes: list of probable causes for the drift\n"
                    "3. risk_assessment: overall risk level (low/medium/high/critical)\n"
                    "4. action_items: recommended actions to investigate/address\n"
                    "5. trend_direction: whether the drift direction is positive/negative/neutral\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Module: {module}\n\n"
                    f"PREVIOUS verification result:\n{json.dumps(previous_data, indent=2, default=str)}\n\n"
                    f"CURRENT verification result:\n{json.dumps(current_data, indent=2, default=str)}"
                ),
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3, max_tokens=2048)
            return _extract_json(response)
        except Exception as e:
            logger.error(f"Drift analysis generation failed: {e}")
            raise LLMProcessingError(f"Drift analysis failed: {e}")
