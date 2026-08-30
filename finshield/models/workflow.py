from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field
import uuid
import time

from finshield.models.domain import InvestigationContext
from finshield.models.agents import (
    CustomerProfileAssessment,
    CreditRiskAssessment,
    TransactionRiskAssessment,
    FraudAssessment,
    HistoricalCaseAssessment,
    RiskAssessment
)

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExecutionStep(BaseModel):
    tool_name: str
    status: ExecutionStatus
    started_at: float
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
class InvestigationState(BaseModel):
    investigation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: InvestigationContext
    
    # Optional assessments populated during the workflow execution
    profile: Optional[CustomerProfileAssessment] = None
    credit: Optional[CreditRiskAssessment] = None
    transactions: Optional[TransactionRiskAssessment] = None
    fraud: Optional[FraudAssessment] = None
    historical: Optional[HistoricalCaseAssessment] = None
    
    # Final synthesized outcome
    final_decision: Optional[RiskAssessment] = None
    
    # Execution tracing
    trace: List[ExecutionStep] = Field(default_factory=list)
    
    def log_tool_start(self, tool_name: str) -> None:
        self.trace.append(ExecutionStep(
            tool_name=tool_name,
            status=ExecutionStatus.RUNNING,
            started_at=time.time()
        ))
        
    def log_tool_end(self, tool_name: str, status: ExecutionStatus, error: Optional[str] = None) -> None:
        for step in reversed(self.trace):
            if step.tool_name == tool_name and step.status == ExecutionStatus.RUNNING:
                step.status = status
                step.completed_at = time.time()
                step.duration_ms = (step.completed_at - step.started_at) * 1000
                step.error = error
                break
