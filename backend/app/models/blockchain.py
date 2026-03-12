import enum
from sqlalchemy import Column, String, Integer, Enum, JSON, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import TenantMixin, TimestampMixin
from app.core.database import Base


class ChainType(str, enum.Enum):
    polygon = "polygon"
    ethereum = "ethereum"
    base = "base"


class AnchorStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    confirmed = "confirmed"
    failed = "failed"


class BlockchainAnchor(TimestampMixin, Base):
    """Global anchor records — not tenant-scoped since they aggregate across orgs."""
    __tablename__ = "blockchain_anchors"

    chain = Column(Enum(ChainType), default=ChainType.polygon, nullable=False)
    merkle_root = Column(String(66), nullable=False)  # 0x + 64 hex chars
    proof_count = Column(Integer, nullable=False)
    tx_hash = Column(String(66), nullable=True)  # Transaction hash
    block_number = Column(Integer, nullable=True)
    status = Column(Enum(AnchorStatus), default=AnchorStatus.pending, nullable=False)
    anchor_date = Column(DateTime(timezone=True), nullable=False)
    proof_hashes = Column(JSON, default=list, nullable=False)  # List of proof hashes included
    gas_used = Column(Integer, nullable=True)
    gas_price_gwei = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    contract_address = Column(String(42), nullable=True)


class ProofAnchorMapping(TimestampMixin, Base):
    """Maps individual proof hashes to their blockchain anchor."""
    __tablename__ = "proof_anchor_mappings"

    anchor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    verification_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    proof_hash = Column(String(66), nullable=False)
    merkle_index = Column(Integer, nullable=False)  # Position in the Merkle tree
    merkle_proof = Column(JSON, default=list, nullable=False)  # Siblings for verification
