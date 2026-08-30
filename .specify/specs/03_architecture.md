# Technical Architecture

## 1. Directory Structure

The proposed high-level architecture enforces clear separation of concerns.

```text
finshield/
├── backend/
│   ├── api/             # FastAPI routes and controllers
│   ├── agents/          # Lyzr specialized agents
│   ├── services/        # Core business logic orchestrating data & agents
│   ├── data/            # Data access layer (Repositories for DuckDB)
│   ├── qdrant/          # Semantic search integration
│   ├── lyzr/            # Lyzr configuration and base classes
│   ├── omi/             # Omi voice integration boundary
│   ├── models/          # Pydantic schemas (e.g. RiskAssessment)
│   ├── config/          # Environment validation (BaseSettings)
│   └── main.py          # Application entrypoint
├── frontend/            # React/Next.js application
├── scripts/             # Data ingestion and utility scripts
├── tests/               # Pytest suite
├── docs/                # Architecture and specification documentation
├── .env                 # Local secrets (ignored in Git)
├── .env.example         # Template for environment variables
├── pyproject.toml       # Python dependencies and build system
└── README.md            # Entry point for developers
```

## 2. Lyzr Agent Architecture
Lyzr will orchestrate specialized agents, preventing a single monolithic prompt/agent from becoming overwhelmed.

**Agents:**
1. **Customer Profile Agent**: Assesses the demographic and baseline profile of the customer.
2. **Credit Risk Agent**: Evaluates historical credit performance, DTI, and loan behaviors.
3. **Transaction Analysis Agent**: Focuses strictly on transactional anomalies, cash flows, and frequency.
4. **Fraud Detection Agent**: Correlates the customer's data against known fraud indicators and flagged transactions.
5. **Historical Case Retrieval Agent**: Uses the `qdrant` module to retrieve and summarize past similar investigations.
6. **Risk Decision Agent**: The master agent. It takes the outputs of Agents 1-5 and synthesizes a final `RiskAssessment`.

## 3. Qdrant Architecture (Semantic Memory)
- **Deployment**: Qdrant Cloud cluster.
- **Collection**: `finshield_memory`
- **Purpose**: Stores historical financial cases, risk assessments, and investigation summaries as vector embeddings.
- **Workflow**: The Historical Case Retrieval Agent takes the current investigation context (customer profile + request), embeds it, and queries Qdrant for Top-K similar cases to inform the decision.

## 4. Omi Architecture (Voice Integration)
- **Integration Boundary**: The `backend/omi/` module will expose endpoints or webhooks that receive transcripts from Omi devices.
- **Flow**: Omi Transcript -> Command Interpretation -> Structured Investigation Request -> Lyzr Orchestration.
- **Fallback**: The backend API will fully support text-based requests for seamless development, testing, and UI dashboard usage without requiring physical Omi hardware.

## 5. Security Requirements
- **Secrets Management**: No API keys hardcoded in source. `backend/config/` must load via environment variables. `.env` is never committed.
- **Data Access**: Agents will NOT have raw SQL access. They must utilize strict `backend/data/` Repositories which validate inputs and prevent SQL injection.
- **Pydantic Validation**: All Agent inputs and outputs, as well as API requests/responses, are validated strictly through Pydantic models.
- **Frontend Security**: No Qdrant or Lyzr API keys are sent to the frontend. The frontend communicates exclusively with the FastAPI backend.
