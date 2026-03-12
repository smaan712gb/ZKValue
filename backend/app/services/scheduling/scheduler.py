import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schedule import VerificationSchedule, DriftAlert, ScheduleFrequency, AlertSeverity, AlertStatus
from app.models.verification import Verification, VerificationStatus
from app.services.verification.engine import VerificationEngine

logger = logging.getLogger(__name__)

FREQUENCY_DELTAS = {
    ScheduleFrequency.daily: timedelta(days=1),
    ScheduleFrequency.weekly: timedelta(weeks=1),
    ScheduleFrequency.monthly: timedelta(days=30),
    ScheduleFrequency.quarterly: timedelta(days=90),
}


class SchedulerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_due_schedules(self) -> list[VerificationSchedule]:
        """Find all schedules that are due for execution."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(VerificationSchedule).where(
                VerificationSchedule.is_active == True,
                VerificationSchedule.is_deleted == False,
                VerificationSchedule.next_run_at <= now,
            )
        )
        return list(result.scalars().all())

    async def execute_schedule(self, schedule: VerificationSchedule) -> Optional[str]:
        """Execute a scheduled verification and check for drift."""
        engine = VerificationEngine(self.session)

        verification = await engine.create_verification(
            org_id=schedule.organization_id,
            user_id=schedule.created_by,
            module=schedule.module,
            input_data=schedule.input_data,
            metadata={
                **schedule.extra_metadata,
                "scheduled": True,
                "schedule_id": str(schedule.id),
                "run_number": schedule.run_count + 1,
            },
        )
        await self.session.flush()

        # Process the verification
        await engine.process_verification(str(verification.id))

        # Refresh to get result
        await self.session.refresh(verification)

        # Check for drift if there's a previous verification
        if schedule.last_verification_id and verification.status == VerificationStatus.completed:
            await self._check_drift(schedule, verification)

        # Update schedule
        schedule.last_run_at = datetime.now(timezone.utc)
        schedule.last_verification_id = verification.id
        schedule.run_count += 1
        schedule.next_run_at = datetime.now(timezone.utc) + FREQUENCY_DELTAS[schedule.frequency]
        await self.session.flush()

        return str(verification.id)

    async def _check_drift(self, schedule: VerificationSchedule, current: Verification) -> None:
        """Compare current verification results with the previous one and create alerts."""
        result = await self.session.execute(
            select(Verification).where(Verification.id == schedule.last_verification_id)
        )
        previous = result.scalar_one_or_none()
        if not previous or not previous.result_data or not current.result_data:
            return

        prev_data = previous.result_data
        curr_data = current.result_data
        threshold = float(schedule.drift_threshold_pct)

        if schedule.module == "private_credit":
            await self._check_credit_drift(schedule, current, previous, prev_data, curr_data, threshold)
        elif schedule.module == "ai_ip_valuation":
            await self._check_valuation_drift(schedule, current, previous, prev_data, curr_data, threshold)

    async def _check_credit_drift(
        self, schedule, current, previous, prev_data, curr_data, threshold
    ):
        """Check for drift in credit portfolio metrics."""
        checks = [
            ("nav_drift", "nav_value", "NAV value"),
            ("ltv_drift", "avg_ltv_ratio", "Average LTV ratio"),
            ("rate_drift", "weighted_avg_rate", "Weighted average rate"),
        ]

        for alert_type, key, label in checks:
            prev_val = prev_data.get(key, 0)
            curr_val = curr_data.get(key, 0)
            if prev_val > 0:
                drift_pct = abs(curr_val - prev_val) / prev_val * 100
                if drift_pct > threshold:
                    direction = "increased" if curr_val > prev_val else "decreased"
                    severity = AlertSeverity.critical if drift_pct > threshold * 2 else AlertSeverity.warning

                    alert = DriftAlert(
                        organization_id=schedule.organization_id,
                        schedule_id=schedule.id,
                        verification_id=current.id,
                        previous_verification_id=previous.id,
                        severity=severity,
                        alert_type=alert_type,
                        message=f"{label} {direction} by {drift_pct:.1f}% (from {prev_val:,.2f} to {curr_val:,.2f})",
                        details={"previous": prev_val, "current": curr_val, "threshold": threshold},
                        drift_pct=drift_pct,
                    )
                    self.session.add(alert)

        # Check covenant breaches
        prev_covenants = prev_data.get("covenant_compliance", {})
        curr_covenants = curr_data.get("covenant_compliance", {})
        for covenant_name, curr_status in curr_covenants.items():
            prev_status = prev_covenants.get(covenant_name, {})
            if prev_status.get("compliant") and not curr_status.get("compliant"):
                alert = DriftAlert(
                    organization_id=schedule.organization_id,
                    schedule_id=schedule.id,
                    verification_id=current.id,
                    previous_verification_id=previous.id,
                    severity=AlertSeverity.critical,
                    alert_type="covenant_violation",
                    message=f"Covenant '{covenant_name}' breached: required {curr_status.get('required')}, actual {curr_status.get('actual')}",
                    details={"covenant": covenant_name, "previous": prev_status, "current": curr_status},
                    drift_pct=None,
                )
                self.session.add(alert)

        await self.session.flush()

    async def _check_valuation_drift(
        self, schedule, current, previous, prev_data, curr_data, threshold
    ):
        """Check for drift in AI-IP valuation."""
        prev_val = prev_data.get("estimated_value", 0)
        curr_val = curr_data.get("estimated_value", 0)
        if prev_val > 0:
            drift_pct = abs(curr_val - prev_val) / prev_val * 100
            if drift_pct > threshold:
                direction = "increased" if curr_val > prev_val else "decreased"
                severity = AlertSeverity.critical if drift_pct > threshold * 2 else AlertSeverity.warning

                alert = DriftAlert(
                    organization_id=schedule.organization_id,
                    schedule_id=schedule.id,
                    verification_id=current.id,
                    previous_verification_id=previous.id,
                    severity=severity,
                    alert_type="value_change",
                    message=f"Estimated value {direction} by {drift_pct:.1f}% (from ${prev_val:,.2f} to ${curr_val:,.2f})",
                    details={"previous_value": prev_val, "current_value": curr_val, "threshold": threshold},
                    drift_pct=drift_pct,
                )
                self.session.add(alert)

        # Check confidence score drop
        prev_conf = prev_data.get("confidence_score", 0)
        curr_conf = curr_data.get("confidence_score", 0)
        if prev_conf > 0 and curr_conf < prev_conf * 0.8:
            alert = DriftAlert(
                organization_id=schedule.organization_id,
                schedule_id=schedule.id,
                verification_id=current.id,
                previous_verification_id=previous.id,
                severity=AlertSeverity.warning,
                alert_type="confidence_drop",
                message=f"Confidence score dropped from {prev_conf:.2f} to {curr_conf:.2f}",
                details={"previous_confidence": prev_conf, "current_confidence": curr_conf},
                drift_pct=abs(curr_conf - prev_conf) / prev_conf * 100 if prev_conf > 0 else 0,
            )
            self.session.add(alert)

        await self.session.flush()

    @staticmethod
    def calculate_next_run(frequency: ScheduleFrequency, from_time: datetime = None) -> datetime:
        """Calculate the next run time for a schedule."""
        base = from_time or datetime.now(timezone.utc)
        return base + FREQUENCY_DELTAS[frequency]
