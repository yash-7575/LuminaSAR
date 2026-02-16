# 🔆 LuminaSAR — Complete Project Brief

> **SAR Narrative Generator with Explainable AI Audit Trail**
>
> Barclays Hack-O-Hire 2026

---

## Table of Contents

1. [What is a SAR & Why Automate It?](#1-what-is-a-sar--why-automate-it)
2. [Project Overview](#2-project-overview)
3. [High-Level Architecture Diagram](#3-high-level-architecture-diagram)
4. [Detailed Data Flow — End to End](#4-detailed-data-flow--end-to-end)
5. [Backend Deep Dive — FastAPI](#5-backend-deep-dive--fastapi)
6. [Database Schema & How It Was Built](#6-database-schema--how-it-was-built)
7. [The 6-Step AI Pipeline — LangGraph](#7-the-6-step-ai-pipeline--langgraph)
8. [How Pattern Detection (ML) Works](#8-how-pattern-detection-ml-works)
9. [How RAG Works — ChromaDB + Sentence-Transformers](#9-how-rag-works--chromadb--sentence-transformers)
10. [How Ollama Generates Text — LLM Integration](#10-how-ollama-generates-text--llm-integration)
11. [The Anti-Hallucination Validator](#11-the-anti-hallucination-validator)
12. [Hash-Chained Audit Trail — The Innovation](#12-hash-chained-audit-trail--the-innovation)
13. [Frontend — React + TypeScript](#13-frontend--react--typescript)
14. [How Frontend Fetches Data from Backend](#14-how-frontend-fetches-data-from-backend)
15. [Docker & Deployment](#15-docker--deployment)
16. [What I Built & In What Order](#16-what-i-built--in-what-order)
17. [Essential Topics to Learn](#17-essential-topics-to-learn)
18. [Similar Project Ideas](#18-similar-project-ideas)

---

## 1. What is a SAR & Why Automate It?

A **Suspicious Activity Report (SAR)** is a regulatory document that banks must file with the Financial Intelligence Unit (FIU) whenever they detect potentially fraudulent or money-laundering transactions. Banks like Barclays file **thousands of SARs per year**.

### The Problem

| Manual Process | LuminaSAR |
|---|---|
| 5-6 hours per SAR | ~30 seconds |
| Human error in data citation | 100% data-grounded |
| No audit trail of reasoning | Full hash-chained audit trail |
| Black-box decisions | Sentence-level explainability |

**Key Point**: A compliance analyst currently reads through hundreds of transactions, identifies suspicious patterns, writes a formal regulatory narrative, and cites specific data points. This is tedious, error-prone, and expensive. Our AI does it in 30 seconds with full transparency.

---

## 2. Project Overview

LuminaSAR is a **full-stack GenAI application** with three major layers:

```
┌──────────────────────────────────────────────────────────────┐
│                       USER (Browser)                         │
│          Dashboard → Generate SAR → View Report              │
├──────────────────────────────────────────────────────────────┤
│                   FRONTEND (React + TS)                      │
│   Vite │ TailwindCSS │ React Query │ Zustand │ Framer Motion │
├──────────────────────────────────────────────────────────────┤
│                     REST API (HTTPS)                         │
│      axios.post("http://localhost:8000/api/v1/sar/...")      │
├──────────────────────────────────────────────────────────────┤
│                   BACKEND (FastAPI)                           │
│   Routes → Schemas (Pydantic) → Services → Models (ORM)     │
├──────────────────────────────────────────────────────────────┤
│                      AI / ML Layer                           │
│   Pattern Detection │ RAG │ LLM (Ollama) │ Validation        │
├──────────────────────────────────────────────────────────────┤
│                      DATA LAYER                              │
│   Supabase PostgreSQL / SQLite │ ChromaDB (Vector DB)        │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. High-Level Architecture Diagram

```
                           ┌────────────────┐
                           │    User's       │
                           │    Browser      │
                           │  (React App)    │
                           └──────┬─────────┘
                                  │ HTTP Requests (axios)
                                  │ GET/POST to localhost:8000
                                  ▼
                    ┌─────────────────────────────┐
                    │        FastAPI Backend       │
                    │     (localhost:8000)          │
                    │                              │
                    │  GET /health                  │
                    │  POST /api/v1/sar/generate    │
                    │  GET  /api/v1/sar/{id}        │
                    │  GET  /api/v1/sar/{id}/audit  │
                    │  GET  /api/v1/sar/stats       │
                    └──────┬──────────────┬────────┘
                           │              │
                    ┌──────▼──────┐ ┌─────▼─────────┐
                    │  SQLAlchemy │ │   LangGraph    │
                    │  ORM Layer  │ │   Workflow     │
                    │  (models/)  │ │  (6 steps)     │
                    └──────┬──────┘ └─────┬─────────┘
                           │              │
                    ┌──────▼──────┐       │
                    │  Database   │       ├──→ PatternDetector (ML)
                    │  Supabase   │       │     └─ pandas, numpy, networkx
                    │  PostgreSQL │       │
                    │     OR      │       ├──→ RAGService
                    │  SQLite     │       │     └─ ChromaDB + sentence-transformers
                    │  (fallback) │       │
                    └─────────────┘       ├──→ LLMService
                                          │     └─ Ollama HTTP API (llama3.2)
                                          │
                                          ├──→ NarrativeValidator
                                          │     └─ Anti-hallucination checks
                                          │
                                          └──→ AuditLogger
                                                └─ SHA-256 hash chain
```

### Component Interaction Sequence

```
   Frontend                Backend                    AI Services
      │                       │                            │
      │  POST /generate       │                            │
      │  {case_id}            │                            │
      ├──────────────────────→│                            │
      │                       │ 1. Fetch customer + txns   │
      │                       │    from DB                 │
      │                       │                            │
      │                       │ 2. PatternDetector.analyze │
      │                       │────────────────────────────→
      │                       │    velocity, volume,       │
      │                       │    structuring, network    │
      │                       │←────────────────────────────
      │                       │                            │
      │                       │ 3. RAGService.retrieve     │
      │                       │────────────────────────────→
      │                       │    ChromaDB semantic search │
      │                       │←────────────────────────────
      │                       │                            │
      │                       │ 4. LLMService.generate     │
      │                       │────────────────────────────→
      │                       │    HTTP POST to Ollama      │
      │                       │    localhost:11434           │
      │                       │←────────────────────────────
      │                       │                            │
      │                       │ 5. Validate narrative      │
      │                       │ 6. Save + audit trail      │
      │                       │                            │
      │  {narrative, audit}   │                            │
      │←──────────────────────│                            │
      │                       │                            │
```

---

## 4. Detailed Data Flow — End to End

Here's exactly what happens when a user clicks **"Generate SAR"**:

### 🖱️ Step 1: User Clicks "Generate" in the Browser

The React frontend (`GenerateSAR.tsx`) collects the `case_id` from the input field and calls:

```typescript
// frontend/src/services/api.ts
const response = await apiClient.post('/api/v1/sar/generate', {
    case_id: "b920a3c4-dccc-44ce-9ebb-9866edcec4dd"
})
```

This is an HTTP POST request from React (port 5173) → FastAPI (port 8000).

### ⚡ Step 2: FastAPI Receives the Request

The backend route handler in `backend/app/routes/sar.py`:

```python
@router.post("/generate")
async def generate_sar(request: GenerateSARRequest, db: Session = Depends(get_db)):
    result = await run_sar_workflow(case.case_id, case.customer_id, db)
```

FastAPI:
- Validates the request with Pydantic (`GenerateSARRequest`)
- Injects a database session via `Depends(get_db)`
- Calls the LangGraph workflow

### 🔄 Step 3: LangGraph Runs 6 Pipeline Steps

The `langgraph_workflow.py` orchestrates everything. Each step reads the `SARState` dict, does its work, and passes it to the next step. Every step logs to the `AuditLogger`.

### 📤 Step 4: Response Goes Back to React

The backend returns a JSON response:

```json
{
    "narrative_id": "abc-123",
    "narrative_text": "SUSPICIOUS ACTIVITY REPORT...",
    "risk_score": 4.5,
    "typologies": ["structuring", "layering"],
    "generation_time_seconds": 34,
    "audit_steps": 6
}
```

React then navigates the user to the **SAREditor** page to view and interact with the narrative.

---

## 5. Backend Deep Dive — FastAPI

### Why FastAPI?

FastAPI was chosen because:

1. **Async support** — LLM calls take 20-30 seconds; async lets us handle multiple requests
2. **Pydantic integration** — Automatic request/response validation and OpenAPI docs
3. **Dependency Injection** — `Depends(get_db)` cleanly provides database sessions
4. **Auto-generated docs** — Swagger UI at `/docs` for free

### How the Backend is Organized

```
backend/
├── app/
│   ├── main.py           ← FastAPI app creation + CORS + router includes
│   ├── config.py          ← Pydantic Settings loading from .env
│   ├── database.py        ← SQLAlchemy engine + session factory
│   ├── models/            ← ORM models (database tables)
│   ├── schemas/           ← Pydantic models (API request/response shapes)
│   ├── routes/            ← API endpoint handlers
│   ├── services/          ← Business logic (AI/ML services)
│   └── utils/             ← Helper functions (hash, prompts)
```

### Key Concepts Used

**1. CORS Middleware** (`main.py`):
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
```
This allows the React frontend (different port 5173) to talk to the backend (port 8000). Without CORS, the browser blocks cross-origin requests.

**2. Dependency Injection** (`database.py`):
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
Every route that needs the database declares `db: Session = Depends(get_db)`. FastAPI automatically creates a session, gives it to the route, and closes it after the request.

**3. Pydantic Validation** (`schemas/request.py`):
```python
class GenerateSARRequest(BaseModel):
    case_id: str
    force_regenerate: bool = False
```
If anyone sends invalid data (e.g., missing `case_id`), FastAPI automatically returns a 422 error with detailed validation messages.

---

## 6. Database Schema & How It Was Built

### Schema Diagram

```
┌──────────────────┐     ┌──────────────────┐
│    customers     │     │   transactions   │
├──────────────────┤     ├──────────────────┤
│ customer_id (PK) │←────│ customer_id (FK) │
│ name             │     │ transaction_id   │
│ account_number   │     │ amount           │
│ occupation       │     │ date             │
│ stated_income    │     │ source_account   │
│ customer_since   │     │ dest_account     │
└────────┬─────────┘     │ transaction_type │
         │               └──────────────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│    sar_cases     │     │  sar_narratives  │
├──────────────────┤     ├──────────────────┤
│ case_id (PK)     │←────│ case_id (FK)     │
│ customer_id (FK) │     │ narrative_id (PK)│──┐
│ status           │     │ narrative_text   │  │
│ risk_score       │     │ generated_at     │  │
│ typologies (JSON)│     │ gen_time_seconds │  │
│ created_at       │     └──────────────────┘  │
└──────────────────┘                            │
                                                │
                         ┌──────────────────┐   │
                         │   audit_trail    │   │
                         ├──────────────────┤   │
                         │ audit_id (PK)    │   │
                         │ narrative_id (FK)│←──┘
                         │ step_name        │
                         │ data_sources JSON│
                         │ reasoning JSON   │
                         │ confidence JSON  │
                         │ previous_hash    │ ← SHA-256 chain
                         │ current_hash     │ ← SHA-256 chain
                         │ logged_at        │
                         └──────────────────┘
```

### How the Tables Connect

1. A **Customer** has many **Transactions** (1-to-many via `customer_id`)
2. A **Customer** has many **SAR Cases** (when suspicious activity is flagged)
3. A **SAR Case** can have one **SAR Narrative** (the AI-generated report)
4. A **SAR Narrative** has many **Audit Trail** entries (one per pipeline step)

### How SQLAlchemy Models Work

Each Python class maps to a database table:

```python
# backend/app/models/customer.py
class Customer(Base):
    __tablename__ = "customers"
    customer_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ...
```

When SQLAlchemy runs a query like `db.query(Customer).filter(...)`, it translates it to SQL:

```sql
SELECT * FROM customers WHERE customer_id = 'abc-123';
```

### Dual Database Strategy

The `database.py` file implements a smart fallback:

```
1. Try connecting to Supabase PostgreSQL (cloud database)
2. If that fails (DNS error, auth error, etc.)
   → Automatically create a local SQLite file (luminasar.db)
   → Create all tables in SQLite
   → App runs perfectly on SQLite
```

This means the app works anywhere — with internet (Supabase) or without (SQLite).

---

## 7. The 6-Step AI Pipeline — LangGraph

The heart of LuminaSAR is the **6-step AI pipeline** in `langgraph_workflow.py`. It uses a TypedDict called `SARState` that flows through every step:

```python
class SARState(TypedDict):
    case_id: str
    customer_id: str
    customer_data: Dict        # Filled by Step 1
    transactions: List[Dict]   # Filled by Step 1
    patterns: Dict             # Filled by Step 2
    typologies: List[str]      # Filled by Step 2
    templates: List[str]       # Filled by Step 3
    narrative: str             # Filled by Step 4
    audit_logs: List[Dict]     # Appended by every step
    risk_score: float          # Filled by Step 2
    narrative_id: str          # Filled by Step 6
    error: Optional[str]       # Set if any step fails
```

### The Pipeline Flow

```
┌─────────────────┐
│  STEP 1: FETCH  │  Query database for customer KYC + transaction records
│  _fetch_data()  │  → Fills: customer_data, transactions
└────────┬────────┘
         ▼
┌────────────────────┐
│  STEP 2: ANALYZE   │  Run 4 ML algorithms on transactions DataFrame
│  _analyze_patterns │  → Fills: patterns, typologies, risk_score
└────────┬───────────┘
         ▼
┌────────────────────────┐
│  STEP 3: RAG RETRIEVE  │  Search ChromaDB for relevant SAR templates
│  _retrieve_templates   │  → Fills: templates
└────────┬───────────────┘
         ▼
┌──────────────────────┐
│  STEP 4: GENERATE    │  Send prompt to Ollama llama3.2 model
│  _generate_narrative │  → Fills: narrative (400-600 words)
└────────┬─────────────┘
         ▼
┌──────────────────────┐
│  STEP 5: VALIDATE    │  Cross-check narrative vs source data
│  _validate()         │  → Checks for hallucinated amounts/dates
└────────┬─────────────┘
         ▼
┌──────────────────────┐
│  STEP 6: SAVE        │  Persist narrative + audit trail to database
│  _save_results()     │  → Fills: narrative_id, commits to DB
└──────────────────────┘
```

### Why LangGraph?

LangGraph (from LangChain) provides:
- **Stateful workflows** — the `SARState` dict is passed between steps
- **Error propagation** — if any step sets `state["error"]`, the pipeline stops
- **Composability** — steps can be added, removed, or reordered easily

---

## 8. How Pattern Detection (ML) Works

The `PatternDetector` class in `pattern_detector.py` runs **4 independent ML/statistical algorithms** on a Pandas DataFrame of transactions:

### Algorithm 1: Velocity Analysis

**What it detects**: Money moving suspiciously fast (many transactions in few days).

```
Example:
  50 transactions in 3 days → HIGH risk
  50 transactions in 60 days → LOW risk
```

**How it works**:
```python
time_span = (max_date - min_date).days
transactions_per_day = len(df) / max(time_span, 1)
# < 7 days = HIGH, < 30 days = MEDIUM, else LOW
```

### Algorithm 2: Volume Analysis

**What it detects**: Unusually large total amounts being moved.

```python
total_amount = df["amount"].sum()
avg_amount = df["amount"].mean()
max_amount = df["amount"].max()
```

Total above ₹1 Crore = very suspicious. Average amount much higher than stated income = suspicious.

### Algorithm 3: Structuring Detection

**What it detects**: Transactions deliberately kept just below ₹50,000 (the CTR reporting threshold in India).

```
Example:
  ₹49,000, ₹48,500, ₹49,900 → Structuring detected!
  (Someone is splitting a large transfer into amounts below ₹50K to avoid automatic reporting)
```

**How it works**:
```python
threshold = 50000  # INR CTR threshold
# Find transactions between 90-100% of threshold (₹45,000 - ₹49,999)
near_threshold = amounts[(amounts >= threshold * 0.90) & (amounts < threshold)]
structuring_likelihood = len(near_threshold) / len(amounts)
```

If more than 30% of transactions are near-threshold → structuring is flagged.

### Algorithm 4: Network Graph Analysis (NetworkX)

**What it detects**: Suspicious account-to-account relationships.

```
Example: If 25 different source accounts all send money to the SAME
destination account → "Smurfing" (many small deposits to evade detection)
```

**How it works**:
1. Build a **directed graph** where nodes = account numbers and edges = transactions
2. Calculate **degree centrality** — accounts that connect to many others are "hubs"
3. Detect **fan-in** (many sources → 1 destination) and **fan-out** (1 source → many destinations)

```python
import networkx as nx
G = nx.DiGraph()
G.add_edge(source_account, dest_account, amount=amt)
centrality = nx.degree_centrality(G)
```

### Typology Matching

After all 4 algorithms run, the results are matched against 6 money laundering typologies:

| Typology | Detection Rule |
|---|---|
| **Layering** | Rapid movement (< 7 days) + many distinct sources |
| **Structuring** | > 30% of transactions near ₹50K threshold |
| **Smurfing** | > 15 unique source accounts feeding one destination |
| **Integration** | > ₹50 Lakh in < 14 days |
| **Round-tripping** | High fan-in AND high fan-out |
| **Funnel Account** | High hub centrality in network graph |

### Risk Score Calculation

The risk score (0-10) is a weighted sum:
- Velocity: 0-30 points
- Volume: 0-25 points
- Structuring: 0-25 points
- Network: 0-20 points
- Total `/10` and capped at 10.0

---

## 9. How RAG Works — ChromaDB + Sentence-Transformers

### What is RAG?

**RAG = Retrieval-Augmented Generation**. Instead of asking the LLM to generate text from scratch, we first *retrieve* relevant reference documents and include them in the prompt. This:

1. **Improves quality** — The LLM has examples to follow
2. **Reduces hallucination** — The LLM is grounded in real templates
3. **Enables specialization** — Different templates for different crime types

### How Our RAG Pipeline Works

```
                        ┌──────────────────────────────┐
                        │   SAR Template Files (.txt)   │
                        │   sar_structuring.txt         │
                        │   sar_layering.txt            │
                        │   sar_smurfing.txt            │
                        │   sar_integration.txt         │
                        └────────────┬─────────────────┘
                                     │  Load templates
                                     ▼
                        ┌──────────────────────────────┐
                        │   Sentence-Transformers      │
                        │   Model: all-MiniLM-L6-v2    │
                        │   Converts text → 384-dim    │
                        │   vector embedding           │
                        └────────────┬─────────────────┘
                                     │  Store embeddings
                                     ▼
                        ┌──────────────────────────────┐
                        │        ChromaDB              │
                        │   Collection: sar_templates  │
                        │   Stores: text + embedding   │
                        │   + metadata (typology, src) │
                        └────────────┬─────────────────┘
                                     │
                         ┌───────────┴──────────────┐
                         │   AT QUERY TIME:          │
                         │   1. Detected typologies  │
                         │      ["structuring"]      │
                         │   2. Create query text    │
                         │   3. Encode to embedding  │
                         │   4. Similarity search    │
                         │   5. Return top-k matches │
                         └──────────────────────────┘
```

### Step-by-Step RAG Flow

**Step A: Loading Templates (Happens on Startup)**

```python
# rag_service.py → load_templates()
1. Read all .txt files from backend/data/templates/
2. For each file:
   a. Read the content
   b. Extract the typology from the filename (e.g., "sar_layering.txt" → "layering")
   c. Encode the text to a 384-dimensional vector using sentence-transformers
   d. Store in ChromaDB: {document: text, embedding: vector, metadata: {typology, source}}
```

**Step B: Retrieving Templates (During SAR Generation)**

```python
# rag_service.py → retrieve_templates(typologies=["structuring", "layering"])
1. Build a query string: "SAR narrative for structuring, layering money laundering"
2. Encode the query to a 384-dimensional vector
3. ChromaDB performs cosine similarity search against all stored template embeddings
4. Return top 3 most similar templates
```

### What are Embeddings (Simplified)?

An embedding is a list of numbers that represents the "meaning" of text:

```
"money laundering structuring" → [0.12, -0.45, 0.78, ..., 0.33]  (384 numbers)
"transactions below threshold" → [0.15, -0.42, 0.75, ..., 0.30]  (similar numbers!)
"cat sitting on mat"           → [-0.8, 0.61, -0.22, ..., 0.99]  (very different!)
```

ChromaDB uses **cosine similarity** to find which stored templates are most similar to the query. Templates about structuring will rank highest when the detected typology is structuring.

---

## 10. How Ollama Generates Text — LLM Integration

### What is Ollama?

Ollama is a **local LLM runtime** — it runs AI language models (like llama3.2) entirely on your computer. No API keys, no cloud, no data leakage.

### How We Connect to Ollama

The connection is simple — Ollama exposes a **REST API** on `http://localhost:11434`:

```python
# llm_service.py → generate_narrative()

async with httpx.AsyncClient(timeout=120.0) as client:
    response = await client.post(
        "http://localhost:11434/api/generate",  # Ollama's API endpoint
        json={
            "model": "llama3.2:latest",
            "prompt": prompt,                    # Our constructed prompt
            "stream": False,                     # Wait for complete response
            "options": {
                "temperature": 0.3,              # Low = more factual, less creative
                "num_predict": 2000,             # Max output tokens
                "top_p": 0.9,                    # Nucleus sampling
            },
        },
    )
```

### The Prompt Engineering

The magic is in **how we construct the prompt** (`utils/prompts.py`). The prompt includes:

```
╔════════════════════════════════════════════╗
║  SYSTEM INSTRUCTION                        ║
║  "You are a senior bank compliance analyst ║
║   writing a SAR for FIU-IND..."            ║
║                                            ║
║  CRITICAL: Use ONLY the data below.        ║
║  DO NOT invent amounts or dates.           ║
╠════════════════════════════════════════════╣
║  CUSTOMER DATA (from database)             ║
║  Name: Rajesh Malhotra                     ║
║  Account: HDFC203847591                    ║
║  Occupation: Import/Export Business         ║
║  Income: ₹12,00,000                        ║
╠════════════════════════════════════════════╣
║  TRANSACTIONS (from database)              ║
║  - ₹49,000 on 2026-01-15 from HDFC → BOB  ║
║  - ₹48,500 on 2026-01-16 from HDFC → SBI  ║
║  ... (up to 25 transactions)               ║
╠════════════════════════════════════════════╣
║  DETECTED PATTERNS (from PatternDetector)  ║
║  Risk Score: 6.5/10                        ║
║  Typologies: structuring, layering         ║
║  Velocity: 14 days, 3.5 txn/day           ║
║  Structuring Likelihood: 45.0%             ║
╠════════════════════════════════════════════╣
║  REFERENCE TEMPLATES (from RAG/ChromaDB)   ║
║  [Retrieved SAR template about structuring] ║
╠════════════════════════════════════════════╣
║  YOUR TASK:                                ║
║  Write a 400-600 word SAR narrative with:  ║
║  1. Subject Information                    ║
║  2. Suspicious Activity Description        ║
║  3. Supporting Evidence                    ║
║  4. Analyst Assessment                     ║
╚════════════════════════════════════════════╝
```

### Why Temperature 0.3?

| Temperature | Effect |
|---|---|
| 0.0 | Completely deterministic, always picks most likely token |
| 0.3 | Mostly factual, slight variation in wording ← **We use this** |
| 0.7 | Balanced creativity and accuracy |
| 1.0 | Very creative, more hallucination risk |

For compliance documents, we want **factual accuracy over creativity**, hence 0.3.

---

## 11. The Anti-Hallucination Validator

After the LLM generates text, we run **two validation passes** before saving:

### Pass 1: Structural Validator (`validator.py`)

```python
class NarrativeValidator:
    def validate(self, narrative, transactions, customer):
        # 1. Is the customer's name mentioned?
        # 2. Is the account number referenced?
        # 3. Is the narrative at least 100 words?
        # 4. Does it contain generic AI responses ("As an AI...")?
        # 5. Does it have SAR structure keywords ("suspicious", "transaction")?
```

### Pass 2: Amount Cross-Reference (`llm_service.py`)

```python
def validate_narrative(self, narrative, source_data):
    # 1. Extract all ₹ amounts from the narrative using regex
    # 2. Extract all transaction amounts from source data
    # 3. Check if every amount in the narrative exists in source data
    # 4. Flag any amount > ₹1,000 that doesn't match source data
```

This catches hallucination like:
- ❌ LLM says "₹5,75,000 was transferred" but no such amount exists in data
- ✅ LLM says "₹49,000 was transferred" and ₹49,000 exists in transactions

---

## 12. Hash-Chained Audit Trail — The Innovation

This is the **key differentiator** of LuminaSAR — every step of the AI pipeline is logged with a **SHA-256 hash chain**, similar to how blockchain works.

### How the Hash Chain Works

```
┌──────────────────────────────────────────────────────────┐
│  STEP 1: fetch_data                                       │
│  data_sources: {customer_id: "abc", database: "supabase"} │
│  reasoning: {action: "Fetched KYC data", customer: "..."}│
│  confidence: 1.0                                          │
│  previous_hash: "0000...0000" (genesis hash)              │
│  current_hash: SHA256(all above fields) = "a3f7..."       │
├──────────────────────────────────────────────────────────┤
│  STEP 2: analyze_patterns                                 │
│  data_sources: {transaction_ids, algorithms}               │
│  reasoning: {velocity, structuring, network}               │
│  confidence: 0.92                                          │
│  previous_hash: "a3f7..." ← links to Step 1!             │
│  current_hash: SHA256(all above) = "e8b2..."              │
├──────────────────────────────────────────────────────────┤
│  STEP 3: retrieve_templates                               │
│  previous_hash: "e8b2..." ← links to Step 2!             │
│  current_hash: "c4d1..."                                  │
├──────────────────────────────────────────────────────────┤
│  ... and so on for all 6 steps                            │
└──────────────────────────────────────────────────────────┘
```

### Why Hash Chains?

Each step's `current_hash` is computed from ALL its data + the `previous_hash`. This means:

1. **Tamper-evident** — If anyone modifies a step's data, its hash changes, breaking the chain
2. **Ordered** — You can verify the exact sequence of AI decisions
3. **Regulatory-compliant** — Auditors can independently verify that no step was altered

### Verification

```python
def verify_chain(self) -> bool:
    for i in range(1, len(self.logs)):
        # Check chain link
        if self.logs[i]["previous_hash"] != self.logs[i-1]["current_hash"]:
            return False  # Chain is broken!
        # Recompute hash to verify integrity
        expected = compute_hash(self.logs[i], exclude_keys=["current_hash"])
        if self.logs[i]["current_hash"] != expected:
            return False  # Data was tampered!
    return True
```

### Sentence-Level Attribution

The `create_sentence_attribution()` method maps **each sentence** in the narrative back to specific transactions:

```python
# For each sentence in the narrative:
#   - Check if any transaction ID appears in it
#   - Check if any transaction amount appears in it
#   - Check if any account number appears in it
#   - Record which data points were referenced
```

This powers the **click-to-audit** feature in the frontend — analysts click a sentence and see exactly which transactions informed it.

---

## 13. Frontend — React + TypeScript

### Tech Stack

| Library | Purpose |
|---|---|
| **React 18** | UI component library |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Fast build tool (replaces Webpack) |
| **TailwindCSS** | Utility-first CSS framework |
| **React Query** (@tanstack/react-query) | Server state management (API caching) |
| **Zustand** | Client state management |
| **Framer Motion** | Smooth animations |
| **Lucide React** | Icon library |
| **React Router DOM** | Client-side routing |

### Page Structure

```
App.tsx  (Router)
  ├── /          → Dashboard.tsx    (Stats, recent cases, "New SAR" button)
  ├── /generate  → GenerateSAR.tsx  (Case ID input, 6-step progress animation)
  └── /editor/:id → SAREditor.tsx   (Narrative viewer + audit trail panel)
```

### Dashboard (`Dashboard.tsx`)

- Fetches statistics from `GET /api/v1/sar/stats/overview`
- Shows 6 glassmorphism stat cards (total SARs, pending cases, avg time, etc.)
- Fetches recent cases from `GET /api/v1/sar/`
- Displays a table with case status, risk scores, and typology badges

### Generate SAR (`GenerateSAR.tsx`)

- Input field for Case ID
- On submit: calls `POST /api/v1/sar/generate`
- Shows a **6-step progress animation** while waiting (fetch → analyze → retrieve → generate → validate → save)
- On completion: navigates to `/editor/{narrative_id}`

### SAR Editor (`SAREditor.tsx`)

- Fetches narrative from `GET /api/v1/sar/{id}`
- Fetches audit trail from `GET /api/v1/sar/{id}/audit`
- Displays the narrative with **clickable sentences**
- On sentence click: opens an audit panel showing data sources and reasoning
- Approve button calls `POST /api/v1/sar/{id}/approve`

---

## 14. How Frontend Fetches Data from Backend

### The API Client

All backend calls go through a centralized Axios client (`frontend/src/services/api.ts`):

```typescript
const apiClient = axios.create({
    baseURL: 'http://localhost:8000',
    timeout: 180000,  // 3 minutes (for LLM generation)
    headers: { 'Content-Type': 'application/json' },
})
```

### TypeScript Interfaces

We define the exact shape of API responses:

```typescript
export interface DashboardStats {
    total_sars: number
    pending_cases: number
    avg_generation_time: number
    ...
}
```

This means TypeScript will catch errors at compile time if the backend response doesn't match.

### API Methods

```typescript
export const api = {
    health:        () => apiClient.get('/health'),
    generateSAR:   (data) => apiClient.post('/api/v1/sar/generate', data),
    getNarrative:  (id) => apiClient.get(`/api/v1/sar/${id}`),
    getAuditTrail: (id) => apiClient.get(`/api/v1/sar/${id}/audit`),
    approveSAR:    (id) => apiClient.post(`/api/v1/sar/${id}/approve`),
    getStats:      () => apiClient.get('/api/v1/sar/stats/overview'),
    getRecentCases:() => apiClient.get('/api/v1/sar/'),
}
```

### How React Calls These

In a page component (e.g., `Dashboard.tsx`):

```tsx
const [stats, setStats] = useState<DashboardStats | null>(null)

useEffect(() => {
    const fetchStats = async () => {
        const data = await api.getStats()
        setStats(data)
    }
    fetchStats()
}, [])
```

React's `useEffect` hook runs on component mount, calls the API, and stores the result in state. The component then re-renders with the data.

---

## 15. Docker & Deployment

### Docker Compose Architecture

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend    # Uses backend/Dockerfile
    ports: 8000:8000    # Expose API
    env_file: .env      # Load environment variables
    environment:
      OLLAMA_HOST: http://host.docker.internal:11434  # Connect to host's Ollama

  frontend:
    build: ./frontend   # Uses frontend/Dockerfile (multi-stage)
    ports: 3000:80      # Nginx serves on port 3000
    depends_on: backend # Start after backend
```

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim       # Small Python image
RUN apt-get install gcc libpq-dev  # PostgreSQL client library
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile (Multi-Stage Build)

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
RUN npm install
RUN npm run build         # Creates optimized production bundle

# Stage 2: Serve
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]
```

The multi-stage build means the final image only contains the compiled HTML/JS/CSS (a few MB), not the node_modules (hundreds of MB).

---

## 16. What I Built & In What Order

Here's the chronological development story:

| # | Phase | What Was Done |
|---|---|---|
| 1 | **Project Setup** | Created `.gitignore`, repo structure, and initial README |
| 2 | **Backend Core** | Set up FastAPI app, Pydantic Settings, SQLAlchemy database connection |
| 3 | **Database Models** | Created 5 SQLAlchemy ORM models (Customer, Transaction, SARCase, SARNarrative, AuditTrail) |
| 4 | **API Schemas** | Wrote Pydantic request/response schemas for type-safe API |
| 5 | **API Routes** | Implemented all FastAPI endpoints (health, generate, get, audit, approve, stats) |
| 6 | **ML Pattern Detection** | Built 4 detection algorithms (velocity, volume, structuring, network) + typology matching + risk scoring |
| 7 | **RAG Service** | Integrated ChromaDB + sentence-transformers for SAR template retrieval |
| 8 | **LLM Integration** | Connected to Ollama via HTTP, built grounded prompt templates with anti-hallucination instructions |
| 9 | **Audit Logger** | Implemented SHA-256 hash-chained audit trail with sentence-level attribution |
| 10 | **Validator** | Built narrative validator to cross-check amounts/dates against source data |
| 11 | **LangGraph Workflow** | Orchestrated all 6 steps into a single pipeline with state management |
| 12 | **Data Generation** | Created synthetic data script for 5 customers + 120+ transactions + 5 SAR cases |
| 13 | **Frontend Setup** | Initialized Vite + React + TypeScript + TailwindCSS project |
| 14 | **Frontend Pages** | Built Dashboard (stats + cases), GenerateSAR (6-step progress), SAREditor (audit panel) |
| 15 | **Docker** | Wrote Dockerfiles + docker-compose.yml for containerized deployment |
| 16 | **Debugging** | Fixed Supabase connectivity issues, implemented SQLite fallback, refactored models for cross-DB compatibility |
| 17 | **Documentation** | Comprehensive README + this brief document |

---

## 17. Essential Topics to Learn

If you want to build projects like LuminaSAR, here are the **specific subtopics** you should learn (not the entire framework — just what matters):

### 🐍 Python / Backend

| Topic | What to Learn | Why It Matters |
|---|---|---|
| **FastAPI Basics** | Route decorators (`@app.get`, `@app.post`), path parameters, query parameters | You define your API endpoints with these |
| **FastAPI Dependency Injection** | `Depends()`, how `yield` works in dependencies | Clean database session management |
| **Pydantic Models** | `BaseModel`, field types, validators, `BaseSettings` | Request validation, config management |
| **Async/Await** | `async def`, `await`, `httpx.AsyncClient` | LLM calls are slow; async prevents blocking |
| **SQLAlchemy ORM** | `Column`, `Base`, `Session`, `query().filter()`, `create_engine` | All database operations go through this |
| **Environment Variables** | `python-dotenv`, `.env` files, `os.getenv()` | Never hardcode secrets |

### 🤖 AI / ML

| Topic | What to Learn | Why It Matters |
|---|---|---|
| **Embeddings** | What are vector embeddings, cosine similarity, `sentence-transformers` | The foundation of RAG |
| **Vector Databases** | ChromaDB (or Pinecone, Weaviate), collections, upsert, query | Storing and searching embeddings |
| **RAG Pattern** | Load documents → embed → store → query → retrieve → inject into prompt | The core pattern for grounded AI |
| **Prompt Engineering** | System prompts, few-shot examples, grounding, temperature | How you control LLM output quality |
| **Ollama API** | `/api/generate`, model parameters, streaming vs non-streaming | Local LLM integration |
| **LangGraph** | `StateGraph`, nodes, edges, `TypedDict` state | Multi-step AI workflows |

### ⚛️ React / Frontend

| Topic | What to Learn | Why It Matters |
|---|---|---|
| **React Hooks** | `useState`, `useEffect`, `useCallback` | State management and side effects |
| **React Router** | `BrowserRouter`, `Route`, `useNavigate`, `useParams` | Page navigation |
| **Axios / Fetch** | HTTP requests, `async/await`, error handling | Calling backend APIs |
| **TypeScript Interfaces** | `interface`, generic types, `Record<string, any>` | Type-safe API responses |
| **TailwindCSS** | Utility classes, responsive design (`md:`, `lg:`), custom themes | Rapid UI styling |
| **Component Patterns** | Props, state lifting, conditional rendering | Building reusable UI pieces |

### 🏗️ Architecture / DevOps

| Topic | What to Learn | Why It Matters |
|---|---|---|
| **REST API Design** | HTTP methods (GET/POST), status codes, JSON, CORS | Frontend-backend communication |
| **Docker Basics** | `Dockerfile`, `docker-compose.yml`, images, containers, volumes | Reproducible deployments |
| **Database Design** | Primary keys, foreign keys, 1-to-many relationships, JSON columns | Schema planning |
| **Git** | Branching, staging, committed, meaningful commit messages | Version control |

### 🔐 Security Concepts

| Topic | What to Learn | Why It Matters |
|---|---|---|
| **Hashing** | SHA-256, `hashlib`, hash chains | Audit trail integrity |
| **CORS** | What it is, why browsers block cross-origin, how to configure | Frontend-backend on different ports |
| **JWT** | JSON Web Tokens, signing, verification | User authentication |
| **Environment Security** | `.env` in `.gitignore`, secrets management | Never commit passwords |

---

## 18. Similar Project Ideas

Here are project ideas that use the **same tech stack and patterns** as LuminaSAR:

### 🔹 Beginner-Friendly (Same patterns, simpler domain)

| Project | Tech Used | Description |
|---|---|---|
| **AI Resume Screener** | FastAPI + Ollama + React | Upload resumes, LLM extracts skills/experience, compare against job descriptions using RAG |
| **Smart Meeting Summarizer** | FastAPI + Ollama + ChromaDB | Upload meeting transcripts, generate summaries with action items, search past meetings via RAG |
| **AI Study Notes Generator** | FastAPI + Ollama + React | Upload textbook chapters, LLM generates study notes, flashcards, and quiz questions with source attribution |

### 🔹 Intermediate (More complex pipeline)

| Project | Tech Used | Description |
|---|---|---|
| **Medical Report Analyzer** | FastAPI + LangGraph + Ollama + RAG | Upload lab reports, detect anomalies, generate patient-friendly summaries with source citations |
| **Legal Contract Reviewer** | FastAPI + RAG + Ollama | Upload contracts, compare against regulatory templates via RAG, highlight risky clauses with audit trail |
| **AI Code Reviewer** | FastAPI + Ollama + ChromaDB | Submit code, retrieve coding standards via RAG, generate code review with line-by-line annotations |
| **Customer Support Bot** | FastAPI + RAG + React | Build a chatbot that retrieves answers from company docs (RAG), logs every response with source attribution |

### 🔹 Advanced (Full production-grade)

| Project | Tech Used | Description |
|---|---|---|
| **Financial Fraud Detection Dashboard** | FastAPI + ML + LangGraph + React | Real-time transaction monitoring, ML anomaly detection, automated alert generation with audit trail |
| **AI-Powered Research Assistant** | LangGraph + RAG + Ollama | Multi-step research workflow: search → extract → synthesize → cite, with hash-chained provenance |
| **Regulatory Compliance Copilot** | FastAPI + RAG + Ollama + React | Upload company policies, compare against regulations (GDPR, HIPAA), generate compliance reports |
| **Explainable AI Diagnostic Tool** | FastAPI + ML + LangGraph | Run ML predictions and generate human-readable explanations with sentence-level attribution to input features |

### 🔹 The Learning Progression

```
[ Start Here ]
    │
    ▼
Build a simple API with FastAPI
    │  (Learn: routes, Pydantic, SQLAlchemy)
    ▼
Add a React frontend
    │  (Learn: axios, useState, useEffect)
    ▼
Connect to Ollama for text generation
    │  (Learn: HTTP API, prompt engineering)
    ▼
Add RAG with ChromaDB
    │  (Learn: embeddings, vector search)
    ▼
Build a multi-step pipeline with LangGraph
    │  (Learn: state management, async workflows)
    ▼
Add audit trail and validation
    │  (Learn: hashing, data integrity)
    ▼
Dockerize everything
    │  (Learn: containers, compose, deployment)
    ▼
[ You're now at LuminaSAR level! ]
```

---

<p align="center">
  <strong>LuminaSAR</strong> — Because compliance shouldn't be a black box. 🔆
</p>
