import hashlib
import json
import logging
import time
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.model_registry import ModelUsageRecord, DataLineageEvent, ModelProvider, LineageEventType

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (approximate)
MODEL_PRICING = {
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}


class ModelRegistryService:
    """Track LLM model usage, costs, and data lineage for audit reproducibility."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_model_usage(
        self,
        org_id: UUID,
        verification_id: UUID,
        provider: str,
        model_name: str,
        operation: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str = "",
        response_text: str = "",
        success: bool = True,
        error_message: str | None = None,
    ) -> ModelUsageRecord:
        """Record an LLM model invocation for audit trail."""
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        pricing = MODEL_PRICING.get(model_name, {"input": 0.5, "output": 1.0})
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000

        # Hash prompts for reproducibility
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest() if system_prompt else None
        response_hash = hashlib.sha256(response_text.encode()).hexdigest() if response_text else None

        record = ModelUsageRecord(
            organization_id=org_id,
            verification_id=verification_id,
            provider=ModelProvider(provider) if provider in ModelProvider.__members__ else ModelProvider.custom,
            model_name=model_name,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_hash=prompt_hash,
            response_hash=response_hash,
            cost_usd=round(cost, 6),
            success="true" if success else "error",
            error_message=error_message,
        )
        self.session.add(record)
        return record

    async def record_lineage_event(
        self,
        org_id: UUID,
        verification_id: UUID,
        event_type: str,
        step_order: int,
        input_data: Any,
        output_data: Any,
        transformation: str,
        details: Dict[str, Any] | None = None,
        duration_ms: int = 0,
        parent_event_id: UUID | None = None,
    ) -> DataLineageEvent:
        """Record a data transformation step in the verification pipeline."""
        input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()
        output_hash = hashlib.sha256(
            json.dumps(output_data, sort_keys=True, default=str).encode()
        ).hexdigest()

        event = DataLineageEvent(
            organization_id=org_id,
            verification_id=verification_id,
            event_type=LineageEventType(event_type),
            step_order=step_order,
            input_hash=input_hash,
            output_hash=output_hash,
            transformation=transformation,
            details=details or {},
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
        )
        self.session.add(event)
        return event

    async def get_verification_lineage(
        self, org_id: UUID, verification_id: UUID
    ) -> Dict[str, Any]:
        """Get complete data lineage for a verification."""
        # Get lineage events
        events_result = await self.session.execute(
            select(DataLineageEvent).where(
                DataLineageEvent.organization_id == org_id,
                DataLineageEvent.verification_id == verification_id,
            ).order_by(DataLineageEvent.step_order)
        )
        events = events_result.scalars().all()

        # Get model usage
        usage_result = await self.session.execute(
            select(ModelUsageRecord).where(
                ModelUsageRecord.organization_id == org_id,
                ModelUsageRecord.verification_id == verification_id,
            ).order_by(ModelUsageRecord.created_at)
        )
        usages = usage_result.scalars().all()

        return {
            "verification_id": str(verification_id),
            "lineage_events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type.value,
                    "step_order": e.step_order,
                    "transformation": e.transformation,
                    "input_hash": e.input_hash,
                    "output_hash": e.output_hash,
                    "details": e.details,
                    "duration_ms": e.duration_ms,
                    "created_at": e.created_at,
                }
                for e in events
            ],
            "model_usage": [
                {
                    "id": str(u.id),
                    "provider": u.provider.value,
                    "model_name": u.model_name,
                    "operation": u.operation,
                    "total_tokens": u.total_tokens,
                    "cost_usd": u.cost_usd,
                    "latency_ms": u.latency_ms,
                    "success": u.success,
                    "prompt_hash": u.prompt_hash,
                    "response_hash": u.response_hash,
                    "created_at": u.created_at,
                }
                for u in usages
            ],
            "total_events": len(events),
            "total_llm_calls": len(usages),
            "total_tokens": sum(u.total_tokens for u in usages),
            "total_cost_usd": round(sum(u.cost_usd for u in usages), 4),
        }

    async def get_org_model_stats(self, org_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get aggregated model usage statistics for an organization."""
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.session.execute(
            select(
                ModelUsageRecord.model_name,
                ModelUsageRecord.provider,
                func.count(ModelUsageRecord.id).label("call_count"),
                func.sum(ModelUsageRecord.total_tokens).label("total_tokens"),
                func.sum(ModelUsageRecord.cost_usd).label("total_cost"),
                func.avg(ModelUsageRecord.latency_ms).label("avg_latency"),
            ).where(
                ModelUsageRecord.organization_id == org_id,
                ModelUsageRecord.created_at >= cutoff,
            ).group_by(ModelUsageRecord.model_name, ModelUsageRecord.provider)
        )
        rows = result.all()

        by_model = []
        for row in rows:
            by_model.append({
                "model_name": row.model_name,
                "provider": row.provider.value if hasattr(row.provider, 'value') else str(row.provider),
                "call_count": row.call_count,
                "total_tokens": row.total_tokens or 0,
                "total_cost_usd": round(float(row.total_cost or 0), 4),
                "avg_latency_ms": round(float(row.avg_latency or 0)),
            })

        return {
            "period_days": days,
            "by_model": by_model,
            "total_calls": sum(m["call_count"] for m in by_model),
            "total_tokens": sum(m["total_tokens"] for m in by_model),
            "total_cost_usd": round(sum(m["total_cost_usd"] for m in by_model), 4),
        }
