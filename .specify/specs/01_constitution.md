# FinShield Project Constitution

## 1. Vision
FinShield is a voice-first banking risk investigation copilot designed for bank officers. It autonomously investigates financial customers by combining customer profiles, transaction histories, repayment behaviors, and historical financial cases. 

## 2. Core Principles
- **Decision Support Copilot**: The system provides explainable risk assessments. It must **NOT** autonomously approve, reject, freeze, block, or deny a customer's financial account. Final decisions always remain with a human banking officer.
- **Explainability**: Every risk assessment must be clearly justified with risk factors, positive factors, and historical evidence.
- **Security-First**: Sensitive financial data must be handled with strict security constraints. API keys, secrets, and raw database access must never be exposed to the frontend or directly to LLMs executing arbitrary queries.
- **Observability**: The autonomous agent workflow must be visible to the user, particularly via the frontend interface.

## 3. Technology Stack
- **Voice Input**: Omi (Real-time voice input)
- **Vector Memory**: Qdrant Cloud (Persistent semantic financial memory)
- **Agent Orchestration**: Lyzr (Multi-agent orchestration, reasoning, and task execution)
- **Data Layer**: DuckDB (Structured analytical queries) & Parquet (Data storage)
- **Backend Framework**: Python / FastAPI
- **Frontend**: To be determined (Next.js/React recommended for dashboarding)

## 4. Boundaries & Limitations
- No autonomous irreversible financial actions.
- Agents operate on predefined abstractions (Repositories) and cannot execute arbitrary SQL against the financial database.
- System operates in an isolated environment relying on deterministic schema abstractions.
