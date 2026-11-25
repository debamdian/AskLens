# AskLens: AI Data Analyst Platform 🔍📊

> An autonomous **Senior AI Data Analyst & Data Scientist** that plans analyses, writes validated safe SQL against PostgreSQL, executes statistical reasoning, and streams back executive plain-language answers, interactive charts, data tables, and audited SQL.

---

## ⚡ Key Highlights & Architecture

- **Free & Open-Source Only**: 100% free-tier and local tools (Google Gemini Free Tier, local Ollama, PostgreSQL with `pgvector`, Next.js 15, FastAPI).
- **Dual-Schema Database Architecture**:
  - `warehouse`: E-commerce sales data (customers, products, orders, returns, marketing spend) queried by the agent via a dedicated `warehouse_readonly` PostgreSQL role.
  - `app`: Metadata, user sessions, chat history, golden queries, pgvector embeddings, and audit logs.
- **SQL Safety & Defense-in-Depth**:
  - Parsed using `sqlglot` AST validation.
  - Strictly single-statement `SELECT` only (CTEs permitted).
  - Banned commands: DDL/DML, `pg_catalog`, `information_schema`, and dangerous built-ins (`pg_sleep`, `lo_*`, `dblink`).
  - Automatic `LIMIT` clause injection and `EXPLAIN (FORMAT JSON)` cost threshold verification.
- **Realistic E-Commerce Anomaly**:
  - Contains ~2 years of sales data across Indian regions (Gujarat, Maharashtra, Karnataka, etc.).
  - Features an engineered sales dip in Gujarat during Q3/Q4 caused by a 85% marketing spend slash and supply stockouts in top Electronics categories.
- **Interactive UI**:
  - Streaming progress status with collapsible step details.
  - Apache ECharts dynamic visualizer (Bar, Line, Pie).
  - Paginated data preview with one-click CSV download.
  - Collapsible, syntax-highlighted SQL viewer with execution latency and cost estimate.

---

## 🚀 Quickstart Guide (Under 15 Minutes)

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/)
- [Node.js 20+](https://nodejs.org/) & [Python 3.11+](https://www.python.org/)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/debamdian/AskLens.git
cd AskLens
cp .env.example .env
```
Edit `.env` to configure your free LLM provider:
- **Google Gemini Free Tier** (Default): Set `GEMINI_API_KEY=your_key` and `GEMINI_MODEL=gemini-3.5-flash`.
- **Local Ollama**: Set `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen2.5-coder:7b`.
- **Groq / OpenRouter**: Set `LLM_PROVIDER=openai_compat`, `OPENAI_COMPAT_API_KEY=your_key`.

### 2. Start PostgreSQL with pgvector & Seed Sample Data
```bash
docker compose up -d postgres
python -m pip install -e api/
python api/seed/seed_warehouse.py
```

### 3. Launch Services

#### Option A: Docker Compose (All-in-One)
```bash
docker compose up
```

#### Option B: Local Development
**Terminal 1 (Backend API):**
```bash
cd api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend Web App):**
```bash
cd web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🧪 Testing & Verification

Run the comprehensive SQL AST validator test suite:
```bash
pytest api/tests/test_sql_validator.py -v
```
*(All 24 test cases verify the blocking of injection attacks, multi-statements, DDL/DML, catalog probing, and row limit enforcement.)*

---

## 📦 Project Structure
```text
AskLens/
├── docker-compose.yml        # PostgreSQL + pgvector, API, and Web containers
├── .env.example              # Documented environment templates
├── docker/postgres/init.sql  # Dual-schema and read-only role setup
├── api/                      # FastAPI Python backend
│   ├── app/
│   │   ├── main.py
│   │   ├── core/config.py
│   │   ├── db/connector.py   # Read-only executor & cost estimator
│   │   ├── schema/crawler.py # information_schema auto-crawler
│   │   ├── sql/validator.py  # sqlglot AST safety validator
│   │   ├── sql/generator.py  # Context-aware SQL generator
│   │   ├── llm/factory.py    # Resilient multi-provider LLM interface
│   │   └── routers/          # SSE streaming & schema endpoints
│   ├── seed/                 # Realistic warehouse generator with Gujarat dip
│   └── tests/                # AST safety and injection test suite
└── web/                      # Next.js 15 App Router frontend
    ├── components/chat/      # Streaming feed, DataTable, ChartRenderer, CollapsibleSQL
    ├── components/sidebar/   # Schema explorer, glossary viewer, dark mode
    └── app/                  # Next.js layout & page
```
