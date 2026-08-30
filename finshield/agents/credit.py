from finshield.models.domain import InvestigationContext
from finshield.models.agents import CreditRiskAssessment, Evidence

class CreditRiskAgent:
    """
    Deterministically evaluates credit risk based on debt metrics and repayment history.
    """
    
    def analyze(self, context: InvestigationContext) -> CreditRiskAssessment:
        fc = context.financial_context
        profile = fc.profile
        
        risk_level = "LOW"
        score = 0.0
        key_factors = []
        positive_factors = []
        evidence = []
        metrics = {}
        
        if not profile:
            return CreditRiskAssessment(
                investigation_id=context.investigation_id,
                customer_id=fc.customer_id,
                credit_risk_score=50.0,
                risk_level="MEDIUM",
                explanation="No credit profile data available to assess risk."
            )
            
        metrics["outstanding_debt"] = profile.bureau_total_outstanding_debt or 0.0
        metrics["credit_amount"] = profile.credit_amount or 0.0
        metrics["overdue_amount"] = profile.bureau_total_overdue or 0.0
        
        # Evidence Gathering
        if metrics["overdue_amount"] > 0:
            evidence.append(Evidence(
                source_type="duckdb",
                source_id=fc.customer_id,
                description="Bureau Total Overdue",
                value=metrics["overdue_amount"],
                relevance="HIGH"
            ))
            key_factors.append(f"Customer has overdue debt: ₹{metrics['overdue_amount']:,.2f}")
            score += 40.0
            risk_level = "HIGH"
            
        # Repayment ratio
        if profile.inst_payment_completion_ratio is not None:
            ratio = profile.inst_payment_completion_ratio
            metrics["payment_completion_ratio"] = ratio
            if ratio >= 0.95:
                positive_factors.append(f"Strong payment completion history ({ratio*100:.0f}%)")
            elif ratio < 0.8:
                key_factors.append(f"Poor payment completion history ({ratio*100:.0f}%)")
                score += 20.0
                if risk_level != "HIGH":
                    risk_level = "MEDIUM_HIGH"
                    
        # Income to Debt Ratio
        if fc.income_to_debt_ratio is not None:
            ratio = fc.income_to_debt_ratio
            if ratio < 0.3 and metrics["outstanding_debt"] > 0:
                key_factors.append(f"High debt burden relative to income (Ratio: {ratio:.2f})")
                score += 20.0
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
            elif ratio > 2.0:
                positive_factors.append(f"Strong income to debt coverage (Ratio: {ratio:.2f})")
                
        # Existing credit risk score mapping (if any)
        if profile.credit_risk_score:
            metrics["bureau_credit_risk_score"] = profile.credit_risk_score
            if profile.credit_risk_score > 30.0:
                score += 10.0
                
        # Final capping and heuristics
        score = min(score, 100.0)
        
        if score == 0.0 and len(key_factors) == 0:
            explanation = "Customer demonstrates strong credit characteristics with no identified risk factors."
        else:
            explanation = "Credit risk evaluated based on current debt exposure and historical repayment behavior."
            
        return CreditRiskAssessment(
            investigation_id=context.investigation_id,
            customer_id=fc.customer_id,
            credit_risk_score=score,
            risk_level=risk_level,
            key_factors=key_factors,
            positive_factors=positive_factors,
            metrics=metrics,
            evidence=evidence,
            explanation=explanation
        )
