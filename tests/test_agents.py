import pytest
from finshield.models.domain import InvestigationContext, CustomerFinancialContext, CustomerProfile, TransactionProfile
from finshield.agents.customer import CustomerProfileAgent
from finshield.agents.credit import CreditRiskAgent
from finshield.agents.transaction import TransactionAnalysisAgent
from finshield.agents.fraud import FraudDetectionAgent

@pytest.fixture
def base_context():
    return InvestigationContext(
        investigation_id="TEST-INV",
        financial_context=CustomerFinancialContext(
            customer_id="C-1",
            profile=CustomerProfile(
                finshield_customer_id="C-1",
                age=30,
                employment_years=5,
                total_income=100000,
                bureau_total_outstanding_debt=50000,
                bureau_total_overdue=0,
                inst_payment_completion_ratio=1.0
            ),
            transaction_summary=TransactionProfile(
                account_id="A-1",
                transaction_count=10,
                total_transaction_amount=5000,
                avg_transaction_amount=500,
                transfer_count=2,
                cash_out_count=1,
                payment_count=7,
                cash_in_count=0,
                debit_count=0,
                fraud_transaction_count=0,
                fraud_ratio=0.0,
                flagged_transaction_count=0,
                avg_balance_change=100
            ),
            income_to_debt_ratio=2.0,
            has_prior_fraud_flags=False
        )
    )

def test_customer_agent(base_context):
    agent = CustomerProfileAgent()
    result = agent.analyze(base_context)
    
    assert result.customer_id == "C-1"
    assert result.data_completeness == "HIGH"
    assert any("Stable employment" in ind for ind in result.financial_stability_indicators)

def test_credit_agent_low_risk(base_context):
    agent = CreditRiskAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "LOW"
    assert result.credit_risk_score == 0.0

def test_credit_agent_high_risk(base_context):
    # Overdue debt should trigger high risk
    base_context.financial_context.profile.bureau_total_overdue = 5000
    agent = CreditRiskAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "HIGH"
    assert result.credit_risk_score >= 40.0
    
def test_transaction_agent_normal(base_context):
    agent = TransactionAnalysisAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "LOW"
    assert len(result.anomalies) == 0
    
def test_transaction_agent_anomaly(base_context):
    # High cash out ratio
    base_context.financial_context.transaction_summary.cash_out_count = 9
    agent = TransactionAnalysisAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "MEDIUM_HIGH"
    assert len(result.anomalies) == 1
    assert "cash-out" in result.anomalies[0]
    
def test_fraud_agent_clean(base_context):
    agent = FraudDetectionAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "LOW"
    assert result.confirmed_fraud_count == 0
    
def test_fraud_agent_confirmed(base_context):
    base_context.financial_context.transaction_summary.fraud_transaction_count = 2
    agent = FraudDetectionAgent()
    result = agent.analyze(base_context)
    
    assert result.risk_level == "HIGH"
    assert result.confirmed_fraud_count == 2
    assert result.fraud_risk_score == 100.0
