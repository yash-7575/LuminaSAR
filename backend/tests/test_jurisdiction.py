"""Tests for jurisdiction context resolution and prompt generation."""

import pytest
from app.utils.prompts import JURISDICTION_CONTEXT


# ─── JURISDICTION_CONTEXT registry ───────────────────────────────────────────


EXPECTED_JURISDICTIONS = ["IN", "US", "UK", "EU", "SG", "HK", "UAE", "AU"]


class TestJurisdictionContext:
    @pytest.mark.parametrize("code", EXPECTED_JURISDICTIONS)
    def test_jurisdiction_exists(self, code):
        assert code in JURISDICTION_CONTEXT

    @pytest.mark.parametrize("code", EXPECTED_JURISDICTIONS)
    def test_jurisdiction_has_required_fields(self, code):
        ctx = JURISDICTION_CONTEXT[code]
        required = [
            "regulatory_body",
            "currency_symbol",
            "identity_name",
            "filing_threshold",
            "legal_terminology",
            "reporting_form",
            "sar_sections",
        ]
        for field in required:
            assert field in ctx, f"Missing '{field}' in {code}"
            assert ctx[field], f"Empty '{field}' in {code}"

    @pytest.mark.parametrize("code", EXPECTED_JURISDICTIONS)
    def test_sar_sections_has_at_least_four(self, code):
        """Each jurisdiction must define at least 4 SAR sections."""
        sections = JURISDICTION_CONTEXT[code]["sar_sections"]
        assert isinstance(sections, list)
        assert len(sections) >= 4

    def test_in_uses_rupee_symbol(self):
        assert JURISDICTION_CONTEXT["IN"]["currency_symbol"] == "₹"

    def test_us_uses_dollar_symbol(self):
        assert JURISDICTION_CONTEXT["US"]["currency_symbol"] == "$"

    def test_uk_uses_pound_symbol(self):
        assert JURISDICTION_CONTEXT["UK"]["currency_symbol"] == "£"

    def test_eu_uses_euro_symbol(self):
        assert JURISDICTION_CONTEXT["EU"]["currency_symbol"] == "€"

    def test_fallback_for_unknown_jurisdiction(self):
        """Unknown jurisdiction code falls back to IN."""
        ctx = JURISDICTION_CONTEXT.get("ZZ", JURISDICTION_CONTEXT["IN"])
        assert ctx["regulatory_body"] == "Financial Intelligence Unit (FIU-IND)"


# ─── Prompt formatting ──────────────────────────────────────────────────────


class TestPromptFormatting:
    @pytest.mark.asyncio
    async def test_create_prompt_uses_correct_currency_for_us(self):
        from app.services.llm_service import LLMService

        svc = LLMService()
        prompt = await svc.create_sar_prompt(
            customer_data={
                "name": "John Doe",
                "account_number": "US-ACC-001",
                "occupation": "N/A",
                "customer_since": "2020-01-01",
                "stated_income": 100000,
            },
            transactions=[
                {
                    "amount": 5000,
                    "date": "2024-01-01",
                    "source_account": "A",
                    "destination_account": "B",
                    "transaction_type": "wire",
                }
            ],
            patterns={
                "risk_score": 7,
                "velocity": {"time_span_days": 30, "transactions_per_day": 1, "risk": "MEDIUM"},
                "volume": {"total_amount": 5000, "avg_amount": 5000},
                "structuring": {"structuring_likelihood": 0.2, "near_threshold_count": 0},
                "network": {"unique_sources": 1, "unique_destinations": 1},
            },
            templates=[],
            typologies=["Structuring"],
            jurisdiction="US",
        )
        assert "$" in prompt
        assert "FinCEN" in prompt
        assert "BSA" in prompt or "PATRIOT" in prompt

    @pytest.mark.asyncio
    async def test_create_prompt_uses_correct_currency_for_in(self):
        from app.services.llm_service import LLMService

        svc = LLMService()
        prompt = await svc.create_sar_prompt(
            customer_data={
                "name": "Ravi Kumar",
                "account_number": "IN-ACC-001",
                "occupation": "N/A",
                "customer_since": "2020-01-01",
                "stated_income": 500000,
            },
            transactions=[
                {
                    "amount": 50000,
                    "date": "2024-01-01",
                    "source_account": "A",
                    "destination_account": "B",
                    "transaction_type": "cash",
                }
            ],
            patterns={
                "risk_score": 8,
                "velocity": {"time_span_days": 10, "transactions_per_day": 5, "risk": "HIGH"},
                "volume": {"total_amount": 50000, "avg_amount": 50000},
                "structuring": {"structuring_likelihood": 0.8, "near_threshold_count": 3},
                "network": {"unique_sources": 2, "unique_destinations": 3},
            },
            templates=[],
            typologies=["Structuring"],
            jurisdiction="IN",
        )
        assert "₹" in prompt
        assert "FIU-IND" in prompt
        assert "PMLA" in prompt
