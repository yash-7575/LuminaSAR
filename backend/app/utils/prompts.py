"""LLM Prompt Templates for SAR generation."""

JURISDICTION_CONTEXT = {
    "IN": {
        "regulatory_body": "Financial Intelligence Unit (FIU-IND)",
        "currency_symbol": "₹",
        "identity_name": "Aadhaar/PAN",
        "filing_threshold": "₹1,000,000",
        "legal_terminology": "Money Laundering (Prevention) Act (PMLA)",
        "reporting_form": "STR (Suspicious Transaction Report)",
        "sar_sections": [
            "Subject Information",
            "Suspicious Activity Description",
            "Supporting Evidence",
            "Analyst Assessment",
        ],
    },
    "US": {
        "regulatory_body": "Financial Crimes Enforcement Network (FinCEN)",
        "currency_symbol": "$",
        "identity_name": "SSN/EIN",
        "filing_threshold": "$10,000",
        "legal_terminology": "Bank Secrecy Act (BSA) / USA PATRIOT Act",
        "reporting_form": "FinCEN SAR Form",
        "sar_sections": [
            "Subject Information",
            "Suspicious Activity Information",
            "Narrative",
            "Filing Institution Contact",
        ],
    },
    "UK": {
        "regulatory_body": "National Crime Agency (NCA)",
        "currency_symbol": "£",
        "identity_name": "NI Number",
        "filing_threshold": "£10,000",
        "legal_terminology": "Proceeds of Crime Act 2002 (POCA) / JMLSG Guidance",
        "reporting_form": "SAR (Defence / Consent / Information)",
        "sar_sections": [
            "Subject Details",
            "Reason for Suspicion",
            "Transaction Details",
            "Reporting Officer Assessment",
        ],
    },
    "EU": {
        "regulatory_body": "EU Anti-Money Laundering Authority (AMLA)",
        "currency_symbol": "€",
        "identity_name": "National ID / Passport",
        "filing_threshold": "€15,000",
        "legal_terminology": "EU 6th Anti-Money Laundering Directive (6AMLD)",
        "reporting_form": "STR (Suspicious Transaction Report)",
        "sar_sections": [
            "Subject Identification",
            "Suspicious Activity Description",
            "Transaction Analysis",
            "Risk Assessment and Recommendation",
        ],
    },
    "SG": {
        "regulatory_body": "Suspicious Transaction Reporting Office (STRO)",
        "currency_symbol": "S$",
        "identity_name": "NRIC/FIN",
        "filing_threshold": "S$20,000",
        "legal_terminology": "Corruption, Drug Trafficking and Other Serious Crimes Act (CDSA)",
        "reporting_form": "STR (Suspicious Transaction Report)",
        "sar_sections": [
            "Subject Information",
            "Details of Suspicious Transaction",
            "Grounds for Suspicion",
            "Action Taken by Reporting Entity",
        ],
    },
    "HK": {
        "regulatory_body": "Joint Financial Intelligence Unit (JFIU)",
        "currency_symbol": "HK$",
        "identity_name": "HKID",
        "filing_threshold": "HK$120,000",
        "legal_terminology": "Anti-Money Laundering and Counter-Terrorist Financing Ordinance (AMLO)",
        "reporting_form": "STR (Suspicious Transaction Report)",
        "sar_sections": [
            "Subject Information",
            "Description of Suspicious Activity",
            "Supporting Transaction Data",
            "Reporting Officer Conclusion",
        ],
    },
    "UAE": {
        "regulatory_body": "UAE Financial Intelligence Unit (FIU)",
        "currency_symbol": "AED",
        "identity_name": "Emirates ID",
        "filing_threshold": "AED 55,000",
        "legal_terminology": "Federal Decree-Law No. 20 of 2018 (AML/CFT)",
        "reporting_form": "STR (Suspicious Transaction Report)",
        "sar_sections": [
            "Subject Identification",
            "Suspicious Activity Narrative",
            "Transaction Analysis",
            "Risk Classification and Recommendations",
        ],
    },
    "AU": {
        "regulatory_body": "Australian Transaction Reports and Analysis Centre (AUSTRAC)",
        "currency_symbol": "A$",
        "identity_name": "TFN/ABN",
        "filing_threshold": "A$10,000",
        "legal_terminology": "Anti-Money Laundering and Counter-Terrorism Financing Act 2006 (AML/CTF Act)",
        "reporting_form": "SMR (Suspicious Matter Report)",
        "sar_sections": [
            "Subject Information",
            "Suspicious Matter Description",
            "Supporting Transaction Details",
            "Reporting Entity Assessment",
        ],
    },
}

SAR_GENERATION_PROMPT = """You are a senior bank compliance analyst writing a Suspicious Activity Report (SAR) for regulatory submission to the {regulatory_body} in a {deployment_env} environment.

**CRITICAL INSTRUCTIONS:**
- Use ONLY the data provided below. DO NOT invent any amounts, dates, or account numbers.
- Every number you write MUST appear in the source data.
- Follow the regulatory format strictly for {jurisdiction} jurisdiction.
- Cite specific transaction details when describing activity.
- Write in formal regulatory language compliant with {legal_terminology}.
- Use {currency_symbol} for all financial amounts.
- This report will be filed using the {reporting_form}.

**CUSTOMER INFORMATION:**
Name: {customer_name}
Account Number: {account_number}
Occupation: {occupation}
Customer Since: {customer_since}
Stated Income: {currency_symbol}{stated_income}
Secondary ID ({identity_name}): Provided in KYC

**TRANSACTION SUMMARY ({num_transactions} transactions):**
{transactions_text}

**DETECTED PATTERNS:**
- Risk Score: {risk_score}/10
- Detected Typologies: {typologies}
- Velocity: {velocity_days} days span, {velocity_tpd} transactions/day ({velocity_risk} risk)
- Total Amount: {currency_symbol}{total_amount}
- Average Amount: {currency_symbol}{avg_amount}
- Unique Source Accounts: {unique_sources}
- Unique Destination Accounts: {unique_destinations}
- Structuring Likelihood: {structuring_likelihood}
- Near-Threshold Transactions: {near_threshold_count} (Filing threshold: {filing_threshold})

**KNOWLEDGE GRAPH EVIDENCE:**
{graph_evidence}

**REFERENCE TEMPLATES:**
{templates_text}

**YOUR TASK:**
Write a complete SAR narrative formatted with these jurisdictional sections required by {regulatory_body}:

{jurisdictional_sections}

**NARRATIVE REQUIREMENTS:**
- Length: 3-4 paragraphs, 400-600 words.
- Tone: Formal, professional regulatory language compliant with {legal_terminology}.
- Subjectivity: Explain why the activity is suspicious based on the source data.
- Knowledge Graph Insight: {graph_insight} Must be integrated into the relevant section.
- Thresholds: Reference the {filing_threshold} limit when discussing structuring.

Write in a factual and specific manner. Reference actual data points."""


SAR_VALIDATION_PROMPT = """Review the following SAR narrative and verify that ALL amounts, dates, and account numbers mentioned in the narrative exist in the source data.

**NARRATIVE:**
{narrative}

**SOURCE TRANSACTIONS:**
{source_data}

List any discrepancies found. If all data points match, respond with "VALIDATED: All data points verified."
"""
