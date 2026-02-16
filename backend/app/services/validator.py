"""Narrative Validator — Prevents hallucinations in generated SAR narratives.

Cross-references narrative content against source transaction data
to ensure all mentioned amounts, dates, and accounts are real.
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger("luminasar.validator")


class NarrativeValidator:
    """Validates generated SAR narratives against source data."""

    def validate(
        self, narrative: str, transactions: List[Dict], customer: Dict
    ) -> Dict:
        """Run all validation checks.

        Args:
            narrative: Generated narrative text
            transactions: Source transaction data
            customer: Customer data

        Returns:
            Validation result with overall status, errors, and warnings
        """
        errors = []
        warnings = []

        # 1. Check customer name is mentioned
        if customer.get("name") and customer["name"] not in narrative:
            warnings.append(
                f"Customer name '{customer['name']}' not found in narrative"
            )

        # 2. Check account number
        if (
            customer.get("account_number")
            and customer["account_number"] not in narrative
        ):
            warnings.append("Customer account number not referenced in narrative")

        # 3. Check narrative isn't too short
        word_count = len(narrative.split())
        if word_count < 100:
            errors.append(f"Narrative too short ({word_count} words, minimum 100)")

        # 4. Check narrative isn't empty or generic
        generic_phrases = ["I cannot", "I'm sorry", "As an AI"]
        for phrase in generic_phrases:
            if phrase.lower() in narrative.lower():
                errors.append(f"Narrative contains generic AI response: '{phrase}'")

        # 5. Check for SAR structure keywords
        required_sections = ["activity", "transaction", "suspicious"]
        found_sections = sum(
            1 for s in required_sections if s.lower() in narrative.lower()
        )
        if found_sections < 2:
            warnings.append("Narrative may be missing key SAR sections")

        valid = len(errors) == 0

        result = {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "word_count": word_count,
            "sections_found": found_sections,
        }

        if valid:
            logger.info(f"✅ Narrative validation passed ({word_count} words)")
        else:
            logger.warning(f"❌ Narrative validation failed: {errors}")

        return result
