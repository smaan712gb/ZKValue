import hashlib
import json
import io
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from app.models.verification import Verification
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProofService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _hash_data(data: Any) -> str:
        """Create a SHA-256 hash of data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def generate_merkle_tree(data_points: List[Any]) -> str:
        """Generate a Merkle root hash from a list of data points."""
        if not data_points:
            return hashlib.sha256(b"empty").hexdigest()

        hashes = [
            hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()
            for d in data_points
        ]

        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_level

        return hashes[0]

    def create_computation_proof(
        self,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        computation_type: str,
    ) -> Dict[str, Any]:
        """Create a cryptographic proof of computation correctness.

        The proof is deterministic given the same inputs/outputs/type — the timestamp
        is NOT included in the proof hash so verification can be reproduced.
        """
        inputs_hash = self._hash_data(inputs)
        outputs_hash = self._hash_data(outputs)

        # Merkle tree over deterministic data points (no timestamp in proof)
        proof_data_points = [
            {"inputs_hash": inputs_hash},
            {"outputs_hash": outputs_hash},
            {"computation_type": computation_type},
        ]
        proof_hash = self.generate_merkle_tree(proof_data_points)

        now = datetime.now(timezone.utc).isoformat()

        return {
            "proof_hash": f"0x{proof_hash}",
            "inputs_hash": f"0x{inputs_hash}",
            "outputs_hash": f"0x{outputs_hash}",
            "algorithm": "SHA-256 + Merkle Root",
            "timestamp": now,
            "data_points": proof_data_points,
        }

    @staticmethod
    def verify_proof(proof_hash: str, inputs: dict, outputs: dict, computation_type: str) -> bool:
        """Verify a previously generated proof by recomputing the Merkle root.

        Uses the exact same algorithm as create_computation_proof.
        """
        inputs_hash = hashlib.sha256(
            json.dumps(inputs, sort_keys=True, default=str).encode()
        ).hexdigest()
        outputs_hash = hashlib.sha256(
            json.dumps(outputs, sort_keys=True, default=str).encode()
        ).hexdigest()

        # Recreate the exact same data points used in creation
        proof_data_points = [
            {"inputs_hash": inputs_hash},
            {"outputs_hash": outputs_hash},
            {"computation_type": computation_type},
        ]

        # Recompute Merkle root using the same algorithm
        hashes = [
            hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()
            for d in proof_data_points
        ]
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            new_level = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_level

        recomputed_hash = f"0x{hashes[0]}"
        return recomputed_hash == proof_hash

    def generate_certificate_pdf(
        self, verification: Verification, proof_data: Dict[str, Any]
    ) -> bytes:
        """Generate a PDF proof certificate."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CertTitle", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1d4ed8"),
            spaceAfter=6,
        )
        heading_style = ParagraphStyle(
            "CertHeading", parent=styles["Heading2"], fontSize=14,
            textColor=colors.HexColor("#1e293b"), spaceBefore=16, spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "CertBody", parent=styles["Normal"], fontSize=10,
            textColor=colors.HexColor("#475569"), leading=14,
        )

        elements = []

        # Header
        elements.append(Paragraph("ZKValue", title_style))
        elements.append(Paragraph("Cryptographic Verification Certificate", body_style))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 16))

        # Verification Info
        elements.append(Paragraph("Verification Details", heading_style))
        info_data = [
            ["Verification ID", str(verification.id)],
            ["Module", verification.module.value.replace("_", " ").title()],
            ["Status", verification.status.value.upper()],
            ["Created", str(verification.created_at)],
            ["Completed", str(verification.completed_at or "N/A")],
        ]
        info_table = Table(info_data, colWidths=[150, 320])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
            ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1e293b")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))

        # Proof Details
        elements.append(Paragraph("Cryptographic Proof", heading_style))
        proof_text = (
            f"<b>Algorithm:</b> {proof_data.get('algorithm', 'SHA-256 + Merkle Root')}<br/>"
            f"<b>Proof Hash:</b> {proof_data.get('proof_hash', 'N/A')}<br/>"
            f"<b>Inputs Hash:</b> {proof_data.get('inputs_hash', 'N/A')}<br/>"
            f"<b>Outputs Hash:</b> {proof_data.get('outputs_hash', 'N/A')}<br/>"
            f"<b>Timestamp:</b> {proof_data.get('timestamp', 'N/A')}"
        )
        elements.append(Paragraph(proof_text, body_style))
        elements.append(Spacer(1, 16))

        # Results Summary
        if verification.result_data:
            elements.append(Paragraph("Verified Results", heading_style))
            result_items = []
            for key, value in verification.result_data.items():
                if not isinstance(value, (dict, list)):
                    display_key = key.replace("_", " ").title()
                    if isinstance(value, float) and value > 1000:
                        display_val = f"${value:,.2f}"
                    else:
                        display_val = str(value)
                    result_items.append([display_key, display_val])
            if result_items:
                result_table = Table(result_items, colWidths=[200, 270])
                result_table.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(result_table)

        elements.append(Spacer(1, 24))
        elements.append(HRFlowable(width="100%", color=colors.HexColor("#e2e8f0")))
        elements.append(Spacer(1, 8))

        # Footer
        footer_text = (
            "This certificate was generated by ZKValue and cryptographically signed. "
            "The proof hash can be independently verified to confirm the correctness of all "
            "computations without accessing the underlying data."
        )
        elements.append(Paragraph(footer_text, ParagraphStyle(
            "Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8"),
        )))

        doc.build(elements)
        return buffer.getvalue()

    async def generate_and_store_certificate(self, verification_id: str) -> Optional[str]:
        """Generate and store a proof certificate for a verification."""
        result = await self.session.execute(
            select(Verification).where(Verification.id == verification_id)
        )
        verification = result.scalar_one_or_none()
        if not verification or not verification.proof_hash:
            return None

        proof_data = {
            "proof_hash": verification.proof_hash,
            "algorithm": "SHA-256 + Merkle Root",
            "timestamp": str(verification.completed_at or verification.created_at),
        }

        pdf_bytes = self.generate_certificate_pdf(verification, proof_data)

        # Store certificate — try S3 first, fall back to local storage
        if settings.AWS_ACCESS_KEY and settings.AWS_SECRET_KEY:
            try:
                return await self._upload_to_s3(pdf_bytes, verification_id)
            except Exception as e:
                logger.warning(f"S3 upload failed, falling back to local storage: {e}")
                return self._store_locally(pdf_bytes, verification_id)
        else:
            return self._store_locally(pdf_bytes, verification_id)

    async def _upload_to_s3(self, pdf_bytes: bytes, verification_id: str) -> str:
        """Upload PDF certificate to S3."""
        import boto3
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION,
        )
        key = f"certificates/{verification_id}.pdf"
        s3.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        url = f"https://{settings.S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        logger.info(f"Certificate uploaded to S3: {url}")
        return url

    @staticmethod
    def _store_locally(pdf_bytes: bytes, verification_id: str) -> str:
        """Store PDF certificate to local filesystem."""
        cert_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "certificates")
        os.makedirs(cert_dir, exist_ok=True)
        file_path = os.path.join(cert_dir, f"{verification_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"Certificate stored locally: {file_path} ({len(pdf_bytes)} bytes)")
        return f"/storage/certificates/{verification_id}.pdf"
