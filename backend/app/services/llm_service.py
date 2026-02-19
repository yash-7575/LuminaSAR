"""
LLM Service — Interface with Ollama for SAR narrative generation.

Hybrid RAG Enabled:
- Structural templates (Chroma)
- Similar historical SAR cases (FAISS)
"""

import httpx
from typing import Dict, List
from app.config import get_settings
from app.utils.prompts import SAR_GENERATION_PROMPT
import logging
import re

logger = logging.getLogger("luminasar.llm")
settings = get_settings()


class LLMService:
    """Interfaces with Ollama to generate SAR narratives."""

    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_host

    # ======================================================
    # PROMPT CREATION (HYBRID RAG ENABLED)
    # ======================================================

    def create_sar_prompt(
        self,
        customer_data: dict,
        transactions: List[dict],
        patterns: dict,
        templates: str,
        typologies: List[str],
        similar_cases: str,  # 🔥 NEW PARAM
    ) -> str:
        """Construct grounded prompt for SAR generation."""

        # -----------------------------
        # Format transactions
        # -----------------------------
        transaction_lines = []
        for t in transactions[:25]:
            line = (
                f"  - ₹{float(t.get('amount', 0)):,.2f} on {t.get('date', 'N/A')} "
                f"from {t.get('source_account', 'N/A')} "
                f"to {t.get('destination_account', 'N/A')} "
                f"({t.get('transaction_type', 'unknown')})"
            )
            transaction_lines.append(line)

        transactions_text = "\n".join(transaction_lines)

        if len(transactions) > 25:
            transactions_text += (
                f"\n  ... and {len(transactions) - 25} more transactions"
            )

        # -----------------------------
        # Extract pattern components
        # -----------------------------
        velocity = patterns.get("velocity", {})
        volume = patterns.get("volume", {})
        structuring = patterns.get("structuring", {})
        network = patterns.get("network", {})

        # -----------------------------
        # Build final prompt
        # -----------------------------
        prompt = SAR_GENERATION_PROMPT.format(
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
            templates_text=templates if templates else "No templates available.",
            similar_cases=similar_cases if similar_cases else "No similar cases found.",
        )

        return prompt

    # ======================================================
    # GENERATE VIA OLLAMA
    # ======================================================

    async def generate_narrative(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 800,  # 🔥 Reduced to avoid timeout
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

    # ======================================================
    # VALIDATION
    # ======================================================

    def validate_narrative(self, narrative: str, source_data: dict) -> dict:
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        amount_pattern = r"₹[\d,]+(?:\.\d+)?"
        amounts_in_narrative = re.findall(amount_pattern, narrative)

        source_amounts = set()
        transactions = source_data.get("transactions", [])
        total = sum(float(t.get("amount", 0)) for t in transactions)
        source_amounts.add(round(total, 2))

        for t in transactions:
            source_amounts.add(round(float(t.get("amount", 0)), 2))

        for amount_str in amounts_in_narrative:
            clean = amount_str.replace("₹", "").replace(",", "")
            try:
                amount_val = float(clean)
                matched = any(abs(amount_val - src) < 1.0 for src in source_amounts)

                if not matched and amount_val > 1000:
                    validation_result["warnings"].append(
                        f"Amount {amount_str} not found in source data"
                    )
            except ValueError:
                pass

        return validation_result
