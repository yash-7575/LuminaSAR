"""Audit Logger — Creates tamper-evident audit trail with hash chains.

Every step of the SAR generation pipeline is logged with:
- Step name
- Data sources used
- AI reasoning
- Confidence scores
- SHA-256 hash chain for integrity verification
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List
from app.utils.hash import compute_hash, GENESIS_HASH
import logging
import re

logger = logging.getLogger("luminasar.audit")


class AuditLogger:
    """Creates and manages hash-chained audit logs."""

    def __init__(self):
        self.logs: List[Dict] = []

    def log_step(
        self,
        step_name: str,
        data_sources: Dict,
        reasoning: Dict,
        outputs: Dict,
        confidence: float = 0.0,
    ):
        """Log a workflow step with hash chain.

        Args:
            step_name: Name of the pipeline step
            data_sources: Input data references used
            reasoning: AI reasoning for this step
            outputs: Output data produced
            confidence: Confidence score (0-1)
        """
        log_entry = {
            "step_name": step_name,
            "data_sources": data_sources,
            "reasoning": reasoning,
            "confidence_scores": {"confidence": confidence, **outputs},
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "previous_hash": self._get_last_hash(),
        }

        log_entry["current_hash"] = compute_hash(
            log_entry, exclude_keys=["current_hash"]
        )
        self.logs.append(log_entry)
        logger.info(
            f"📋 Audit: {step_name} (hash: {log_entry['current_hash'][:16]}...)"
        )

    def _get_last_hash(self) -> str:
        """Get hash of previous log entry."""
        if not self.logs:
            return GENESIS_HASH
        return self.logs[-1]["current_hash"]

    def verify_chain(self) -> bool:
        """Verify integrity of entire hash chain."""
        for i in range(1, len(self.logs)):
            if self.logs[i]["previous_hash"] != self.logs[i - 1]["current_hash"]:
                return False

            # Recompute and verify current hash
            expected = compute_hash(self.logs[i], exclude_keys=["current_hash"])
            if self.logs[i]["current_hash"] != expected:
                return False

        return True

    def create_sentence_attribution(
        self, narrative: str, transactions: List[Dict]
    ) -> Dict:
        """Map each sentence in the narrative to source transactions.

        This is the INNOVATION SHOWCASE — sentence-level data tracing.

        Args:
            narrative: Generated SAR narrative text
            transactions: Source transaction data

        Returns:
            Dictionary mapping sentence index to its data sources
        """
        sentences = [s.strip() for s in re.split(r"[.!?]+", narrative) if s.strip()]
        attribution = {}

        for i, sentence in enumerate(sentences):
            mentioned_ids = []
            mentioned_amounts = []
            mentioned_accounts = []

            for txn in transactions:
                txn_id = str(txn.get("transaction_id", ""))
                amount = str(txn.get("amount", ""))
                source = str(txn.get("source_account", ""))
                dest = str(txn.get("destination_account", ""))

                # Check if transaction ID (or short form) appears in sentence
                if txn_id[:8] in sentence:
                    mentioned_ids.append(txn_id)

                # Check if amount appears in sentence
                if amount and amount in sentence:
                    mentioned_amounts.append(float(txn.get("amount", 0)))

                # Check if account numbers appear
                if source and source in sentence:
                    mentioned_accounts.append(source)
                if dest and dest in sentence:
                    mentioned_accounts.append(dest)

            attribution[f"sentence_{i}"] = {
                "text": sentence,
                "transaction_ids": mentioned_ids,
                "amounts": mentioned_amounts,
                "accounts": mentioned_accounts,
                "has_data_reference": bool(
                    mentioned_ids or mentioned_amounts or mentioned_accounts
                ),
                "position": i,
            }

        return attribution

    def reset(self):
        """Reset the audit logger for a new generation."""
        self.logs = []
