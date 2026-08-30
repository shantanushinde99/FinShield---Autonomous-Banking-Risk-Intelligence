# Product Requirements / Specification

## 1. Product Overview
FinShield empowers bank officers with an AI-driven, voice-activated investigation tool to assess the risk of a customer applying for a loan or performing significant financial actions.

## 2. Core Workflow
1. **Command Input**: Officer provides a voice (via Omi) or text command (e.g., "Investigate customer C10452 for a ₹10 lakh personal loan").
2. **Intent & Entity Extraction**: System identifies the customer ID and the investigation intent.
3. **Data Retrieval**: Customer profiles, transactions, and historical data are fetched from DuckDB.
4. **Semantic Retrieval**: Qdrant retrieves semantically similar historical investigation cases.
5. **Agent Orchestration (Lyzr)**:
   - *Customer Profile Agent* analyzes demographic and historical application data.
   - *Credit Risk Agent* analyzes credit scores, previous loan performance, and debt-to-income.
   - *Transaction Analysis Agent* evaluates transactional anomalies, spending behavior, and fraud metrics.
   - *Fraud Detection Agent* flags known fraud patterns.
   - *Historical Case Agent* contextualizes findings against Qdrant memory.
6. **Synthesis**: The *Risk Decision Agent* synthesizes the evidence.
7. **Reporting**: The system generates a structured risk assessment and recommendation.
8. **Follow-up**: The officer can interrogate the assessment via text/voice.

## 3. User Interface (Frontend)
- **Dashboard**: High-level overview.
- **Customer Search**: Find customers and initiate investigations.
- **Investigation Workspace**: The main arena where voice commands are issued.
- **Execution Visualization**: Live tracing of Lyzr agent activities (observable workflow).
- **Risk Assessment View**: Clearly formatted report showing risk score, factors, evidence, and similar historical cases.
