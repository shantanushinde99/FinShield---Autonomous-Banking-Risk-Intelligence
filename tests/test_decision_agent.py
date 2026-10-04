from unittest.mock import patch
import pytest

from finshield.agents.decision import RiskDecisionAgent
from finshield.models.agents import (
    CustomerProfileAssessment, CreditRiskAssessment, TransactionRiskAssessment,
    FraudAssessment, HistoricalCaseAssessment, RiskAssessment,
)
from finshield.models.domain import InvestigationContext, CustomerFinancialContext, CustomerProfile

IDS = dict(investigation_id="INV-1", customer_id="C-1")

def _inputs(confirmed_fraud=0):
    context = InvestigationContext(investigation_id="INV-1", financial_context=CustomerFinancialContext(
        customer_id="C-1", profile=CustomerProfile(finshield_customer_id="C-1", credit_amount=250000.0)))
    return (
        context,
        CustomerProfileAssessment(**IDS, data_completeness="HIGH"),
        CreditRiskAssessment(**IDS, credit_risk_score=20.0, risk_level="MEDIUM", explanation=""),
        TransactionRiskAssessment(**IDS, transaction_risk_score=30.0, risk_level="MEDIUM_HIGH", explanation=""),
        FraudAssessment(**IDS, fraud_risk_score=100.0 if confirmed_fraud else 0.0,
                        risk_level="HIGH" if confirmed_fraud else "LOW",
                        confirmed_fraud_count=confirmed_fraud, flagged_count=0, explanation=""),
        HistoricalCaseAssessment(**IDS, query_summary="", explanation=""),
    )

@patch("finshield.agents.decision.MistralLLMService")
def test_fallback_uses_worst_deterministic_verdict(mock_llm):
    mock_llm.return_value.generate_structured_response.side_effect = RuntimeError("LLM down")
    result = RiskDecisionAgent().analyze(*_inputs())
    assert result.risk_level == "MEDIUM_HIGH"
    assert result.risk_score == 30.0
    assert result.recommendation == "MANUAL_REVIEW"
    assert result.requested_loan_amount == 250000.0

@patch("finshield.agents.decision.MistralLLMService")
def test_confirmed_fraud_overrides_llm(mock_llm):
    mock_llm.return_value.generate_structured_response.return_value = RiskAssessment(
        investigation_id="x", customer_id="x", risk_score=10.0, risk_level="LOW",
        confidence="HIGH", recommendation="APPROVE_RECOMMENDATION", explanation="looks fine")
    result = RiskDecisionAgent().analyze(*_inputs(confirmed_fraud=2))
    assert result.risk_level == "HIGH"
    assert result.recommendation == "DECLINE_RECOMMENDATION"
    assert (result.investigation_id, result.customer_id) == ("INV-1", "C-1")

def test_off_spec_llm_values_are_rejected():
    with pytest.raises(ValueError):
        RiskAssessment(**IDS, risk_score=1.0, risk_level="VERY HIGH", confidence="HIGH",
                       recommendation="APPROVE_RECOMMENDATION", explanation="")
