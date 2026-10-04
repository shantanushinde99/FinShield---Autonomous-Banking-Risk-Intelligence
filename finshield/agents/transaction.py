from finshield.models.domain import InvestigationContext
from finshield.models.agents import TransactionRiskAssessment, Evidence

class TransactionAnalysisAgent:
    """
    Deterministically evaluates transaction patterns, focusing on anomalies and behavioral shifts.
    """
    # A ratio over 1-2 transactions is noise: in the current dataset 99.9% of accounts
    # have a single transaction, so a lone cash-out would otherwise read as "100% cash-out".
    MIN_TXNS_FOR_PATTERNS = 5
    
    def analyze(self, context: InvestigationContext) -> TransactionRiskAssessment:
        t_summary = context.financial_context.transaction_summary
        
        score = 0.0
        risk_level = "LOW"
        anomalies = []
        behavioral_indicators = []
        positive_indicators = []
        evidence = []
        
        if not t_summary:
            return TransactionRiskAssessment(
                investigation_id=context.investigation_id,
                customer_id=context.financial_context.customer_id,
                transaction_risk_score=0.0,
                risk_level="LOW",
                explanation="No transaction history available for analysis."
            )
            
        # Cash-out anomaly check
        if 0 < t_summary.transaction_count < self.MIN_TXNS_FOR_PATTERNS:
            behavioral_indicators.append(
                f"Insufficient history to assess cash-out patterns "
                f"({t_summary.transaction_count} transaction{'s' if t_summary.transaction_count != 1 else ''})"
            )
        elif t_summary.transaction_count >= self.MIN_TXNS_FOR_PATTERNS:
            cash_out_ratio = t_summary.cash_out_count / t_summary.transaction_count
            if cash_out_ratio > 0.8:
                anomalies.append(f"Unusually high proportion of cash-out transactions ({cash_out_ratio*100:.0f}%)")
                score += 30.0
                risk_level = "MEDIUM_HIGH"
                evidence.append(Evidence(
                    source_type="duckdb",
                    source_id=t_summary.account_id,
                    description="Cash-out Ratio",
                    value=cash_out_ratio,
                    relevance="HIGH"
                ))
            elif cash_out_ratio < 0.2:
                positive_indicators.append("Low cash-out velocity indicating stable holding behavior")
                
        # Volume anomaly check (heuristic for unusual volume)
        if t_summary.total_transaction_amount > 1_000_000:
            behavioral_indicators.append(f"High total transaction volume: ₹{t_summary.total_transaction_amount:,.2f}")
            
        # Missing or dormant account
        if t_summary.transaction_count == 0:
            behavioral_indicators.append("Dormant account with zero transactions")
        elif t_summary.transaction_count > 50:
            behavioral_indicators.append(f"High transaction frequency ({t_summary.transaction_count} transactions)")
            
        # Final scoring caps
        score = min(score, 100.0)
        
        return TransactionRiskAssessment(
            investigation_id=context.investigation_id,
            customer_id=context.financial_context.customer_id,
            transaction_risk_score=score,
            risk_level=risk_level,
            behavioral_indicators=behavioral_indicators,
            anomalies=anomalies,
            positive_indicators=positive_indicators,
            evidence=evidence,
            explanation="Transaction behavior evaluated based on volume, frequency, and cash-out patterns."
        )
