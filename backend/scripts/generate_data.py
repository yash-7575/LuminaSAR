"""Synthetic data generator for LuminaSAR demo.

Generates realistic-looking:
- Customers with KYC data
- Transaction patterns with suspicious activity
- SAR cases ready for narrative generation

Run: python -m scripts.generate_data
"""

import uuid
import random
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try import, fall back to raw SQL
try:
    from supabase import create_client

    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    print("⚠️ supabase-py not found. Install with: pip install supabase")

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv(
    "SUPABASE_ANON_KEY", ""
)

# Indian names and occupations
FIRST_NAMES = [
    "Rajesh",
    "Priya",
    "Amit",
    "Sunita",
    "Vikram",
    "Ananya",
    "Arjun",
    "Deepa",
    "Rahul",
    "Kavita",
    "Sanjay",
    "Meera",
    "Rohit",
    "Neha",
    "Suresh",
]
LAST_NAMES = [
    "Sharma",
    "Patel",
    "Mehta",
    "Gupta",
    "Singh",
    "Reddy",
    "Joshi",
    "Desai",
    "Kumar",
    "Verma",
    "Chowdhury",
    "Nair",
    "Pandey",
    "Aggarwal",
    "Shah",
]
OCCUPATIONS = [
    "Business Owner",
    "Software Engineer",
    "Import-Export Dealer",
    "Real Estate Agent",
    "Jeweler",
    "Restaurant Owner",
    "Textile Trader",
    "Pharmaceutical Distributor",
    "Retired Government Official",
    "Self-Employed Consultant",
]
BANKS = [
    "State Bank of India",
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
    "Punjab National Bank",
    "Bank of Baroda",
    "Kotak Mahindra Bank",
    "IndusInd Bank",
]
CITIES = [
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Pune",
    "Ahmedabad",
]

TYPOLOGY_CONFIGS = {
    "structuring": {
        "description": "Multiple transactions just below ₹50,000 CTR threshold",
        "amount_range": (42000, 49900),
        "num_transactions": (15, 30),
        "time_span_days": 14,
    },
    "layering": {
        "description": "Rapid movement of funds through multiple accounts",
        "amount_range": (100000, 500000),
        "num_transactions": (20, 40),
        "time_span_days": 5,
    },
    "smurfing": {
        "description": "Multiple small deposits from many different sources",
        "amount_range": (5000, 30000),
        "num_transactions": (30, 60),
        "time_span_days": 10,
    },
    "integration": {
        "description": "Large value transfers appearing as legitimate business",
        "amount_range": (500000, 5000000),
        "num_transactions": (5, 15),
        "time_span_days": 30,
    },
}


def generate_account_number():
    return f"{random.choice(['SBI', 'HDFC', 'ICICI', 'AXIS'])}{random.randint(100000000, 999999999)}"


def generate_customer():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return {
        "customer_id": str(uuid.uuid4()),
        "name": f"{first} {last}",
        "account_number": generate_account_number(),
        "occupation": random.choice(OCCUPATIONS),
        "risk_rating": random.choice(["low", "medium", "high"]),
        "kyc_status": "verified",
        "address": f"{random.randint(1, 500)}, {random.choice(['MG Road', 'Anna Salai', 'Park Street', 'FC Road', 'Linking Road'])}, {random.choice(CITIES)}",
        "stated_income": random.choice(
            [300000, 500000, 800000, 1200000, 2000000, 5000000]
        ),
        "customer_since": (
            datetime.now() - timedelta(days=random.randint(365, 3650))
        ).strftime("%Y-%m-%d"),
    }


def generate_transactions(customer_id, typology="structuring"):
    config = TYPOLOGY_CONFIGS[typology]
    num_txns = random.randint(*config["num_transactions"])
    base_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))
    txns = []

    external_accounts = [
        generate_account_number() for _ in range(random.randint(3, 15))
    ]

    for i in range(num_txns):
        amount = round(random.uniform(*config["amount_range"]), 2)
        date = base_date - timedelta(
            days=random.randint(0, config["time_span_days"]),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        is_inbound = random.random() < 0.6  # 60% inbound

        txn = {
            "transaction_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "amount": amount,
            "currency": "INR",
            "transaction_type": random.choice(
                ["wire_transfer", "cash_deposit", "rtgs", "neft", "upi"]
            ),
            "source_account": random.choice(external_accounts)
            if is_inbound
            else "SELF",
            "destination_account": "SELF"
            if is_inbound
            else random.choice(external_accounts),
            "date": date.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "completed",
        }
        txns.append(txn)

    return txns


def generate_sar_case(customer_id, typologies):
    return {
        "case_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "status": "pending",
        "risk_score": None,
        "typologies": typologies,
    }


def main():
    print("🏗️  LuminaSAR — Generating Synthetic Data")
    print("=" * 50)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        print("   Falling back to JSON file output...")
        use_supabase = False
    else:
        use_supabase = HAS_SUPABASE

    all_data = {"customers": [], "transactions": [], "sar_cases": []}

    scenarios = [
        ("structuring", ["structuring"]),
        ("layering", ["layering"]),
        ("smurfing", ["smurfing"]),
        ("integration", ["integration"]),
        ("structuring", ["structuring", "layering"]),
    ]

    for typology, case_typologies in scenarios:
        customer = generate_customer()
        all_data["customers"].append(customer)
        print(f"\n👤 Customer: {customer['name']} ({customer['account_number']})")

        transactions = generate_transactions(customer["customer_id"], typology)
        all_data["transactions"].extend(transactions)
        print(f"   💳 {len(transactions)} transactions ({typology})")

        sar_case = generate_sar_case(customer["customer_id"], case_typologies)
        all_data["sar_cases"].append(sar_case)
        print(f"   📋 Case: {sar_case['case_id'][:8]}...")

    print("\n📤 Uploading to Database...")
    from app.database import SessionLocal
    from app.models.customer import Customer as CustomerModel
    from app.models.transaction import Transaction as TransactionModel
    from app.models.sar_case import SARCase as SARCaseModel

    db = SessionLocal()
    try:
        # Convert Pydantic-like dicts to SQLAlchemy models
        for cust_data in all_data["customers"]:
            # Handle possible field name differences (stated_income vs stated_income)
            customer = CustomerModel(
                customer_id=cust_data["customer_id"],
                name=cust_data["name"],
                account_number=cust_data["account_number"],
                occupation=cust_data["occupation"],
                stated_income=cust_data["stated_income"],
                customer_since=datetime.strptime(
                    cust_data["customer_since"], "%Y-%m-%d"
                ),
            )
            db.merge(customer)
        print(f"   ✅ {len(all_data['customers'])} customers")

        for txn_data in all_data["transactions"]:
            transaction = TransactionModel(
                transaction_id=txn_data["transaction_id"],
                customer_id=txn_data["customer_id"],
                amount=txn_data["amount"],
                date=datetime.strptime(txn_data["date"], "%Y-%m-%dT%H:%M:%S"),
                source_account=txn_data["source_account"],
                destination_account=txn_data["destination_account"],
                transaction_type=txn_data["transaction_type"],
            )
            db.merge(transaction)
        print(f"   ✅ {len(all_data['transactions'])} transactions")

        for case_data in all_data["sar_cases"]:
            sar_case = SARCaseModel(
                case_id=case_data["case_id"],
                customer_id=case_data["customer_id"],
                status=case_data["status"],
                risk_score=case_data["risk_score"],
                typologies=case_data["typologies"],
            )
            db.merge(sar_case)
        print(f"   ✅ {len(all_data['sar_cases'])} SAR cases")

        db.commit()
    except Exception as e:
        print(f"❌ Database error: {e}")
        db.rollback()
    finally:
        db.close()

    print(f"\n{'=' * 50}")
    print("✨ Data generation complete!")
    print(f"   Customers: {len(all_data['customers'])}")
    print(f"   Transactions: {len(all_data['transactions'])}")
    print(f"   SAR Cases: {len(all_data['sar_cases'])}")
    print(f"\n📋 Case IDs for testing:")
    for case in all_data["sar_cases"]:
        print(f"   {case['case_id']}")


if __name__ == "__main__":
    main()
