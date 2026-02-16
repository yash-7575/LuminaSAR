"""Shared pytest fixtures for LuminaSAR tests."""

import sys
import os

# Ensure backend/app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture
def sample_transactions():
    """Realistic sample transaction data for testing."""
    return [
        {
            "transaction_id": "txn-001-abc",
            "amount": 9500,
            "date": "2024-01-15",
            "source_account": "ACC-100",
            "destination_account": "ACC-200",
            "transaction_type": "wire",
        },
        {
            "transaction_id": "txn-002-def",
            "amount": 9800,
            "date": "2024-01-16",
            "source_account": "ACC-100",
            "destination_account": "ACC-300",
            "transaction_type": "wire",
        },
        {
            "transaction_id": "txn-003-ghi",
            "amount": 15000,
            "date": "2024-01-17",
            "source_account": "ACC-300",
            "destination_account": "ACC-100",
            "transaction_type": "wire",
        },
        {
            "transaction_id": "txn-004-jkl",
            "amount": 4500,
            "date": "2024-01-18",
            "source_account": "ACC-200",
            "destination_account": "ACC-400",
            "transaction_type": "cash",
        },
        {
            "transaction_id": "txn-005-mno",
            "amount": 25000,
            "date": "2024-01-19",
            "source_account": "ACC-400",
            "destination_account": "ACC-100",
            "transaction_type": "wire",
        },
    ]


@pytest.fixture
def sample_customer():
    """Sample customer data."""
    return {
        "customer_id": "cust-001",
        "name": "Test Customer",
        "account_number": "ACC-100",
        "occupation": "Business Owner",
        "stated_income": 500000,
        "customer_since": "2020-01-01",
    }
