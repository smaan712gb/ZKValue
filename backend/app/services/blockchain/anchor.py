import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.verification import Verification, VerificationStatus
from app.models.blockchain import BlockchainAnchor, ProofAnchorMapping, AnchorStatus, ChainType
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlockchainAnchorService:
    """Anchor verification proof hashes to blockchain for tamper-evidence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_daily_anchor(self, anchor_date: datetime | None = None) -> Dict[str, Any]:
        """Collect all proof hashes from the day and create a Merkle root anchor."""
        if anchor_date is None:
            anchor_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        next_day = anchor_date + timedelta(days=1)

        # Get all completed verifications with proofs from that day
        result = await self.session.execute(
            select(Verification).where(
                Verification.status == VerificationStatus.completed,
                Verification.proof_hash.isnot(None),
                Verification.completed_at >= anchor_date,
                Verification.completed_at < next_day,
            ).order_by(Verification.completed_at)
        )
        verifications = result.scalars().all()

        if not verifications:
            return {
                "status": "no_proofs",
                "message": f"No completed verifications with proofs found for {anchor_date.strftime('%Y-%m-%d')}",
                "anchor_date": anchor_date.isoformat(),
            }

        # Collect proof hashes
        proof_hashes = [v.proof_hash for v in verifications]

        # Build Merkle tree
        merkle_root, merkle_proofs = self._build_merkle_tree_with_proofs(proof_hashes)

        # Create anchor record
        anchor = BlockchainAnchor(
            chain=ChainType.polygon,
            merkle_root=merkle_root,
            proof_count=len(proof_hashes),
            status=AnchorStatus.pending,
            anchor_date=anchor_date,
            proof_hashes=proof_hashes,
            contract_address=getattr(settings, 'BLOCKCHAIN_CONTRACT_ADDRESS', None),
        )
        self.session.add(anchor)
        await self.session.flush()

        # Create proof-to-anchor mappings
        for i, v in enumerate(verifications):
            mapping = ProofAnchorMapping(
                anchor_id=anchor.id,
                verification_id=v.id,
                organization_id=v.organization_id,
                proof_hash=v.proof_hash,
                merkle_index=i,
                merkle_proof=merkle_proofs.get(i, []),
            )
            self.session.add(mapping)

        # Submit to blockchain
        tx_result = await self._submit_to_chain(anchor)

        return {
            "anchor_id": str(anchor.id),
            "merkle_root": merkle_root,
            "proof_count": len(proof_hashes),
            "anchor_date": anchor_date.isoformat(),
            "tx_hash": tx_result.get("tx_hash"),
            "status": anchor.status.value,
            "chain": anchor.chain.value,
        }

    async def verify_proof_on_chain(
        self, proof_hash: str
    ) -> Dict[str, Any]:
        """Verify that a proof hash is anchored on-chain."""
        # Find the mapping
        result = await self.session.execute(
            select(ProofAnchorMapping).where(
                ProofAnchorMapping.proof_hash == proof_hash
            )
        )
        mapping = result.scalar_one_or_none()

        if not mapping:
            return {
                "proof_hash": proof_hash,
                "anchored": False,
                "message": "Proof hash not found in any blockchain anchor",
            }

        # Get the anchor
        anchor_result = await self.session.execute(
            select(BlockchainAnchor).where(BlockchainAnchor.id == mapping.anchor_id)
        )
        anchor = anchor_result.scalar_one_or_none()

        if not anchor:
            return {
                "proof_hash": proof_hash,
                "anchored": False,
                "message": "Anchor record not found",
            }

        # Verify Merkle proof locally
        is_valid = self._verify_merkle_proof(
            proof_hash, mapping.merkle_index, mapping.merkle_proof, anchor.merkle_root
        )

        return {
            "proof_hash": proof_hash,
            "anchored": True,
            "merkle_root": anchor.merkle_root,
            "merkle_valid": is_valid,
            "tx_hash": anchor.tx_hash,
            "block_number": anchor.block_number,
            "chain": anchor.chain.value,
            "anchor_date": anchor.anchor_date.isoformat() if anchor.anchor_date else None,
            "anchor_status": anchor.status.value,
            "contract_address": anchor.contract_address,
        }

    async def get_anchors(
        self, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """List all blockchain anchors with pagination."""
        count_result = await self.session.execute(
            select(func.count(BlockchainAnchor.id))
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(
            select(BlockchainAnchor)
            .order_by(BlockchainAnchor.anchor_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        anchors = result.scalars().all()

        import math
        return {
            "items": [
                {
                    "id": str(a.id),
                    "chain": a.chain.value,
                    "merkle_root": a.merkle_root,
                    "proof_count": a.proof_count,
                    "tx_hash": a.tx_hash,
                    "block_number": a.block_number,
                    "status": a.status.value,
                    "anchor_date": a.anchor_date.isoformat() if a.anchor_date else None,
                    "gas_used": a.gas_used,
                    "created_at": a.created_at,
                }
                for a in anchors
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    def _build_merkle_tree_with_proofs(
        self, leaves: List[str]
    ) -> Tuple[str, Dict[int, List[str]]]:
        """Build Merkle tree and return root + proofs for each leaf."""
        if not leaves:
            return "0x" + hashlib.sha256(b"empty").hexdigest(), {}

        # Normalize leaves (remove 0x prefix if present)
        normalized = [l.replace("0x", "") for l in leaves]

        # Hash leaves
        current_level = [
            hashlib.sha256(h.encode()).hexdigest() for h in normalized
        ]

        # Track tree levels for proof generation
        tree_levels = [current_level[:]]

        # Build tree
        while len(current_level) > 1:
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i + 1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            current_level = next_level
            tree_levels.append(current_level[:])

        root = f"0x{current_level[0]}"

        # Generate proofs for each leaf
        proofs: Dict[int, List[str]] = {}
        for leaf_idx in range(len(leaves)):
            proof = []
            idx = leaf_idx
            for level in tree_levels[:-1]:
                # Pad level if odd
                padded = level[:]
                if len(padded) % 2 == 1:
                    padded.append(padded[-1])
                sibling_idx = idx ^ 1  # XOR to get sibling
                if sibling_idx < len(padded):
                    proof.append(f"0x{padded[sibling_idx]}")
                idx //= 2
            proofs[leaf_idx] = proof

        return root, proofs

    def _verify_merkle_proof(
        self, leaf_hash: str, leaf_index: int, proof: List[str], root: str
    ) -> bool:
        """Verify a Merkle proof for a specific leaf."""
        normalized = leaf_hash.replace("0x", "")
        current = hashlib.sha256(normalized.encode()).hexdigest()

        idx = leaf_index
        for sibling in proof:
            sibling_hash = sibling.replace("0x", "")
            if idx % 2 == 0:
                combined = current + sibling_hash
            else:
                combined = sibling_hash + current
            current = hashlib.sha256(combined.encode()).hexdigest()
            idx //= 2

        return f"0x{current}" == root

    async def _submit_to_chain(self, anchor: BlockchainAnchor) -> Dict[str, Any]:
        """Submit Merkle root to blockchain. Uses web3.py if configured, otherwise simulates."""
        private_key = getattr(settings, 'BLOCKCHAIN_PRIVATE_KEY', '')
        rpc_url = getattr(settings, 'BLOCKCHAIN_RPC_URL', '')
        contract_address = getattr(settings, 'BLOCKCHAIN_CONTRACT_ADDRESS', '')

        if not private_key or not rpc_url:
            # Simulation mode — record anchor without actual blockchain tx
            logger.info(f"Blockchain anchoring in simulation mode. Merkle root: {anchor.merkle_root}")
            anchor.status = AnchorStatus.confirmed
            anchor.tx_hash = f"0x{'0' * 64}"  # Placeholder
            anchor.block_number = 0
            return {"tx_hash": anchor.tx_hash, "simulated": True}

        try:
            from web3 import Web3
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not w3.is_connected():
                raise ConnectionError("Cannot connect to blockchain RPC")

            account = w3.eth.account.from_key(private_key)

            # Simple data anchoring via a self-transfer with data
            # In production, use a dedicated smart contract
            merkle_bytes = bytes.fromhex(anchor.merkle_root.replace("0x", ""))

            if contract_address:
                # Call anchor contract
                # ABI for: function anchor(bytes32 merkleRoot, uint256 proofCount)
                contract_abi = [
                    {
                        "inputs": [
                            {"name": "merkleRoot", "type": "bytes32"},
                            {"name": "proofCount", "type": "uint256"},
                        ],
                        "name": "anchor",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function",
                    }
                ]
                contract = w3.eth.contract(address=contract_address, abi=contract_abi)
                tx = contract.functions.anchor(merkle_bytes, anchor.proof_count).build_transaction({
                    "from": account.address,
                    "nonce": w3.eth.get_transaction_count(account.address),
                    "gas": 100000,
                    "gasPrice": w3.eth.gas_price,
                })
            else:
                # Simple data transaction
                tx = {
                    "to": account.address,
                    "value": 0,
                    "data": w3.to_hex(merkle_bytes),
                    "nonce": w3.eth.get_transaction_count(account.address),
                    "gas": 50000,
                    "gasPrice": w3.eth.gas_price,
                }

            signed = w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            anchor.tx_hash = receipt.transactionHash.hex()
            anchor.block_number = receipt.blockNumber
            anchor.gas_used = receipt.gasUsed
            anchor.gas_price_gwei = tx.get("gasPrice", 0) // 10**9
            anchor.status = AnchorStatus.confirmed if receipt.status == 1 else AnchorStatus.failed

            logger.info(f"Blockchain anchor confirmed: tx={anchor.tx_hash}, block={anchor.block_number}")
            return {"tx_hash": anchor.tx_hash, "block_number": anchor.block_number, "simulated": False}

        except ImportError:
            logger.warning("web3 not installed, using simulation mode")
            anchor.status = AnchorStatus.confirmed
            anchor.tx_hash = f"0x{'0' * 64}"
            return {"tx_hash": anchor.tx_hash, "simulated": True}
        except Exception as e:
            logger.error(f"Blockchain submission failed: {e}")
            anchor.status = AnchorStatus.failed
            anchor.error_message = str(e)
            return {"error": str(e), "simulated": False}
