from pydantic import BaseModel, Field
from typing import Optional, List

class Customer(BaseModel):
    finshield_customer_id: str
    sk_id_curr: Optional[int] = Field(None, alias="SK_ID_CURR")
    account_id: Optional[str] = None
    synthetic_dataset_mapping: bool

class CustomerProfile(BaseModel):
    finshield_customer_id: str
    gender: Optional[str] = None
    owns_car: Optional[str] = None
    owns_realty: Optional[str] = None
    children: Optional[int] = None
    total_income: Optional[float] = None
    credit_amount: Optional[float] = None
    annuity: Optional[float] = None
    income_type: Optional[str] = None
    education: Optional[str] = None
    family_status: Optional[str] = None
    housing_type: Optional[str] = None
    age: Optional[float] = None
    employment_years: Optional[float] = None
    occupation: Optional[str] = None
    
    # Credit History Risk indicators
    bureau_total_outstanding_debt: Optional[float] = None
    bureau_total_overdue: Optional[float] = None
    inst_late_payments: Optional[float] = None
    inst_payment_completion_ratio: Optional[float] = None
    
    # Risk scores
    credit_risk_score: Optional[float] = None
    transaction_risk_score: Optional[float] = None
    overall_risk_score: Optional[float] = None
    risk_level: Optional[str] = None

class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    name_orig: str
    new_balance_orig: float
    name_dest: str
    new_balance_dest: float
    is_fraud: int
    is_flagged_fraud: int

class TransactionProfile(BaseModel):
    account_id: str
    transaction_count: int
    total_transaction_amount: float
    avg_transaction_amount: float
    transfer_count: float
    cash_out_count: float
    payment_count: float
    cash_in_count: float
    debit_count: float
    fraud_transaction_count: float
    fraud_ratio: float
    flagged_transaction_count: float
    avg_balance_change: float

class FinancialCase(BaseModel):
    case_id: str
    finshield_customer_id: str
    case_text: str
    overall_risk_score: float
    risk_level: str

class CustomerFinancialContext(BaseModel):
    """
    Synthesized financial summary for an investigation.
    """
    customer_id: str
    profile: Optional[CustomerProfile] = None
    transaction_summary: Optional[TransactionProfile] = None
    recent_transactions: List[Transaction] = Field(default_factory=list)
    historical_cases: List[FinancialCase] = Field(default_factory=list)
    
    # Derived metrics calculated at investigation time
    total_exposure: float = 0.0
    income_to_debt_ratio: Optional[float] = None
    has_prior_fraud_flags: bool = False
    
class InvestigationContext(BaseModel):
    """
    Wrapper context consumed by Lyzr agents.
    """
    investigation_id: str
    financial_context: CustomerFinancialContext
