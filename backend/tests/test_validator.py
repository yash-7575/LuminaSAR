"""Tests for currency-aware narrative validation."""

import pytest
from app.services.llm_service import LLMService


@pytest.fixture
def llm_service():
    return LLMService()


class TestCurrencyAwareValidation:
    def test_detects_rupee_amounts_in_narrative(self, llm_service):
        """IN jurisdiction: validate ₹ amounts."""
        narrative = "The subject transferred ₹9,500 on 2024-01-15 and ₹9,800 on 2024-01-16."
        source = {
            "transactions": [
                {"amount": 9500},
                {"amount": 9800},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="IN")
        assert result["valid"] is True
        assert len(result["warnings"]) == 0

    def test_detects_dollar_amounts_in_narrative(self, llm_service):
        """US jurisdiction: validate $ amounts."""
        narrative = "The subject transferred $9,500 on 2024-01-15 and $9,800 on 2024-01-16."
        source = {
            "transactions": [
                {"amount": 9500},
                {"amount": 9800},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="US")
        assert result["valid"] is True
        assert len(result["warnings"]) == 0

    def test_warns_on_hallucinated_dollar_amount(self, llm_service):
        """US jurisdiction: warn on amount not in source data."""
        narrative = "The subject transferred $50,000 in a single transaction."
        source = {
            "transactions": [
                {"amount": 9500},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="US")
        assert len(result["warnings"]) > 0
        assert "$50,000" in result["warnings"][0]

    def test_warns_on_hallucinated_rupee_amount(self, llm_service):
        """IN jurisdiction: warn on amount not in source data."""
        narrative = "The subject deposited ₹1,50,000 in cash."
        source = {
            "transactions": [
                {"amount": 5000},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="IN")
        assert len(result["warnings"]) > 0

    def test_pound_validation_uk(self, llm_service):
        """UK jurisdiction: validate £ amounts."""
        narrative = "The subject transferred £5,000 to an offshore account."
        source = {
            "transactions": [
                {"amount": 5000},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="UK")
        assert result["valid"] is True
        assert len(result["warnings"]) == 0

    def test_euro_validation_eu(self, llm_service):
        """EU jurisdiction: validate € amounts."""
        narrative = "Multiple transfers of €12,000 were detected."
        source = {
            "transactions": [
                {"amount": 12000},
            ]
        }
        result = llm_service.validate_narrative(narrative, source, jurisdiction="EU")
        assert result["valid"] is True
        assert len(result["warnings"]) == 0

    def test_no_amounts_in_narrative(self, llm_service):
        """Narrative with no currency amounts should pass validation."""
        narrative = "The customer exhibited suspicious behavior patterns."
        source = {"transactions": [{"amount": 1000}]}
        result = llm_service.validate_narrative(narrative, source, jurisdiction="US")
        assert result["valid"] is True
        assert len(result["warnings"]) == 0
