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
        """Classify an AI asset using multi-stage structured analysis."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert AI-IP valuation analyst specializing in IAS 38 and ASC 350 compliance.\n\n"
                    "## Analysis Workflow\n"
                    "Follow this structured multi-stage approach:\n"
                    "1. IDENTIFICATION: Determine the asset category based on technical characteristics\n"
                    "2. VALUATION METHOD SELECTION: Choose the optimal approach considering asset maturity, "
                    "market comparables availability, and revenue generation potential\n"
                    "3. COMPLIANCE CHECK: Evaluate IAS 38 recognition criteria (identifiability, control, "
                    "future economic benefits) and ASC 350 indefinite-life intangible tests\n"
                    "4. CONFIDENCE SCORING: Self-assess confidence based on information completeness\n\n"
                    "## Quality Gates\n"
                    "- confidence must reflect actual information quality (low data = low confidence)\n"
                    "- key_value_drivers must be specific and measurable, not generic\n"
                    "- reasoning must cite specific IAS 38/ASC 350 paragraphs when relevant\n\n"
                    "## Output Schema (strict JSON)\n"
                    "{\n"
                    '  "asset_type": "training_data|model_weights|inference_infra|deployed_app",\n'
                    '  "valuation_method": "cost_approach|market_approach|income_approach",\n'
                    '  "key_value_drivers": ["specific driver 1", "specific driver 2", ...],\n'
                    '  "risk_factors": ["risk 1", "risk 2"],\n'
                    '  "ias38_eligible": true/false,\n'
                    '  "ias38_criteria": {"identifiability": true/false, "control": true/false, "future_benefits": true/false},\n'
                    '  "asc350_eligible": true/false,\n'
                    '  "confidence": 0.0-1.0,\n'
                    '  "confidence_factors": {"data_completeness": 0.0-1.0, "market_evidence": 0.0-1.0},\n'
                    '  "reasoning": "detailed multi-paragraph analysis"\n'
                    "}"
                ),
            },
            {"role": "user", "content": f"Classify this AI asset:\n\n{description}"},
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3)
            result = _extract_json(response)
            # Quality gate: ensure confidence is calibrated
            if "confidence" in result:
                result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
            return result
        except LLMProcessingError:
            raise
        except Exception as e:
            logger.error(f"Asset classification failed: {e}")
            raise LLMProcessingError(f"Asset classification failed: {e}")

    async def generate_valuation_report(
        self, org_id: UUID, asset_data: Dict[str, Any]
    ) -> str:
        """Generate a detailed valuation report using multi-stage structured workflow."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior AI-IP valuation expert at a Big 4 accounting firm.\n\n"
                    "## Report Structure (mandatory sections)\n"
                    "1. **Executive Summary** — 2-3 paragraph overview with headline valuation range\n"
                    "2. **Asset Description** — Technical capabilities, architecture, competitive positioning\n"
                    "3. **Valuation Methodology** — Selected approach with justification, comparable transactions cited\n"
                    "4. **Detailed Calculations** — Show all inputs, assumptions, discount rates, growth projections. "
                    "Present key figures in tabular format using markdown tables\n"
                    "5. **Sensitivity Analysis** — Bull/Base/Bear scenarios with value ranges\n"
                    "6. **IAS 38 / ASC 350 Compliance** — Paragraph-level assessment of recognition criteria\n"
                    "7. **Risk Factors** — Ranked by impact (High/Medium/Low) with mitigation strategies\n"
                    "8. **Conclusion** — Final valuation range with confidence interval\n\n"
                    "## Quality Standards\n"
                    "- Use markdown tables for all numerical data (inputs, scenarios, sensitivities)\n"
                    "- Include specific $ amounts, %, and basis point figures — never vague qualifiers alone\n"
                    "- All assumptions must be explicitly stated with source/rationale\n"
                    "- Professional language suitable for LP reports and board presentations\n"
                    "- Format all currency as USD with appropriate magnitude (M/B)\n\n"
                    "## Visualization Data\n"
                    "At the end of the report, include a JSON block fenced as ```json containing:\n"
                    "{\n"
                    '  "chart_data": {\n'
                    '    "valuation_waterfall": [{"label": "...", "value": N}, ...],\n'
                    '    "sensitivity_matrix": [{"scenario": "Bear|Base|Bull", "value": N, "probability": 0.X}, ...],\n'
                    '    "risk_heatmap": [{"risk": "...", "impact": "High|Medium|Low", "likelihood": "High|Medium|Low"}, ...]\n'
                    "  }\n"
                    "}\n"
                    "This data will be used to render professional charts in the frontend."
                ),
            },
            {
                "role": "user",
                "content": f"Generate a valuation report for:\n\n{json.dumps(asset_data, indent=2)}",
            },
        ]

        try:
            is_reasoning_model = model in ["deepseek-reasoner", "o1", "o1-mini"]
            if is_reasoning_model:
                return await provider.reason(messages, model=model)
            else:
                return await provider.chat(messages, model=model, temperature=0.4, max_tokens=8192)
        except Exception as e:
            logger.error(f"Valuation report generation failed: {e}")
            raise LLMProcessingError(f"Valuation report generation failed: {e}")

    async def analyze_loan_tape(self, org_id: UUID, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a loan tape using structured multi-stage credit analysis workflow."""
        provider, model = await self.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior credit analyst specializing in private credit portfolio analysis.\n\n"
                    "## Analysis Workflow (execute all stages)\n"
                    "**Stage 1 — Data Quality Assessment**: Check for missing data, outliers, inconsistencies\n"
                    "**Stage 2 — Anomaly Detection**: Flag unusual patterns (rate outliers, LTV spikes, "
                    "concentration clusters, maturity walls)\n"
                    "**Stage 3 — Risk Scoring**: Evaluate concentration risk (single-name, sector, geography), "
                    "credit quality distribution, and weighted average life\n"
                    "**Stage 4 — Covenant Analysis**: Assess DSCR, leverage, and concentration limit compliance "
                    "with specific margin-to-breach calculations\n"
                    "**Stage 5 — Health Rating**: Composite score (1-10) with breakdown by dimension\n\n"
                    "## Quality Gates\n"
                    "- Every anomaly must include severity (critical/warning/info) and affected loan count\n"
                    "- Concentration risks must cite specific percentages\n"
                    "- Health rating must be justified with sub-scores\n\n"
                    "## Output Schema (strict JSON)\n"
                    "{\n"
                    '  "data_quality": {"completeness": 0.0-1.0, "issues": ["..."]},\n'
                    '  "anomalies": [{"type": "...", "severity": "critical|warning|info", '
                    '"description": "...", "affected_loans": N, "recommendation": "..."}],\n'
                    '  "concentration_risks": [{"type": "...", "exposure_pct": 0.XX, '
                    '"threshold": 0.XX, "status": "within_limit|breached|near_breach"}],\n'
                    '  "covenant_assessment": {"dscr": {"value": N, "required": N, "margin": N, "status": "pass|fail|warning"}, '
                    '"leverage": {"value": N, "required": N, "margin": N, "status": "pass|fail|warning"}},\n'
                    '  "health_rating": N,\n'
                    '  "health_breakdown": {"credit_quality": N, "diversification": N, "covenant_headroom": N, "liquidity": N},\n'
                    '  "chart_data": {\n'
                    '    "health_radar": [{"axis": "Credit Quality", "value": N}, {"axis": "Diversification", "value": N}, ...],\n'
                    '    "risk_distribution": [{"category": "Low", "count": N}, {"category": "Medium", "count": N}, ...]\n'
                    "  },\n"
                    '  "summary": "2-3 sentence executive summary"\n'
                    "}"
                ),
            },
            {
                "role": "user",
                "content": f"Analyze this loan tape summary:\n\n{json.dumps(loan_data, indent=2)}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.3)
            result = _extract_json(response)
            # Quality gate: clamp health rating
            if "health_rating" in result:
                result["health_rating"] = max(1, min(10, int(result["health_rating"])))
            return result
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
                    "You are a verification analyst writing for LP reports and audit documentation.\n\n"
                    "## Summary Structure\n"
                    "1. **Verification Outcome** — Pass/Fail with key metrics (1 sentence)\n"
                    "2. **Scope** — What was verified (asset type, portfolio size, date range)\n"
                    "3. **Key Findings** — 2-3 bullet points with specific figures\n"
                    "4. **Proof Integrity** — Hash verification status and cryptographic method\n\n"
                    "## Standards\n"
                    "- Keep under 200 words total\n"
                    "- Use specific numbers, not vague qualifiers\n"
                    "- Professional tone suitable for board-level distribution\n"
                    "- Reference compliance frameworks (IAS 38, ASC 350, DSCR) where applicable"
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
