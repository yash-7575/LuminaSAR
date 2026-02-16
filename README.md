# 🔆 LuminaSAR — The Glass Box AI

> *SAR Narrative Generator with Explainable AI Audit Trail*
>
> **Barclays Hack-O-Hire 2026**

<p align="center">
  <strong>Where Every Decision is Transparent</strong>
</p>

---

## 🚀 What is LuminaSAR?

LuminaSAR is an AI-powered **Suspicious Activity Report (SAR) narrative generator** that reduces manual SAR writing from **5-6 hours → ~30 seconds** while maintaining **complete explainability** through a sentence-level audit trail.

### The Innovation: Sentence-Level Data Attribution

Unlike black-box AI systems, LuminaSAR provides a **Glass Box** approach:
- Every sentence in the generated narrative links back to the exact source data
- A **hash-chained audit trail** provides tamper-evident logging of every AI decision
- Analysts can click any sentence to see which transactions, patterns, and templates informed it

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LuminaSAR Architecture                    │
├─────────────┬──────────────────────────────────┬────────────┤
│  Frontend   │         Backend API             │   Data     │
│  React/TS   │         FastAPI                 │  Layer     │
│  Tailwind   │                                  │            │
│  ┌────────┐ │  ┌──────────────────────────┐   │ ┌────────┐ │
│  │Dashboard│ │  │   LangGraph Workflow     │   │ │Supabase│ │
│  │Generate │─┼──│ 1. Fetch Data           │───┼─│PostgreS│ │
│  │Editor   │ │  │ 2. Analyze Patterns (ML)│   │ │  QL    │ │
│  │AuditView│ │  │ 3. RAG Template Lookup  │   │ └────────┘ │
│  └────────┘ │  │ 4. LLM Generation       │   │ ┌────────┐ │
│             │  │ 5. Validate (anti-halluc)│   │ │ SQLite │ │
│             │  │ 6. Save + Audit Trail   │   │ │Fallback│ │
│             │  └──────────────────────────┘   │ └────────┘ │
│             │  ┌────────────┐ ┌──────────┐   │ ┌────────┐ │
│             │  │ Ollama     │ │  Audit   │   │ │ChromaDB│ │
│             │  │ llama3.2   │ │  Logger  │   │ │  RAG   │ │
│             │  └────────────┘ └──────────┘   │ └────────┘ │
└─────────────┴──────────────────────────────────┴────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Narrative Generation** | Ollama llama3.2 generates regulatory-compliant SAR narratives |
| 🔍 **ML Pattern Detection** | Velocity, volume, structuring, network analysis algorithms |
| 📚 **RAG Templates** | ChromaDB + sentence-transformers for context-aware generation |
| 🔗 **Hash-Chained Audit** | SHA-256 hash chain for tamper-evident audit trail |
| 📝 **Sentence Attribution** | Click any sentence → see exact source data |
| 🏷️ **Typology Matching** | Structuring, layering, smurfing, integration, round-tripping |
| 📊 **Risk Scoring** | 0-10 risk score from multi-factor analysis |
| 🔒 **100% Local** | No data leaves your network — Ollama runs locally |
| 🔄 **Auto DB Fallback** | Automatic SQLite fallback if Supabase is unreachable |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, TailwindCSS, React Query, Zustand, Framer Motion |
| **Backend** | FastAPI, SQLAlchemy, Pydantic |
| **AI/ML** | Ollama (llama3.2), LangGraph, ChromaDB, sentence-transformers |
| **Database** | Supabase PostgreSQL (primary) / SQLite (automatic fallback) |
| **Analysis** | Pandas, NumPy, Scikit-learn, NetworkX |
| **Infra** | Docker, Docker Compose, Nginx |

---

## 📋 Prerequisites

Before cloning the repo, make sure you have the following installed on your machine:

| Requirement | Version | Download Link |
|-------------|---------|---------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **Ollama** | Latest | [ollama.com](https://ollama.com/download) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |
| **Docker Desktop** | Latest *(optional)* | [docker.com](https://www.docker.com/products/docker-desktop/) |

> **Note:** Docker is only needed if you want containerized deployment. The project runs perfectly fine without it using the local development setup.

---

## ⚡ Quick Start (Local Development)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yash-7575/LuminaSAR.git
cd LuminaSAR
```

---

### Step 2: Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

> **⚠️ Troubleshooting:** If `pip install` hangs or fails with dependency conflicts, try:
> ```bash
> pip install --no-cache-dir -r requirements.txt
> ```
> Or install core packages first:
> ```bash
> pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv
> pip install langchain langchain-community langgraph chromadb sentence-transformers ollama
> pip install pandas numpy scikit-learn networkx httpx
> ```

---

### Step 3: Configure Environment Variables

Create or edit the file `backend/.env`:

```env
# Supabase Configuration (Optional — the app auto-falls-back to SQLite)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
DATABASE_URL=postgresql://postgres:your_password@db.your-project.supabase.co:5432/postgres

# JWT
JWT_SECRET_KEY=change_me_to_64_char_hex_string

# Ollama (REQUIRED — this is the local LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db
```

> **💡 Important:** If you don't have Supabase credentials, that's perfectly fine! The backend will automatically fall back to a local **SQLite database** (`luminasar.db`) and work out of the box. Supabase is only needed for cloud PostgreSQL.

---

### Step 4: Install and Start Ollama

Ollama is the **local LLM runtime** that powers the narrative generation. It runs entirely on your machine — no API keys, no cloud, no data leakage.

```bash
# Install Ollama from https://ollama.com/download

# Pull the required model (~2GB download)
ollama pull llama3.2:latest

# Start the Ollama server (it runs on port 11434)
ollama serve
```

> **✅ Verify Ollama is running:**
> ```bash
> curl http://localhost:11434/api/tags
> ```
> You should see a JSON response listing `llama3.2:latest`.

---

### Step 5: Seed the Database with Test Data

```bash
cd backend
python -m scripts.generate_data
```

This will:
- Generate **5 synthetic customers** with Indian bank accounts
- Create **~120+ transactions** with suspicious patterns (structuring, layering, smurfing, etc.)
- Create **5 SAR cases** ready for narrative generation
- Print **Case IDs** you can use for testing

Example output:
```
🏗️ LuminaSAR — Generating Synthetic Data
==================================================

👤 Customer: Sanjay Verma (AXIS206078254)
   💳 21 transactions (structuring)
   📋 Case: b920a3c4...

...

📋 Case IDs for testing:
   b920a3c4-dccc-44ce-9ebb-9866edcec4dd
   8e23cac6-6d07-4d92-bc7b-79092dbfce65
   ...
```

> **📝 Save one of these Case IDs** — you'll need it to generate a SAR narrative.

---

### Step 6: Start the Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **API Root:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

### Step 7: Start the Frontend

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

---

### Step 8: Generate Your First SAR! 🚀

1. Open **http://localhost:5173** in your browser
2. You'll see the **Dashboard** with pending cases and statistics
3. Click **"New SAR"** to go to the generation page
4. Enter a **Case ID** from Step 5 (e.g., `b920a3c4-dccc-44ce-9ebb-9866edcec4dd`)
5. Click **"Generate SAR"** and watch the 6-step pipeline in action
6. Review the generated narrative in the **SAR Editor** with click-to-audit functionality

---

## 🐳 Docker Deployment (Alternative)

If you prefer containerized deployment:

```bash
# Make sure Ollama is running on the host machine first!
ollama serve

# Build and start all services
docker-compose up --build
```

This starts:
| Service | URL | Description |
|---------|-----|-------------|
| **Backend** | http://localhost:8000 | FastAPI server |
| **Frontend** | http://localhost:3000 | React app (via Nginx) |

> **Note:** When running in Docker, the backend connects to Ollama on the host via `host.docker.internal:11434`. Make sure Ollama is running before starting Docker.

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/docs` | Interactive Swagger API documentation |
| `POST` | `/api/v1/sar/generate` | Generate a SAR narrative |
| `GET` | `/api/v1/sar/{narrative_id}` | Get narrative details |
| `GET` | `/api/v1/sar/{narrative_id}/audit` | Get complete audit trail |
| `POST` | `/api/v1/sar/{narrative_id}/approve` | Approve SAR for filing |
| `GET` | `/api/v1/sar/` | List recent SAR cases |
| `GET` | `/api/v1/sar/stats/overview` | Dashboard statistics |

### Example: Generate a SAR

```bash
curl -X POST http://localhost:8000/api/v1/sar/generate \
  -H "Content-Type: application/json" \
  -d '{"case_id": "YOUR_CASE_ID_HERE"}'
```

### Example: Get Dashboard Stats

```bash
curl http://localhost:8000/api/v1/sar/stats/overview
```

Response:
```json
{
  "total_sars": 1,
  "pending_cases": 4,
  "avg_generation_time": 34.0,
  "total_customers": 5,
  "high_risk_cases": 0,
  "cost_savings_lakhs": 0.1
}
```

---

## 🔍 The 6-Step AI Pipeline

Each step is logged to the audit trail with data sources, reasoning, confidence scores, and SHA-256 hash links.

```
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│  1. FETCH    │───▶│  2. ANALYZE      │───▶│  3. RAG RETRIEVE  │
│  Customer &  │    │  ML Pattern      │    │  Template lookup  │
│  Transaction │    │  Detection       │    │  via ChromaDB     │
│  Data        │    │  (4 algorithms)  │    │  sentence-embed   │
└──────────────┘    └──────────────────┘    └───────────────────┘
                                                       │
┌──────────────┐    ┌──────────────────┐    ┌──────────▼────────┐
│  6. SAVE     │◀───│  5. VALIDATE     │◀───│  4. GENERATE      │
│  Narrative + │    │  Anti-halluc     │    │  LLM Narrative    │
│  Audit Trail │    │  Cross-check     │    │  via Ollama       │
│  to Database │    │  Against Source   │    │  (grounded)       │
└──────────────┘    └──────────────────┘    └───────────────────┘
```

### Step Details

| Step | Service | What It Does |
|------|---------|-------------|
| **1. Fetch Data** | `langgraph_workflow.py` | Queries customer KYC and transaction records from the database |
| **2. Analyze Patterns** | `pattern_detector.py` | Runs 4 ML algorithms: velocity analysis, volume analysis, structuring detection (₹50K threshold), network graph analysis (NetworkX) |
| **3. Retrieve Templates** | `rag_service.py` | Searches ChromaDB vector store for relevant SAR templates using `all-MiniLM-L6-v2` embeddings |
| **4. Generate Narrative** | `llm_service.py` | Constructs a grounded prompt with all data + templates, sends to Ollama `llama3.2` with anti-hallucination instructions |
| **5. Validate** | `validator.py` | Cross-references generated text against source data for factual accuracy, checks for hallucinated amounts/dates |
| **6. Save Results** | `audit_logger.py` | Persists narrative + creates sentence-level attribution + builds SHA-256 hash chain |

---

## 📊 Database Schema

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `customers` | Customer KYC data | `customer_id`, `name`, `account_number`, `occupation`, `stated_income`, `customer_since` |
| `transactions` | Transaction records | `transaction_id`, `customer_id`, `amount`, `date`, `source_account`, `destination_account`, `transaction_type` |
| `sar_cases` | SAR case metadata | `case_id`, `customer_id`, `status`, `risk_score`, `typologies` (JSON) |
| `sar_narratives` | Generated narrative text | `narrative_id`, `case_id`, `narrative_text`, `generated_at`, `generation_time_seconds` |
| `audit_trail` | Hash-chained audit steps | `audit_id`, `narrative_id`, `step_name`, `data_sources` (JSON), `reasoning` (JSON), `confidence_scores` (JSON), `previous_hash`, `current_hash` |

> **Database Flexibility:** The models use standard SQLAlchemy types (`String`, `JSON`, `DateTime`) instead of Postgres-specific types, allowing seamless switching between Supabase PostgreSQL and local SQLite.

---

## 📁 Project Structure

```
LuminaSAR/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic Settings from .env
│   │   ├── database.py            # SQLAlchemy engine + SQLite fallback
│   │   ├── main.py                # FastAPI app with CORS
│   │   ├── models/                # SQLAlchemy ORM models
│   │   │   ├── customer.py        # Customer KYC model
│   │   │   ├── transaction.py     # Transaction model
│   │   │   ├── sar_case.py        # SAR case model
│   │   │   ├── sar_narrative.py   # Generated narrative model
│   │   │   └── audit_trail.py     # Hash-chained audit model
│   │   ├── routes/                # FastAPI endpoints
│   │   │   ├── health.py          # GET /health
│   │   │   └── sar.py             # All SAR CRUD + generation routes
│   │   ├── schemas/               # Pydantic request/response models
│   │   │   ├── request.py         # GenerateSARRequest, ApproveSARRequest
│   │   │   └── response.py        # SARResponse, AuditTrailResponse, etc.
│   │   ├── services/              # Core AI/ML services
│   │   │   ├── pattern_detector.py    # ML pattern detection algorithms
│   │   │   ├── rag_service.py         # ChromaDB + embeddings RAG
│   │   │   ├── llm_service.py         # Ollama LLM integration
│   │   │   ├── audit_logger.py        # Hash-chained audit trail
│   │   │   ├── validator.py           # Anti-hallucination validation
│   │   │   └── langgraph_workflow.py  # 6-step pipeline orchestrator
│   │   └── utils/                 # Utilities
│   │       ├── hash.py            # SHA-256 hash functions
│   │       └── prompts.py         # SAR generation prompt templates
│   ├── data/
│   │   └── templates/             # SAR reference templates
│   │       ├── sar_structuring.txt
│   │       ├── sar_layering.txt
│   │       ├── sar_smurfing.txt
│   │       └── sar_integration.txt
│   ├── scripts/
│   │   └── generate_data.py       # Synthetic data generation
│   ├── luminasar.db               # Local SQLite fallback (auto-generated)
│   ├── chroma_db/                 # ChromaDB vector store (auto-generated)
│   ├── .env                       # Environment variables
│   ├── requirements.txt           # Python dependencies
│   └── Dockerfile                 # Backend container
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # React Router setup
│   │   ├── main.tsx               # App entry point
│   │   ├── components/
│   │   │   └── Navbar.tsx         # Navigation bar
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # Stats widgets, case table
│   │   │   ├── GenerateSAR.tsx    # 6-step animated generation UI
│   │   │   └── SAREditor.tsx      # Sentence-level audit trail viewer
│   │   ├── services/
│   │   │   └── api.ts             # Axios API client
│   │   └── styles/
│   │       └── globals.css        # Glassmorphism, glow effects
│   ├── index.html                 # HTML entry point
│   ├── tailwind.config.js         # TailwindCSS configuration
│   ├── vite.config.ts             # Vite bundler config
│   ├── tsconfig.json              # TypeScript config
│   ├── package.json               # Node.js dependencies
│   ├── nginx.conf                 # Production Nginx config
│   └── Dockerfile                 # Frontend container
├── docker-compose.yml             # Multi-service orchestration
└── README.md                      # This file
```

---

## 🔧 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | No | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | No | — | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | No | — | Supabase service role key (for data seeding) |
| `DATABASE_URL` | No | SQLite fallback | PostgreSQL connection string |
| `JWT_SECRET_KEY` | No | `change_me...` | JWT signing secret |
| `OLLAMA_HOST` | **Yes** | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | **Yes** | `llama3.2:latest` | LLM model to use |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage directory |

---

## ❓ Frequently Asked Questions

### "I don't have Supabase — will it work?"

**Yes!** The backend automatically detects if Supabase is unreachable and falls back to a local **SQLite** database (`luminasar.db`). All features work identically.

### "Which Ollama model should I use?"

We recommend `llama3.2:latest` (default). It's ~2GB and runs on most modern machines. For faster generation on lower-end hardware, try `llama3.2:1b`.

```bash
# Default (recommended)
ollama pull llama3.2:latest

# Lighter alternative
ollama pull llama3.2:1b
```

### "How long does SAR generation take?"

Typically **25-40 seconds** depending on your hardware. The bottleneck is the LLM generation step (Step 4). GPU-accelerated Ollama will be significantly faster.

### "I'm getting `ModuleNotFoundError`"

Make sure you:
1. Activated your virtual environment (`venv\Scripts\activate` on Windows)
2. Installed all dependencies (`pip install -r requirements.txt`)
3. Are running commands from the `backend/` directory

### "The frontend can't connect to the backend"

The frontend expects the backend at `http://localhost:8000`. Make sure:
1. The backend is running on port 8000
2. CORS is configured (it is by default for `localhost:5173`)

### "`pip install` is stuck on backtracking"

This can happen with complex dependency chains. Try:
```bash
pip install --no-cache-dir -r requirements.txt
```

---

## 🎯 Hackathon Problem Statement

> **Barclays Hack-O-Hire 2026**: Build a production-grade GenAI tool that automates SAR narrative filing with full explainability.

### Our Differentiators

| Feature | Details |
|---------|---------|
| ✅ **Sentence-Level Attribution** | Not just "what" the AI generated, but "why" for each sentence |
| ✅ **Hash-Chained Audit Trail** | SHA-256 tamper-evident, regulatory-compliant logging |
| ✅ **100% Local LLM** | No sensitive data leaves the bank's network |
| ✅ **Indian Regulatory Compliance** | PMLA, FIU-IND, ₹50K CTR threshold detection |
| ✅ **Multi-Typology Detection** | ML-driven (not rule-based) — structuring, layering, smurfing, integration |
| ✅ **Anti-Hallucination Validation** | Cross-references every generated fact against source data |
| ✅ **Production-Ready** | Docker deployment, auto-fallback database, health checks |

---

## 🧪 Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## 📜 License

This project was built for Barclays Hack-O-Hire 2026.


---

<p align="center">
  <strong>LuminaSAR</strong> — Because compliance shouldn't be a black box. 🔆
</p>
