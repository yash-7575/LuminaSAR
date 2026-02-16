"""Tests for the /api/v1/config endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestConfigEndpoint:
    def test_returns_200(self, client):
        response = client.get("/api/v1/config/")
        assert response.status_code == 200

    def test_response_has_required_fields(self, client):
        data = client.get("/api/v1/config/").json()
        assert "jurisdiction" in data
        assert "deployment_env" in data
        assert "supported_jurisdictions" in data

    def test_supported_jurisdictions_is_list(self, client):
        data = client.get("/api/v1/config/").json()
        assert isinstance(data["supported_jurisdictions"], list)
        assert len(data["supported_jurisdictions"]) == 8

    def test_all_expected_jurisdictions_present(self, client):
        data = client.get("/api/v1/config/").json()
        expected = {"IN", "US", "UK", "EU", "SG", "HK", "UAE", "AU"}
        assert set(data["supported_jurisdictions"]) == expected

    def test_jurisdiction_is_valid(self, client):
        data = client.get("/api/v1/config/").json()
        assert data["jurisdiction"] in data["supported_jurisdictions"]

    def test_deployment_env_is_string(self, client):
        data = client.get("/api/v1/config/").json()
        assert isinstance(data["deployment_env"], str)
        assert data["deployment_env"] in ("cloud", "on-prem", "hybrid")
