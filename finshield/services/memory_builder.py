from typing import Dict, Any, List
from finshield.models.domain import InvestigationContext, FinancialCase

class MemoryDocumentBuilder:
    """
    Constructs semantic memory documents and Qdrant payloads from the InvestigationContext.
    """
    
    @staticmethod
    def build_case_document(context: InvestigationContext, historical_case: FinancialCase) -> tuple[str, Dict[str, Any]]:
        """
        Takes an InvestigationContext and a specific Historical Case to build a single Memory Point.
        Returns a tuple of (semantic_text, payload_metadata).
        """
        fc = context.financial_context
        profile = fc.profile
        t_summary = fc.transaction_summary
        
        # 1. Build Payload Metadata (for filtering)
        payload = {
            "memory_type": "historical_financial_case",
            "case_id": historical_case.case_id,
            "customer_id": fc.customer_id,
            "risk_level": historical_case.risk_level,
            "overall_risk_score": historical_case.overall_risk_score,
            "transaction_risk_score": profile.transaction_risk_score if profile else None,
            "credit_risk_score": profile.credit_risk_score if profile else None,
            "fraud_transaction_count": t_summary.fraud_transaction_count if t_summary else 0,
            "transaction_count": t_summary.transaction_count if t_summary else 0,
            "total_transaction_amount": t_summary.total_transaction_amount if t_summary else 0.0,
            "income": profile.total_income if profile else None,
            "outstanding_debt": profile.bureau_total_outstanding_debt if profile else 0.0,
            "repayment_completion_ratio": profile.inst_payment_completion_ratio if profile else None,
            "has_prior_fraud_flags": fc.has_prior_fraud_flags
        }
        
        # 2. Build Semantic Text (Fixing currency encoding directly here)
        lines = []
        lines.append("FINANCIAL INVESTIGATION CASE\n")
        lines.append(f"Customer ID: {fc.customer_id}\n")
        
        if profile:
            lines.append("Profile:")
            lines.append(f"Age: {int(profile.age) if profile.age else 'Unknown'}")
            lines.append(f"Employment: {profile.employment_years:.1f} years" if profile.employment_years else "Employment: Unknown")
            lines.append(f"Occupation: {profile.occupation or 'Unknown'}")
            income_str = f"₹{profile.total_income:,.2f}" if profile.total_income else "Unknown"
            lines.append(f"Annual income: {income_str}\n")
            
            lines.append("Credit:")
            lines.append(f"Credit amount: ₹{profile.credit_amount:,.2f}" if profile.credit_amount else "Credit amount: ₹0.00")
            lines.append(f"Outstanding debt: ₹{profile.bureau_total_outstanding_debt:,.2f}" if profile.bureau_total_outstanding_debt else "Outstanding debt: ₹0.00")
            lines.append(f"Overdue amount: ₹{profile.bureau_total_overdue:,.2f}\n" if profile.bureau_total_overdue else "Overdue amount: ₹0.00\n")
            
            lines.append("Repayment:")
            comp_ratio = (profile.inst_payment_completion_ratio * 100) if profile.inst_payment_completion_ratio else 100.0
            lines.append(f"Payment completion: {comp_ratio:.0f}%")
            lines.append(f"Late payments: {int(profile.inst_late_payments) if profile.inst_late_payments else 0}\n")
            
        if t_summary:
            lines.append("Transactions:")
            lines.append(f"Transaction count: {t_summary.transaction_count}")
            lines.append(f"Total transaction volume: ₹{t_summary.total_transaction_amount:,.2f}")
            lines.append(f"Fraud transactions: {int(t_summary.fraud_transaction_count)}")
            lines.append(f"Flagged transactions: {int(t_summary.flagged_transaction_count)}")
            lines.append(f"Cash-out transactions: {int(t_summary.cash_out_count)}\n")
            
        lines.append("Risk:")
        if profile:
            lines.append(f"Credit risk score: {profile.credit_risk_score or 0:.2f}")
            lines.append(f"Transaction risk score: {profile.transaction_risk_score or 0:.2f}")
        lines.append(f"Overall risk score: {historical_case.overall_risk_score:.2f}")
        lines.append(f"Risk level: {historical_case.risk_level}\n")
        
        # We can extract text snippets from the actual case_text provided in DuckDB if we want,
        # or we just use the historical_case risk as the outcome. The DB has some text, we should include it.
        # But we must clean out bad encoding artifacts.
        cleaned_case_text = historical_case.case_text.replace("Γé╣", "₹") if historical_case.case_text else ""
        
        lines.append("Historical outcome summary:")
        lines.append(cleaned_case_text.strip())
        
        semantic_text = "\n".join(lines)
        payload["text"] = semantic_text
        
        return semantic_text, payload

    @staticmethod
    def build_query_document(context: InvestigationContext) -> str:
        """
        Builds a semantic query from a customer's context to search for similar cases.
        """
        fc = context.financial_context
        profile = fc.profile
        t_summary = fc.transaction_summary
        
        query = ["Customer profile for similarity search:"]
        if profile:
            query.append(f"Income: ₹{profile.total_income:,.2f}" if profile.total_income else "Income: Unknown")
            query.append(f"Debt: ₹{profile.bureau_total_outstanding_debt:,.2f}" if profile.bureau_total_outstanding_debt else "Debt: 0")
            comp_ratio = (profile.inst_payment_completion_ratio * 100) if profile.inst_payment_completion_ratio else 100.0
            query.append(f"Repayment rate: {comp_ratio:.0f}%")
            
        if t_summary:
            query.append(f"Total transaction volume: ₹{t_summary.total_transaction_amount:,.2f}")
            query.append(f"Prior fraud incidents: {int(t_summary.fraud_transaction_count)}")
            
        return "\n".join(query)
