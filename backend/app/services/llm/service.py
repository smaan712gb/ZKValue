import logging
import json
import re
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.organization import Organization
from app.services.llm.provider import get_llm_provider, LLMProvider

logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    """Raised when LLM provider is not properly configured."""
    pass


class LLMProcessingError(Exception):
    """Raised when LLM processing fails."""
    pass


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and extra text."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise LLMProcessingError(f"Could not extract valid JSON from LLM response: {text[:200]}")


class LLMService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_provider_for_org(self, org_id: UUID) -> tuple[LLMProvider, str]:
        """Get the LLM provider configured for an organization."""
        result = await self.session.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()

        if org:
            provider_name = org.llm_provider or settings.DEFAULT_LLM_PROVIDER
            model = org.llm_model or settings.DEFAULT_LLM_MODEL
        else:
            provider_name = settings.DEFAULT_LLM_PROVIDER
            model = settings.DEFAULT_LLM_MODEL

        # Get the appropriate API key
        api_keys = {
            "deepseek": settings.DEEPSEEK_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
        }
        api_key = api_keys.get(provider_name, "")

        if not api_key:
            raise LLMConfigurationError(
                f"No API key configured for LLM provider '{provider_name}'. "
                f"Set the {provider_name.upper()}_API_KEY environment variable or choose a different provider."
            )

        base_urls = {
            "deepseek": settings.DEEPSEEK_BASE_URL,
        }

        provider = get_llm_provider(
            provider_name,
            api_key=api_key,
            base_url=base_urls.get(provider_name),
        )
        return provider, model

    async def classify_asset(self, org_id: UUID, description: str) -> Dict[str, Any]:
        """Classify an AI asset using LLM analysis."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert AI-IP valuation analyst specializing in IAS 38 and ASC 350 compliance. "
                    "Classify the following AI asset and determine the most appropriate valuation method. "
                    "Respond in JSON format with keys: asset_type (training_data|model_weights|inference_infra|deployed_app), "
                    "valuation_method (cost_approach|market_approach|income_approach), "
                    "key_value_drivers (list of strings), "
                    "ias38_eligible (boolean), "
                    "asc350_eligible (boolean), "
                    "confidence (float 0-1), "
                    "reasoning (string)."
                ),
            },
            {"role": "user", "content": f"Classify this AI asset:\n\n{description}"},
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3)
            return _extract_json(response)
        except LLMProcessingError:
            raise
        except Exception as e:
            logger.error(f"Asset classification failed: {e}")
            raise LLMProcessingError(f"Asset classification failed: {e}")

    async def generate_valuation_report(
        self, org_id: UUID, asset_data: Dict[str, Any]
    ) -> str:
        """Generate a detailed valuation report using LLM."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior AI-IP valuation expert at a Big 4 accounting firm. "
                    "Generate a professional valuation report for the following AI asset. "
                    "Include: Executive Summary, Asset Description, Valuation Methodology, "
                    "Detailed Calculations, IAS 38 / ASC 350 Compliance Assessment, "
                    "Risk Factors, and Conclusion with final valuation range. "
                    "Use professional financial language suitable for board presentations."
                ),
            },
            {
                "role": "user",
                "content": f"Generate a valuation report for:\n\n{json.dumps(asset_data, indent=2)}",
            },
        ]

        try:
            # Use reasoning mode for complex analysis
            is_reasoning_model = model in ["deepseek-reasoner", "o1", "o1-mini"]
            if is_reasoning_model:
                return await provider.reason(messages, model=model)
            else:
                return await provider.chat(messages, model=model, temperature=0.4, max_tokens=8192)
        except Exception as e:
            logger.error(f"Valuation report generation failed: {e}")
            raise LLMProcessingError(f"Valuation report generation failed: {e}")

    async def analyze_loan_tape(self, org_id: UUID, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a loan tape using LLM for anomaly detection and insights."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior credit analyst specializing in private credit portfolio analysis. "
                    "Analyze the loan tape data provided and identify: "
                    "1. Any anomalies or concerning patterns, "
                    "2. Portfolio concentration risks, "
                    "3. Covenant compliance assessment, "
                    "4. Overall portfolio health rating (1-10). "
                    "Respond in JSON format with keys: anomalies (list), "
                    "concentration_risks (list), covenant_assessment (dict), "
                    "health_rating (int), summary (string)."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze this loan tape summary:\n\n{json.dumps(loan_data, indent=2)}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3)
            return _extract_json(response)
        except LLMProcessingError:
            raise
        except Exception as e:
            logger.error(f"Loan tape analysis failed: {e}")
            raise LLMProcessingError(f"Loan tape analysis failed: {e}")

    async def generate_proof_summary(
        self, org_id: UUID, verification_data: Dict[str, Any]
    ) -> str:
        """Generate a human-readable summary of a verification proof."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a verification analyst. Write a concise, professional summary "
                    "of the verification results suitable for LP reports and audit documentation. "
                    "Keep it under 200 words."
                ),
            },
            {
                "role": "user",
                "content": f"Summarize these verification results:\n\n{json.dumps(verification_data, indent=2)}",
            },
        ]

        try:
            return await provider.chat(messages, model=model, temperature=0.5, max_tokens=500)
        except Exception as e:
            logger.error(f"Proof summary generation failed: {e}")
            raise LLMProcessingError(f"Proof summary generation failed: {e}")
