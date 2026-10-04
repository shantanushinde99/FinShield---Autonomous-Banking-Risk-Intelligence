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

RISK_LEVELS = ["LOW", "MEDIUM", "MEDIUM_HIGH", "HIGH"]

class RiskDecisionAgent:
    """
    Synthesizes evidence from specialized agents using Mistral LLM to form a final risk decision.
    """
    def analyze(self, 
                context: InvestigationContext,
                profile: CustomerProfileAssessment,
                credit: CreditRiskAssessment,
                transaction: TransactionRiskAssessment,
                fraud: FraudAssessment,
                historical: HistoricalCaseAssessment) -> RiskAssessment:
                
        fc_profile = context.financial_context.profile
        # Home Credit's AMT_CREDIT is the credit amount of the loan applied for
        loan_amount = fc_profile.credit_amount if fc_profile else None

        # 1. Compile all structured evidence into a JSON prompt context
        evidence_context = {
            "investigation_id": context.investigation_id,
            "customer_id": context.financial_context.customer_id,
            "profile": profile.model_dump(),
            "credit_risk": credit.model_dump(),
            "transaction_risk": transaction.model_dump(),
            "fraud_indicators": fraud.model_dump(),
            "historical_similarities": historical.model_dump(),
            "requested_loan_amount": loan_amount
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
            "7. risk_score is on a 0-100 scale, the same scale as the agents' scores.\n"
            "8. historical_similarities.similar_default_rate is the default rate among the 50 most similar past "
            "customers; judge it against portfolio_default_rate. similar_cases lists only the closest 5 as examples, "
            "so do not count defaults in that list.\n"
            "9. Base the decision on the evidence above; do not raise concerns that no agent reported.\n"
        )
        
        try:
            logger.info("Calling Mistral LLM to synthesize final risk decision...")
            # Constructed here so a missing API key degrades to the fallback below
            result = MistralLLMService().generate_structured_response(prompt, RiskAssessment)
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            # Fallback: worst of the deterministic agent verdicts, routed to a human
            scored = [
                (credit.credit_risk_score, credit.risk_level),
                (transaction.transaction_risk_score, transaction.risk_level),
                (fraud.fraud_risk_score, fraud.risk_level),
            ]
            result = RiskAssessment(
                investigation_id=context.investigation_id,
                customer_id=context.financial_context.customer_id,
                risk_score=max(score for score, _ in scored),
                risk_level=max((level for _, level in scored), key=RISK_LEVELS.index),
                confidence="LOW",
                recommendation="MANUAL_REVIEW",
                explanation="Automated synthesis was unavailable, so this combines the rule-based agent results. Manual review required."
            )

        # Ensure identifiers are consistent with the context
        result.investigation_id = context.investigation_id
        result.customer_id = context.financial_context.customer_id
        result.requested_loan_amount = loan_amount

        # Hard compliance rule: enforced in code, not left to the LLM
        if fraud.confirmed_fraud_count > 0:
            result.risk_level = "HIGH"
            result.recommendation = "DECLINE_RECOMMENDATION"

        return result
