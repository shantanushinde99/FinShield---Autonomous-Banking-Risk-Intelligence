import pytest
from unittest.mock import patch, MagicMock
from finshield.services.memory_builder import MemoryDocumentBuilder
from finshield.models.domain import InvestigationContext, CustomerFinancialContext, CustomerProfile, TransactionProfile, FinancialCase
from finshield.services.retrieval import FinancialMemoryService

def test_memory_document_builder():
    context = InvestigationContext(
        investigation_id="TEST-1",
        financial_context=CustomerFinancialContext(
            customer_id="C-123",
            profile=CustomerProfile(
                finshield_customer_id="C-123",
                age=35.0,
                total_income=100000.0,
                bureau_total_outstanding_debt=50000.0,
                credit_risk_score=0.5,
                transaction_risk_score=1.2,
            ),
            transaction_summary=TransactionProfile(
                account_id="A-123",
                transaction_count=10,
                total_transaction_amount=5000.0,
                avg_transaction_amount=500.0,
                transfer_count=0.0,
                cash_out_count=2.0,
                payment_count=8.0,
                cash_in_count=0.0,
                debit_count=0.0,
                fraud_transaction_count=1.0,
                fraud_ratio=0.1,
                flagged_transaction_count=0.0,
                avg_balance_change=100.0
            ),
            has_prior_fraud_flags=True
        )
    )
    
    # Include corrupt currency symbol to test cleanup
    historical_case = FinancialCase(
        case_id="HC-123",
        finshield_customer_id="C-123",
        case_text="Test outcome. Γé╣100 debt.",
        overall_risk_score=1.7,
        risk_level="MEDIUM"
    )
    
    text, payload = MemoryDocumentBuilder.build_case_document(context, historical_case)
    
    assert "₹100,000.00" in text # Income formatting
    assert "₹50,000.00" in text # Debt formatting
    assert "Γé╣" not in text
    assert "₹100" in text # Text normalization
    
    assert payload["memory_type"] == "historical_financial_case"
    assert payload["case_id"] == "HC-123"
    assert payload["customer_id"] == "C-123"
    assert payload["risk_level"] == "MEDIUM"
    assert payload["fraud_transaction_count"] == 1.0
    assert payload["has_prior_fraud_flags"] is True
    assert "text" in payload

@patch("finshield.services.retrieval.get_qdrant_client")
@patch("finshield.services.retrieval.MistralEmbeddingService")
def test_financial_memory_service_search(MockEmbedder, MockQdrant):
    mock_qdrant = MagicMock()
    MockQdrant.return_value = mock_qdrant
    
    mock_embedder = MagicMock()
    mock_embedder.embed_text.return_value = [0.1] * 1024
    MockEmbedder.return_value = mock_embedder
    
    mock_hit = MagicMock()
    mock_hit.score = 0.95
    mock_hit.payload = {
        "case_id": "CASE-99",
        "risk_level": "HIGH",
        "text": "Detailed case text here"
    }
    
    mock_response = MagicMock()
    mock_response.points = [mock_hit]
    mock_qdrant.query_points.return_value = mock_response

    service = FinancialMemoryService()
    results = service.search_similar_cases("test query")

    assert len(results) == 1
    assert results[0]["case_id"] == "CASE-99"
    assert results[0]["similarity_score"] == 0.95
    assert results[0]["risk_level"] == "HIGH"
    
    # Verify qdrant was called correctly
    mock_qdrant.query_points.assert_called_once()
    mock_embedder.embed_text.assert_called_once_with("test query")
