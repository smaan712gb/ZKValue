import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification, VerificationStatus, VerificationModule
from app.services.verification.proof import ProofService
from app.services.valuation.ai_ip import AIIPValuationService
from app.services.credit.analyzer import CreditAnalyzerService
from app.services.llm.service import LLMService
from app.services.notifications.service import NotificationService
from app.models.notification import NotificationType

logger = logging.getLogger(__name__)


class VerificationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.proof_service = ProofService(session)
        self.llm_service = LLMService(session)
        self.notification_service = NotificationService(session)

    async def create_verification(
        self,
        org_id: UUID,
        user_id: UUID,
        module: str,
        input_data: dict,
        metadata: dict | None = None,
    ) -> Verification:
        """Create a new verification record."""
        verification = Verification(
            organization_id=org_id,
            created_by=user_id,
            module=VerificationModule(module),
            status=VerificationStatus.pending,
            input_data=input_data,
            extra_metadata=metadata or {},
        )
        self.session.add(verification)
        await self.session.flush()
        await self.session.refresh(verification)
        logger.info(f"Created verification {verification.id} for org {org_id}")
        return verification

    async def process_verification(self, verification_id: str) -> None:
        """Main processing pipeline for a verification."""
        result = await self.session.execute(
            select(Verification).where(Verification.id == verification_id)
        )
        verification = result.scalar_one_or_none()
        if not verification:
            logger.error(f"Verification {verification_id} not found")
            return

        # Mark as processing
        verification.status = VerificationStatus.processing
        await self.session.flush()

        try:
            if verification.module == VerificationModule.private_credit:
                result_data = await self._process_credit(verification)
            elif verification.module == VerificationModule.ai_ip_valuation:
                result_data = await self._process_ai_ip(verification)
            else:
                raise ValueError(f"Unknown module: {verification.module}")

            # Generate proof
            proof_data = self.proof_service.create_computation_proof(
                inputs=verification.input_data,
                outputs=result_data,
                computation_type=verification.module.value,
            )

            # Update verification
            verification.result_data = result_data
            verification.proof_hash = proof_data["proof_hash"]
            verification.status = VerificationStatus.completed
            verification.completed_at = datetime.now(timezone.utc)
            await self.session.flush()

            # Generate certificate
            cert_url = await self.proof_service.generate_and_store_certificate(
                str(verification.id)
            )
            if cert_url:
                verification.proof_certificate_url = cert_url

            # Generate LLM executive summary for the report
            try:
                summary = await self.llm_service.generate_proof_summary(
                    verification.organization_id, result_data
                )
                if verification.extra_metadata is None:
                    verification.extra_metadata = {}
                verification.extra_metadata = {**verification.extra_metadata, "executive_summary": summary}
            except Exception as summary_err:
                logger.warning(f"Failed to generate executive summary: {summary_err}")

            await self.session.commit()
            logger.info(f"Verification {verification_id} completed successfully")

            # Send completion notification
            try:
                await self.notification_service.notify_verification_completed(
                    org_id=verification.organization_id,
                    verification_id=str(verification.id),
                    module=verification.module.value,
                    metadata=verification.extra_metadata or {},
                )
                await self.session.commit()
            except Exception as notify_err:
                logger.warning(f"Failed to send completion notification: {notify_err}")

        except Exception as e:
            logger.error(f"Verification {verification_id} failed: {e}")
            verification.status = VerificationStatus.failed
            verification.error_message = str(e)
            await self.session.commit()

            # Send failure notification
            try:
                await self.notification_service.notify_verification_failed(
                    org_id=verification.organization_id,
                    verification_id=str(verification.id),
                    error=str(e),
                    metadata=verification.extra_metadata or {},
                )
                await self.session.commit()
            except Exception as notify_err:
                logger.warning(f"Failed to send failure notification: {notify_err}")

    async def _process_credit(self, verification: Verification) -> dict:
        """Process a private credit verification."""
        credit_service = CreditAnalyzerService(self.session, self.llm_service)
        return await credit_service.process_verification(verification)

    async def _process_ai_ip(self, verification: Verification) -> dict:
        """Process an AI-IP valuation verification."""
        valuation_service = AIIPValuationService(self.session, self.llm_service)
        return await valuation_service.process_verification(verification)
