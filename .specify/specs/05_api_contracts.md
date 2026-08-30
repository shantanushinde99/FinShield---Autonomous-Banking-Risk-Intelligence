# API Contracts & RiskAssessment Schema

## 1. Investigation API Endpoints

### `POST /api/v1/investigations/start`
Starts a new investigation based on an officer's prompt (text or parsed voice).
- **Request Body**:
```json
{
  "prompt": "Investigate customer C10452 for a ₹10 lakh personal loan.",
  "officer_id": "OFC-991"
}
```
- **Response**:
```json
{
  "investigation_id": "INV-8832-1",
  "status": "in_progress",
  "message": "Investigation started. Websocket available for live tracing."
}
```

### `GET /api/v1/investigations/{investigation_id}`
Retrieves the current status or final output of an investigation.

## 2. RiskAssessment Schema (Output Contract)
The Risk Decision Agent produces the final recommendation adhering to this Pydantic schema:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RiskAssessment(BaseModel):
    customer_id: str = Field(..., description="The ID of the investigated customer")
    investigation_id: str = Field(..., description="Unique ID for this investigation")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calculated risk score from 0-100")
    risk_level: str = Field(..., description="LOW, MEDIUM, MEDIUM_HIGH, HIGH")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent's confidence in the assessment")
    requested_loan_amount: Optional[float] = Field(None, description="The loan amount in the prompt, if any")
    risk_factors: List[str] = Field(..., description="List of negative signals or risks")
    positive_factors: List[str] = Field(..., description="List of positive signals or mitigations")
    evidence: List[str] = Field(..., description="Specific data points validating the factors")
    similar_cases: List[str] = Field(..., description="Summaries of semantically similar historical cases")
    recommendation: str = Field(..., description="APPROVE_RECOMMENDATION, MANUAL_REVIEW, DECLINE_RECOMMENDATION")
    explanation: str = Field(..., description="Detailed explanation of the recommendation for the officer")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
```
