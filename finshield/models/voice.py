from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

from finshield.models.workflow import InvestigationState

class VoiceSessionState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    INVESTIGATING = "INVESTIGATING"
    COMPLETED = "COMPLETED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    FAILED = "FAILED"

# --- Internal Voice Models ---

class VoiceTranscript(BaseModel):
    """Normalized internal transcript (built from Omi webhook segments)"""
    text: str = Field(..., description="The recognized transcript text")
    session_id: str = Field(default="default_session", description="Omi session identifier")
    speaker: Optional[str] = Field(None, description="Speaker identifier if available")
    is_final: bool = Field(default=True, description="Whether this is a final transcript segment")

class VoiceInvestigationRequest(BaseModel):
    """The normalized investigation command extracted from voice"""
    session_id: str
    customer_id: str
    command: str
    intent: str = "RISK_INVESTIGATION"

class VoiceResponse(BaseModel):
    """The concise response meant to be spoken back to the user"""
    status: str
    investigation_id: Optional[str] = None
    customer_id: Optional[str] = None
    risk_level: Optional[str] = None
    recommendation: Optional[str] = None
    spoken_summary: str
    confidence: Optional[str] = None

class VoiceSession(BaseModel):
    """Tracks the state of an active voice interaction"""
    session_id: str
    state: VoiceSessionState = VoiceSessionState.IDLE
    customer_id: Optional[str] = None
    investigation_id: Optional[str] = None
    last_transcript: Optional[str] = None
    last_response: Optional[VoiceResponse] = None
    # Full result of the last voice-triggered investigation, served to the dashboard
    last_state: Optional[InvestigationState] = None
