"""Tests for KnowledgeGraphService."""

import pytest
from app.services.graph_service import KnowledgeGraphService, RegulatoryAdvisory


@pytest.fixture
def graph_service():
    return KnowledgeGraphService()


# ─── get_typology_context ────────────────────────────────────────────────────


class TestGetTypologyContext:
    def test_returns_advisory_for_known_typology_in(self, graph_service):
        result = graph_service.get_typology_context(["Layering"], jurisdiction="IN")
        assert len(result["advisories"]) > 0
        assert "Layering" in result["evidence_text"]
        assert result["confidence_score"] > 0.3

    def test_returns_advisory_for_known_typology_us(self, graph_service):
        result = graph_service.get_typology_context(["Structuring"], jurisdiction="US")
        assert len(result["advisories"]) > 0
        assert any(a["jurisdiction"] == "US" for a in result["advisories"])
        assert "FinCEN" in result["evidence_text"] or "31 CFR" in result["evidence_text"]

    def test_falls_back_to_in_for_unknown_jurisdiction(self, graph_service):
        result = graph_service.get_typology_context(["Layering"], jurisdiction="ZZ")
        # Should fall back to IN advisories
        assert len(result["advisories"]) > 0
        assert any(a["jurisdiction"] == "IN" for a in result["advisories"])

    def test_returns_fallback_for_unknown_typology(self, graph_service):
        result = graph_service.get_typology_context(["UnknownType"], jurisdiction="IN")
        assert result["advisories"] == []
        assert "flat vector" in result["evidence_text"].lower() or "no specific" in result["evidence_text"].lower()
        assert result["confidence_score"] <= 0.3

    def test_multiple_typologies_return_multiple_advisories(self, graph_service):
        result = graph_service.get_typology_context(
            ["Layering", "Structuring", "Hawala"], jurisdiction="IN"
        )
        assert len(result["advisories"]) >= 3
        typology_names = {a["typology"] for a in result["advisories"]}
        assert "Layering" in typology_names
        assert "Structuring" in typology_names
        assert "Hawala" in typology_names

    def test_uk_jurisdiction(self, graph_service):
        result = graph_service.get_typology_context(["Layering"], jurisdiction="UK")
        assert len(result["advisories"]) > 0
        assert any(a["jurisdiction"] == "UK" for a in result["advisories"])
        assert "NCA" in result["evidence_text"] or "JMLSG" in result["evidence_text"]

    def test_confidence_score_range(self, graph_service):
        result = graph_service.get_typology_context(["Hawala"], jurisdiction="IN")
        assert 0.0 <= result["confidence_score"] <= 1.0


# ─── analyze_relationships ───────────────────────────────────────────────────


class TestAnalyzeRelationships:
    def test_fallback_when_no_transactions(self, graph_service):
        result = graph_service.analyze_relationships("ACC-100")
        assert "ACC-100" in result["relationship_summary"]
        assert result["centrality_score"] == 0.0
        assert result["risk_amplification_factor"] == 1.0

    def test_detects_cycles_in_transaction_graph(self, graph_service, sample_transactions):
        """ACC-100 → ACC-300 → ACC-100 is a cycle."""
        result = graph_service.analyze_relationships(
            "ACC-100", transactions=sample_transactions
        )
        assert result["cycles_detected"] >= 1
        assert result["risk_amplification_factor"] > 1.0
        assert "cycle" in result["relationship_summary"].lower()

    def test_computes_centrality(self, graph_service, sample_transactions):
        result = graph_service.analyze_relationships(
            "ACC-100", transactions=sample_transactions
        )
        assert result["centrality_score"] >= 0.0
        assert result["num_components"] >= 1

    def test_no_cycles_in_linear_graph(self, graph_service):
        """A→B→C linear chain has no cycles for A."""
        linear_txns = [
            {"source_account": "A", "destination_account": "B", "amount": 1000},
            {"source_account": "B", "destination_account": "C", "amount": 1000},
        ]
        result = graph_service.analyze_relationships("A", transactions=linear_txns)
        assert result["cycles_detected"] == 0
        assert result["risk_amplification_factor"] == 1.0

    def test_empty_transactions(self, graph_service):
        result = graph_service.analyze_relationships("ACC-100", transactions=[])
        assert result["centrality_score"] == 0.0
