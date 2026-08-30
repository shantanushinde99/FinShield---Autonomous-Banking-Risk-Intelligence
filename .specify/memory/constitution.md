# FinShield AI Infrastructure Constitution

## Principle 1 — Minimal Architecture
Never introduce a component unless it solves a demonstrated requirement.

## Principle 2 — Real Integrations
Do not create fake implementations of Lyzr, Qdrant, or Omi.

## Principle 3 — API-First
External services must be accessed through documented APIs/SDKs.

## Principle 4 — Structured Financial Reasoning
Agents must use deterministic DuckDB data and engineered risk features instead of inventing financial facts.

## Principle 5 — Evidence-Based Decisions
Every risk assessment must identify the evidence used.

## Principle 6 — Human-in-the-Loop
FinShield is a decision-support system. It must recommend:
- APPROVE
- MANUAL_REVIEW
- DECLINE
but must NOT autonomously execute irreversible banking actions.

## Principle 7 — Privacy and Secrets
Never hardcode API keys. Never commit .env. Never expose secrets in logs.

## Principle 8 — Minimal Code
Use Ponytail principles throughout development.

## Principle 9 — Test Before Expansion
Every phase must be independently verified before moving to the next phase.
