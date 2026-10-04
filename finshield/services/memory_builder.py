import math
from functools import lru_cache
from typing import Dict, Any, List, Optional

import numpy as np

from finshield.database.connection import get_duckdb_connection
from finshield.models.domain import CustomerFinancialContext, CustomerProfile


def _log(x: Optional[float]) -> Optional[float]:
    return math.log1p(max(x, 0.0)) if x is not None else None

# Profile features used for similarity. Money is log-scaled so a ₹10M outlier doesn't
# dominate; negative employment_years is Home Credit's pensioner / no-employer code.
PROFILE_FEATURES = [
    lambda p: p.age,
    lambda p: p.employment_years if p.employment_years is not None and p.employment_years >= 0 else None,
    lambda p: float(p.employment_years is not None and p.employment_years < 0),
    lambda p: _log(p.total_income),
    lambda p: _log(p.credit_amount),
    lambda p: _log(p.annuity),
    lambda p: _log(p.bureau_total_outstanding_debt),
    lambda p: _log(p.bureau_total_overdue),
    lambda p: _log(p.inst_late_payments),
    lambda p: p.inst_payment_completion_ratio,
    lambda p: p.credit_risk_score,
]


def _raw_features(profile: CustomerProfile) -> List[Optional[float]]:
    return [f(profile) for f in PROFILE_FEATURES]


@lru_cache(maxsize=1)
def _feature_stats():
    """Population mean/std per feature, from the same table at ingest and query time."""
    with get_duckdb_connection() as con:
        rows = con.execute("SELECT * FROM finshield_customer_profiles").fetchall()
        cols = [desc[0] for desc in con.description]
    matrix = np.array([_raw_features(CustomerProfile(**dict(zip(cols, r)))) for r in rows], dtype=float)
    return np.nanmean(matrix, axis=0), np.nanstd(matrix, axis=0)


def profile_vector(profile: CustomerProfile) -> List[float]:
    """Z-scored feature vector; missing values sit at the population mean."""
    mean, std = _feature_stats()
    x = np.array(_raw_features(profile), dtype=float)
    z = np.where(np.isnan(x), 0.0, (x - mean) / np.where(std > 0, std, 1.0))
    return np.clip(z, -5, 5).tolist()


class MemoryDocumentBuilder:
    """
    Constructs case-memory documents and Qdrant payloads for past customers.
    """

    @staticmethod
    def build_case_document(fc: CustomerFinancialContext, case_id: str, defaulted: bool) -> tuple[str, Dict[str, Any]]:
        """
        Builds a single Memory Point for a past customer with a known loan outcome.
        Returns a tuple of (summary_text, payload_metadata).
        """
        profile = fc.profile
        t_summary = fc.transaction_summary

        # 1. Build Payload Metadata (for filtering)
        payload = {
            "case_id": case_id,
            "customer_id": fc.customer_id,
            "defaulted": defaulted,
            "has_prior_fraud_flags": fc.has_prior_fraud_flags,
            "fraud_transaction_count": t_summary.fraud_transaction_count if t_summary else 0,
            "income": profile.total_income if profile else None,
            "outstanding_debt": profile.bureau_total_outstanding_debt if profile else 0.0,
            "repayment_completion_ratio": profile.inst_payment_completion_ratio if profile else None,
        }

        # 2. Build Summary Text (the dashboard parses the labelled lines below)
        lines = []
        lines.append("FINANCIAL INVESTIGATION CASE\n")
        lines.append(f"Customer ID: {fc.customer_id}\n")

        if profile:
            lines.append("Profile:")
            lines.append(f"Age: {int(profile.age) if profile.age else 'Unknown'}")
            lines.append(f"Employment: {profile.employment_years:.1f} years" if profile.employment_years and profile.employment_years >= 0 else "Employment: Unknown")
            lines.append(f"Occupation: {profile.occupation or 'Unknown'}")
            income_str = f"₹{profile.total_income:,.2f}" if profile.total_income else "Unknown"
            lines.append(f"Annual income: {income_str}\n")

            lines.append("Credit:")
            lines.append(f"Credit amount: ₹{profile.credit_amount or 0:,.2f}")
            lines.append(f"Outstanding debt: ₹{profile.bureau_total_outstanding_debt or 0:,.2f}")
            lines.append(f"Overdue amount: ₹{profile.bureau_total_overdue or 0:,.2f}\n")

            lines.append("Repayment:")
            if profile.inst_payment_completion_ratio is not None:
                lines.append(f"Payment completion: {profile.inst_payment_completion_ratio * 100:.0f}%")
            else:
                lines.append("Payment completion: No history")
            lines.append(f"Late payments: {int(profile.inst_late_payments) if profile.inst_late_payments else 0}\n")

        if t_summary:
            lines.append("Transactions:")
            lines.append(f"Transaction count: {t_summary.transaction_count}")
            lines.append(f"Total transaction volume: ₹{t_summary.total_transaction_amount:,.2f}")
            lines.append(f"Fraud transactions: {int(t_summary.fraud_transaction_count)}")
            lines.append(f"Flagged transactions: {int(t_summary.flagged_transaction_count)}")
            lines.append(f"Cash-out transactions: {int(t_summary.cash_out_count)}\n")

        lines.append(f"Loan outcome: {'DEFAULTED' if defaulted else 'REPAID'}")

        text = "\n".join(lines)
        payload["text"] = text
        return text, payload
