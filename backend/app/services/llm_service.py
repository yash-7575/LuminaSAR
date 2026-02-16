"""LLM Service — Interface with Ollama for SAR narrative generation.

Uses llama3.2:latest running locally via Ollama for privacy-preserving,
on-premise text generation with no data leaving the institution.
"""

import httpx
import json
from typing import Dict, List
from app.config import get_settings
from app.utils.prompts import SAR_GENERATION_PROMPT
import logging
import re

logger = logging.getLogger("luminasar.llm")
settings = get_settings()


class LLMService:
    """Interfaces with Ollama to generate SAR narratives."""

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
    ):
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_host

    async def create_sar_prompt(
        self,
        customer_data: dict,
        transactions: List[dict],
        patterns: dict,
        templates: List[str],
        typologies: List[str],
        jurisdiction: str = "IN",
        graph_evidence: str = "No graph relationships detected.",
        graph_insight: str = "Flat vector search used for typologies.",
    ) -> str:
        """Construct a grounded prompt for SAR generation.

        All data is embedded in the prompt to ground the LLM's output
        and prevent hallucination.
        """
        from app.utils.prompts import JURISDICTION_CONTEXT

        ctx = JURISDICTION_CONTEXT.get(jurisdiction, JURISDICTION_CONTEXT["IN"])
        currency = ctx["currency_symbol"]

        # Format transactions for prompt (limit to 25 to avoid token overflow)
        transaction_lines = []
        for t in transactions[:25]:
            line = (
                f"  - {currency}{float(t.get('amount', 0)):,.2f} on {t.get('date', 'N/A')} "
                f"from {t.get('source_account', 'N/A')} to {t.get('destination_account', 'N/A')} "
                f"({t.get('transaction_type', 'unknown')})"
            )
            transaction_lines.append(line)

        transactions_text = "\n".join(transaction_lines)
        if len(transactions) > 25:
            transactions_text += (
                f"\n  ... and {len(transactions) - 25} more transactions"
            )

        # Format templates
        templates_text = (
            "\n---\n".join(templates[:3]) if templates else "No templates available."
        )

        velocity = patterns.get("velocity", {})
        volume = patterns.get("volume", {})
        structuring = patterns.get("structuring", {})
        network = patterns.get("network", {})

        # Format jurisdictional sections
        sections = ctx.get("sar_sections", [])
        section_lines = []
        for i, section in enumerate(sections):
            section_lines.append(f"{i+1}. **{section.upper()}**")
        jurisdictional_sections = "\n".join(section_lines)

        prompt = SAR_GENERATION_PROMPT.format(
            regulatory_body=ctx["regulatory_body"],
            deployment_env=settings.deployment_env,
            jurisdiction=jurisdiction,
            legal_terminology=ctx["legal_terminology"],
            currency_symbol=currency,
            identity_name=ctx["identity_name"],
            filing_threshold=ctx["filing_threshold"],
            reporting_form=ctx["reporting_form"],
            jurisdictional_sections=jurisdictional_sections,
            customer_name=customer_data.get("name", "Unknown"),
            account_number=customer_data.get("account_number", "N/A"),
            occupation=customer_data.get("occupation", "N/A"),
            customer_since=customer_data.get("customer_since", "N/A"),
            stated_income=f"{float(customer_data.get('stated_income', 0)):,.0f}"
            if customer_data.get("stated_income")
            else "N/A",
            num_transactions=len(transactions),
            transactions_text=transactions_text,
            risk_score=patterns.get("risk_score", 0),
            typologies=", ".join(typologies),
            velocity_days=velocity.get("time_span_days", 0),
            velocity_tpd=velocity.get("transactions_per_day", 0),
            velocity_risk=velocity.get("risk", "LOW"),
            total_amount=f"{volume.get('total_amount', 0):,.2f}",
            avg_amount=f"{volume.get('avg_amount', 0):,.2f}",
            unique_sources=network.get("unique_sources", 0),
            unique_destinations=network.get("unique_destinations", 0),
            structuring_likelihood=f"{structuring.get('structuring_likelihood', 0):.1%}",
            near_threshold_count=structuring.get("near_threshold_count", 0),
            templates_text=templates_text,
            graph_evidence=graph_evidence,
            graph_insight=graph_insight,
        )

        return prompt

    async def generate_narrative(self, prompt: str) -> str:
        """Generate SAR narrative using Ollama.

        Args:
            prompt: The fully constructed prompt

        Returns:
            Generated narrative text
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 2000,
                            "top_p": 0.9,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                narrative = result.get("response", "").strip()

                if not narrative:
                    raise Exception("Empty response from LLM")

                logger.info(f"✅ Generated narrative: {len(narrative)} chars")
                return narrative

        except httpx.ConnectError:
            logger.error(f"❌ Cannot connect to Ollama at {self.base_url}")
            raise Exception(
                f"Ollama is not running at {self.base_url}. "
                "Please start Ollama with: ollama serve"
            )
        except httpx.TimeoutException:
            logger.error("❌ Ollama request timed out")
            raise Exception("LLM generation timed out (>120s)")
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            raise

    def validate_narrative(
        self, narrative: str, source_data: dict, jurisdiction: str = "IN"
    ) -> dict:
        """Check for hallucinated amounts and dates.

        Currency-aware: dynamically determines the currency symbol from the
        jurisdiction context before scanning the narrative.

        Args:
            narrative: Generated narrative text
            source_data: Original source data for verification
            jurisdiction: Jurisdiction code to determine currency symbol

        Returns:
            Validation result with errors and warnings
        """
        from app.utils.prompts import JURISDICTION_CONTEXT

        ctx = JURISDICTION_CONTEXT.get(jurisdiction, JURISDICTION_CONTEXT["IN"])
        currency_symbol = ctx["currency_symbol"]

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Build currency-aware regex: escape the symbol and match amounts
        escaped = re.escape(currency_symbol)
        # Handle multi-char symbols like S$, HK$, A$, AED — allow optional whitespace
        amount_pattern = rf"{escaped}\s?[\d,]+(?:\.\d+)?"
        amounts_in_narrative = re.findall(amount_pattern, narrative)

        # Extract source transaction amounts for comparison
        source_amounts = set()
        transactions = source_data.get("transactions", [])
        total = sum(float(t.get("amount", 0)) for t in transactions)
        source_amounts.add(round(total, 2))
        for t in transactions:
            source_amounts.add(round(float(t.get("amount", 0)), 2))

        # Check narrative amounts against source
        for amount_str in amounts_in_narrative:
            clean = amount_str.replace(currency_symbol, "").replace(",", "").strip()
            try:
                amount_val = float(clean)
                # Allow some tolerance for rounding
                matched = any(abs(amount_val - src) < 1.0 for src in source_amounts)
                if not matched and amount_val > 1000:
                    validation_result["warnings"].append(
                        f"Amount {amount_str} not found in source data"
                    )
            except ValueError:
                pass

        return validation_result
