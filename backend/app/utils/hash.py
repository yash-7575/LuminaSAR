"""Hash chain utilities for tamper-evident audit trail."""

import hashlib
import json
from typing import Dict


def compute_hash(data: Dict, exclude_keys: list = None) -> str:
    """Compute SHA-256 hash of a dictionary.

    Args:
        data: Dictionary to hash
        exclude_keys: Keys to exclude from hash computation

    Returns:
        SHA-256 hex digest string
    """
    data_copy = data.copy()
    for key in exclude_keys or []:
        data_copy.pop(key, None)

    # Create deterministic string representation
    data_string = json.dumps(data_copy, sort_keys=True, default=str)
    return hashlib.sha256(data_string.encode()).hexdigest()


GENESIS_HASH = "0" * 64
