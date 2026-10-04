import numpy as np
from unittest.mock import patch, MagicMock
from finshield.services import memory_builder
from finshield.services.memory_builder import MemoryDocumentBuilder, PROFILE_FEATURES, profile_vector
from finshield.models.domain import InvestigationContext, CustomerFinancialContext, CustomerProfile, TransactionProfile
from finshield.services.retrieval import FinancialMemoryService
from finshield.agents.historical import HistoricalCaseRetrievalAgent

def _fc(**profile):
    return CustomerFinancialContext(
        customer_id="C-123",
        profile=CustomerProfile(finshield_customer_id="C-123", **profile),
        transaction_summary=TransactionProfile(
            account_id="A-123", transaction_count=10, total_transaction_amount=5000.0,
            avg_transaction_amount=500.0, transfer_count=0.0, cash_out_count=2.0, payment_count=8.0,
            cash_in_count=0.0, debit_count=0.0, fraud_transaction_count=1.0, fraud_ratio=0.1,
            flagged_transaction_count=0.0, avg_balance_change=100.0,
        ),
        has_prior_fraud_flags=True,
    )

def test_memory_document_builder():
    fc = _fc(age=35.0, total_income=100000.0, bureau_total_outstanding_debt=50000.0)
    text, payload = MemoryDocumentBuilder.build_case_document(fc, "HC-123", defaulted=True)

    assert "₹100,000.00" in text # Income formatting
    assert "₹50,000.00" in text # Debt formatting
    assert "Loan outcome: DEFAULTED" in text
    # Missing repayment history must not masquerade as a perfect record
    assert "Payment completion: No history" in text

    assert payload["case_id"] == "HC-123"
    assert payload["customer_id"] == "C-123"
    assert payload["defaulted"] is True
    assert payload["has_prior_fraud_flags"] is True
    assert payload["text"] == text

def test_profile_vector_normalizes_and_imputes():
    n = len(PROFILE_FEATURES)
    stats = (np.full(n, 10.0), np.full(n, 2.0))
    with patch.object(memory_builder, "_feature_stats", return_value=stats):
        vec = profile_vector(CustomerProfile(finshield_customer_id="C-1", age=14.0, employment_years=-999.0))
    assert len(vec) == n
    assert vec[0] == 2.0        # age z-score: (14 - 10) / 2
    assert vec[1] == 0.0        # pensioner code -> missing -> population mean
    assert vec[2] == -4.5       # pensioner flag (1.0 - 10) / 2
    assert vec[3] == 0.0        # missing income -> population mean

@patch("finshield.services.retrieval.profile_vector", return_value=[0.0] * 11)
@patch("finshield.services.retrieval.get_qdrant_client")
def test_search_excludes_self_and_filters_fraud(MockQdrant, _vec):
    mock_qdrant = MockQdrant.return_value
    hit = MagicMock(score=1.0, payload={"case_id": "CASE-99", "defaulted": True, "text": "summary"})
    mock_qdrant.query_points.return_value = MagicMock(points=[hit])

    context = InvestigationContext(investigation_id="TEST-1", financial_context=_fc(age=35.0))
    results = FinancialMemoryService().search_similar_cases_for_customer(context, limit=5)

    assert results == [{"case_id": "CASE-99", "similarity_score": 0.5, "defaulted": True,
                        "metadata": hit.payload, "case_summary": "summary"}]
    query_filter = mock_qdrant.query_points.call_args.kwargs["query_filter"]
    assert query_filter.must_not[0].key == "customer_id"
    assert query_filter.must_not[0].match.value == "C-123"
    assert query_filter.must[0].key == "has_prior_fraud_flags"

@patch("finshield.agents.historical.FinancialMemoryService")
def test_historical_agent_reports_default_rate(MockService):
    service = MockService.return_value
    service.search_similar_cases_for_customer.return_value = [
        {"case_id": f"C{i}", "similarity_score": 0.9, "defaulted": i < 3, "case_summary": "s"} for i in range(10)
    ]
    service.portfolio_default_rate.return_value = 0.08

    context = InvestigationContext(investigation_id="TEST-1", financial_context=_fc(age=35.0))
    result = HistoricalCaseRetrievalAgent().analyze(context)

    assert len(result.similar_cases) == HistoricalCaseRetrievalAgent.SHOWN_CASES
    assert result.similar_cases[0].outcome == "DEFAULTED"
    assert result.similar_default_rate == 0.3
    assert result.common_patterns == ["3 of the 10 most similar past customers defaulted (30% vs 8% portfolio average)"]
