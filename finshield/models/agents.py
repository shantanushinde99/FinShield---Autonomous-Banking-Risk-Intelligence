from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class Evidence(BaseModel):
    source_type: str  # e.g., "duckdb", "qdrant", "derived"
    source_id: str    # e.g., "FIN_000001", "CASE_001"
    description: str
    value: Any
    relevance: str

class BaseAssessment(BaseModel):
    investigation_id: str
    customer_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerProfileAssessment(BaseAssessment):
    age: Optional[float] = None
    employment_years: Optional[float] = None
    total_income: Optional[float] = None
    occupation: Optional[str] = None
    financial_stability_indicators: List[str] = Field(default_factory=list)
    profile_observations: List[str] = Field(default_factory=list)
    data_completeness: str

class CreditRiskAssessment(BaseAssessment):
    credit_risk_score: float
    risk_level: str  # LOW, MEDIUM, MEDIUM_HIGH, HIGH
    key_factors: List[str] = Field(default_factory=list)
    positive_factors: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str

class TransactionRiskAssessment(BaseAssessment):
    transaction_risk_score: float
    risk_level: str
    behavioral_indicators: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)
    positive_indicators: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str

class FraudAssessment(BaseAssessment):
    fraud_risk_score: float
    risk_level: str
    confirmed_fraud_count: int
    flagged_count: int
    suspicious_patterns: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    explanation: str

class HistoricalCaseItem(BaseModel):
    case_id: str
    similarity_score: float
    risk_level: str
    case_summary: str

class HistoricalCaseAssessment(BaseAssessment):
    query_summary: str
    similar_cases: List[HistoricalCaseItem] = Field(default_factory=list)
    common_patterns: List[str] = Field(default_factory=list)
    explanation: str

class RiskAssessment(BaseAssessment):
    risk_score: float
    risk_level: str  # LOW, MEDIUM, MEDIUM_HIGH, HIGH
    confidence: str  # LOW, MEDIUM, HIGH (heuristic based)
    requested_loan_amount: Optional[float] = None
    risk_factors: List[str] = Field(default_factory=list)
    positive_factors: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    similar_cases: List[str] = Field(default_factory=list)
    recommendation: str  # APPROVE_RECOMMENDATION, MANUAL_REVIEW, DECLINE_RECOMMENDATION
    explanation: Any
