import uuid
from typing import Optional

from finshield.models.domain import InvestigationContext, CustomerFinancialContext
from finshield.data.repositories import CustomerRepository, TransactionRepository, CaseRepository
from finshield.exceptions import CustomerNotFoundError

from finshield.models.workflow import InvestigationState
from finshield.orchestration.lyzr_workflow import FinShieldOrchestrator

class InvestigationContextService:
    @staticmethod
    def build_context(customer_id: str, investigation_id: Optional[str] = None) -> InvestigationContext:
        """
        Assembles a comprehensive InvestigationContext for a given customer.
        """
        if not investigation_id:
            investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"

        # 1. Base Customer
        customer = CustomerRepository.get_customer(customer_id)
        
        # 2. Customer Profile
        profile = CustomerRepository.get_customer_profile(customer_id)
        
        # 3. Transaction Data
        transaction_summary = None
        recent_transactions = []
        if customer.account_id:
            transaction_summary = TransactionRepository.get_transaction_profile(customer.account_id)
            recent_transactions = TransactionRepository.get_recent_transactions(customer.account_id, limit=50)

        # 4. Historical Cases
        cases = CaseRepository.get_customer_cases(customer_id)

        # 5. Derived Metrics Calculation
        total_exposure = 0.0
        income_to_debt_ratio = None
        has_prior_fraud_flags = False

        if profile:
            if profile.bureau_total_outstanding_debt:
                total_exposure += profile.bureau_total_outstanding_debt
            if profile.credit_amount:
                total_exposure += profile.credit_amount
                
            if profile.total_income and profile.total_income > 0 and total_exposure > 0:
                income_to_debt_ratio = total_exposure / profile.total_income
                
        if transaction_summary:
            if transaction_summary.fraud_transaction_count > 0 or transaction_summary.flagged_transaction_count > 0:
                has_prior_fraud_flags = True

        financial_context = CustomerFinancialContext(
            customer_id=customer_id,
            profile=profile,
            transaction_summary=transaction_summary,
            recent_transactions=recent_transactions,
            historical_cases=cases,
            total_exposure=total_exposure,
            income_to_debt_ratio=income_to_debt_ratio,
            has_prior_fraud_flags=has_prior_fraud_flags
        )

        return InvestigationContext(
            investigation_id=investigation_id,
            financial_context=financial_context
        )


class InvestigationWorkflowService:
    """
    Service to run the end-to-end investigation workflow.
    """
    def __init__(self):
        self.orchestrator = FinShieldOrchestrator()
        
    def run_investigation(self, customer_id: str) -> InvestigationState:
        # 1. Build Context
        context = InvestigationContextService.build_context(customer_id)
        
        # 2. Initialize Workflow State
        state = InvestigationState(
            investigation_id=context.investigation_id,
            context=context
        )
        
        # 3. Run the Lyzr Orchestrated Workflow
        final_state = self.orchestrator.run_investigation_workflow(state)
        return final_state
