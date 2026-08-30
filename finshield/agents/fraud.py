from finshield.models.domain import InvestigationContext
from finshield.models.agents import FraudAssessment, Evidence

class FraudDetectionAgent:
    """
    Deterministically evaluates hard fraud evidence such as confirmed fraud and flagged transactions.
    """
    
    def analyze(self, context: InvestigationContext) -> FraudAssessment:
        t_summary = context.financial_context.transaction_summary
        
        score = 0.0
        risk_level = "LOW"
        suspicious_patterns = []
        evidence = []
        confirmed = 0
        flagged = 0
        
        if not t_summary:
            return FraudAssessment(
                investigation_id=context.investigation_id,
                customer_id=context.financial_context.customer_id,
                fraud_risk_score=0.0,
                risk_level="LOW",
                confirmed_fraud_count=0,
                flagged_count=0,
                explanation="No transaction history to evaluate for fraud."
            )
            
        confirmed = int(t_summary.fraud_transaction_count)
        flagged = int(t_summary.flagged_transaction_count)
        
        # Hard Fraud Check
        if confirmed > 0:
            score += 100.0
            risk_level = "HIGH"
            suspicious_patterns.append("Confirmed fraudulent transactions exist in account history.")
            evidence.append(Evidence(
                source_type="duckdb",
                source_id=t_summary.account_id,
                description="Confirmed Fraud Count",
                value=confirmed,
                relevance="CRITICAL"
            ))
            
        # Flagged Check (Suspicious but not confirmed)
        if flagged > 0 and confirmed == 0:
            score += 50.0
            if risk_level != "HIGH":
                risk_level = "MEDIUM_HIGH"
            suspicious_patterns.append("Transactions have been previously flagged by system rules.")
            evidence.append(Evidence(
                source_type="duckdb",
                source_id=t_summary.account_id,
                description="Flagged Transaction Count",
                value=flagged,
                relevance="HIGH"
            ))
            
        # Heuristic rules
        if context.financial_context.has_prior_fraud_flags:
            if "Prior fraud flags detected." not in suspicious_patterns:
                suspicious_patterns.append("Prior fraud flags detected.")
                
        explanation = "Fraud evaluation based on confirmed instances and flagged patterns."
        if score == 0.0:
            explanation = "No confirmed or flagged fraud incidents found in account history."
            
        return FraudAssessment(
            investigation_id=context.investigation_id,
            customer_id=context.financial_context.customer_id,
            fraud_risk_score=score,
            risk_level=risk_level,
            confirmed_fraud_count=confirmed,
            flagged_count=flagged,
            suspicious_patterns=suspicious_patterns,
            evidence=evidence,
            explanation=explanation
        )
