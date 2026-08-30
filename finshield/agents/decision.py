import logging
from finshield.models.domain import InvestigationContext
from finshield.models.agents import (
    CustomerProfileAssessment,
    CreditRiskAssessment,
    TransactionRiskAssessment,
    FraudAssessment,
    HistoricalCaseAssessment,
    RiskAssessment
)
from finshield.services.llm import MistralLLMService

logger = logging.getLogger(__name__)

class RiskDecisionAgent:
    """
    Synthesizes evidence from specialized agents using Mistral LLM to form a final risk decision.
    """
    def __init__(self):
        self.llm_service = MistralLLMService()
        
    def analyze(self, 
                context: InvestigationContext,
                profile: CustomerProfileAssessment,
                credit: CreditRiskAssessment,
                transaction: TransactionRiskAssessment,
                fraud: FraudAssessment,
                historical: HistoricalCaseAssessment) -> RiskAssessment:
                
        # 1. Compile all structured evidence into a JSON prompt context
        evidence_context = {
            "investigation_id": context.investigation_id,
            "customer_id": context.financial_context.customer_id,
            "profile": profile.model_dump(),
            "credit_risk": credit.model_dump(),
            "transaction_risk": transaction.model_dump(),
            "fraud_indicators": fraud.model_dump(),
            "historical_similarities": historical.model_dump(),
            "requested_loan_amount": 100000.0 # Placeholder or derived from application context
        }
        
        prompt = (
            "You are evaluating a bank customer for financial risk.\n\n"
            "Below is the structured evidence collected by 5 specialized deterministic agents:\n"
            "=== EVIDENCE START ===\n"
            f"{evidence_context}\n"
            "=== EVIDENCE END ===\n\n"
            "Based on the evidence above, synthesize a final RiskAssessment.\n"
            "Rules:\n"
            "1. Output MUST be valid JSON adhering to the provided schema.\n"
            "2. risk_level must be exactly one of: 'LOW', 'MEDIUM', 'MEDIUM_HIGH', 'HIGH'.\n"
            "3. confidence must be exactly one of: 'LOW', 'MEDIUM', 'HIGH'. (Consider data completeness and historical alignment).\n"
            "4. recommendation must be exactly one of: 'APPROVE_RECOMMENDATION', 'MANUAL_REVIEW', 'DECLINE_RECOMMENDATION'.\n"
            "5. If there is confirmed fraud, recommendation MUST be DECLINE_RECOMMENDATION and risk_level HIGH.\n"
            "6. Provide a clear, concise explanation suitable for a human bank officer.\n"
        )
        
        try:
            logger.info("Calling Mistral LLM to synthesize final risk decision...")
            result = self.llm_service.generate_structured_response(prompt, RiskAssessment)
            
            # Ensure identifiers are consistent with the context
            result.investigation_id = context.investigation_id
            result.customer_id = context.financial_context.customer_id
            
            return result
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            # Fallback deterministic response in case of LLM failure
            return RiskAssessment(
                investigation_id=context.investigation_id,
                customer_id=context.financial_context.customer_id,
                risk_score=99.0,
                risk_level="HIGH",
                confidence="LOW",
                recommendation="MANUAL_REVIEW",
                explanation=f"LLM Synthesis failed. Falling back to manual review. Error: {str(e)}"
            )
