import pytest
from finshield.exceptions import CustomerNotFoundError
from finshield.data.repositories import CustomerRepository, TransactionRepository, CaseRepository
from finshield.services.investigation import InvestigationContextService

# Using a known ID from the database for testing read-only logic
TEST_CUSTOMER_ID = "FIN_000001"
INVALID_CUSTOMER_ID = "FIN_INVALID_999"

def test_get_customer_success():
    customer = CustomerRepository.get_customer(TEST_CUSTOMER_ID)
    assert customer is not None
    assert customer.finshield_customer_id == TEST_CUSTOMER_ID
    assert customer.account_id is not None

def test_get_customer_not_found():
    with pytest.raises(CustomerNotFoundError):
        CustomerRepository.get_customer(INVALID_CUSTOMER_ID)

def test_get_customer_profile():
    profile = CustomerRepository.get_customer_profile(TEST_CUSTOMER_ID)
    assert profile is not None
    assert profile.finshield_customer_id == TEST_CUSTOMER_ID

def test_get_customer_profile_not_found():
    profile = CustomerRepository.get_customer_profile(INVALID_CUSTOMER_ID)
    assert profile is None

def test_transaction_repository():
    customer = CustomerRepository.get_customer(TEST_CUSTOMER_ID)
    
    if customer.account_id:
        profile = TransactionRepository.get_transaction_profile(customer.account_id)
        if profile:
            assert profile.account_id == customer.account_id
            
        recent = TransactionRepository.get_recent_transactions(customer.account_id, limit=5)
        assert isinstance(recent, list)
        assert len(recent) <= 5

def test_case_repository():
    cases = CaseRepository.get_customer_cases(TEST_CUSTOMER_ID)
    assert isinstance(cases, list)

def test_investigation_service_build_context():
    context = InvestigationContextService.build_context(TEST_CUSTOMER_ID)
    assert context is not None
    assert context.investigation_id.startswith("INV-")
    
    fc = context.financial_context
    assert fc.customer_id == TEST_CUSTOMER_ID
    assert fc.profile is not None
    
    # Check derived metrics
    assert isinstance(fc.total_exposure, float)
    assert isinstance(fc.has_prior_fraud_flags, bool)

def test_investigation_service_invalid_customer():
    with pytest.raises(CustomerNotFoundError):
        InvestigationContextService.build_context(INVALID_CUSTOMER_ID)
