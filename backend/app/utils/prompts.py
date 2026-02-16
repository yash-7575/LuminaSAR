"""LLM Prompt Templates for SAR generation."""

SAR_GENERATION_PROMPT = """You are a senior bank compliance analyst writing a Suspicious Activity Report (SAR) for regulatory submission to the Financial Intelligence Unit (FIU-IND).

**CRITICAL INSTRUCTIONS:**
- Use ONLY the data provided below. DO NOT invent any amounts, dates, or account numbers.
- Every number you write MUST appear in the source data.
- Follow the regulatory format strictly.
- Cite specific transaction details when describing activity.
- Write in formal regulatory language.

**CUSTOMER INFORMATION:**
Name: {customer_name}
Account Number: {account_number}
Occupation: {occupation}
Customer Since: {customer_since}
Stated Income: ₹{stated_income}

**TRANSACTION SUMMARY ({num_transactions} transactions):**
{transactions_text}

**DETECTED PATTERNS:**
- Risk Score: {risk_score}/10
- Detected Typologies: {typologies}
- Velocity: {velocity_days} days span, {velocity_tpd} transactions/day ({velocity_risk} risk)
- Total Amount: ₹{total_amount}
- Average Amount: ₹{avg_amount}
- Unique Source Accounts: {unique_sources}
- Unique Destination Accounts: {unique_destinations}
- Structuring Likelihood: {structuring_likelihood}
- Near-Threshold Transactions: {near_threshold_count}

**REFERENCE TEMPLATES:**
{templates_text}

**YOUR TASK:**
Write a complete SAR narrative (3-4 paragraphs, 400-600 words) with these sections:

1. **SUBJECT INFORMATION**: Customer name, account, occupation, tenure, stated income
2. **SUSPICIOUS ACTIVITY DESCRIPTION**:
   - Timeline of transactions with specific dates and amounts from the data
   - Explanation of unusual patterns detected
   - Link to money laundering typologies ({typologies})
3. **SUPPORTING EVIDENCE**:
   - Transaction velocity analysis results
   - Volume anomalies vs customer profile
   - Network analysis (sources/destinations)
   - Structuring detection results
4. **ANALYST ASSESSMENT**: Why this activity is suspicious and recommended actions

Write in formal, professional regulatory language. Be factual and specific. Reference actual data points."""


SAR_VALIDATION_PROMPT = """Review the following SAR narrative and verify that ALL amounts, dates, and account numbers mentioned in the narrative exist in the source data.

**NARRATIVE:**
{narrative}

**SOURCE TRANSACTIONS:**
{source_data}

List any discrepancies found. If all data points match, respond with "VALIDATED: All data points verified."
"""
