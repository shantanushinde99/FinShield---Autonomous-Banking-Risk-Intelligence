from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

class VoiceSessionState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    INVESTIGATING = "INVESTIGATING"
    COMPLETED = "COMPLETED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    FAILED = "FAILED"

# --- Omi Webhook Payload Models ---

class OmiTranscriptSegment(BaseModel):
    """A single transcript segment from Omi's memory payload"""
    text: str = ""
    speaker: Optional[str] = None
    speakerId: Optional[int] = None
    speaker_name: Optional[str] = None
    is_user: bool = False
    start: Optional[float] = None
    end: Optional[float] = None

class OmiActionItem(BaseModel):
    description: str = ""
    completed: bool = False

class OmiStructured(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    emoji: Optional[str] = None
    category: Optional[str] = None
    action_items: List[OmiActionItem] = Field(default_factory=list)

class OmiMemoryPayload(BaseModel):
    """The full memory object Omi sends to our webhook when a memory is created"""
    id: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    transcript_segments: List[OmiTranscriptSegment] = Field(default_factory=list)
    structured: Optional[OmiStructured] = None
    discarded: bool = False

    def get_full_transcript(self) -> str:
        """Combines all transcript segments into a single string"""
        return " ".join(seg.text for seg in self.transcript_segments if seg.text).strip()

# --- Internal Voice Models ---

class VoiceTranscript(BaseModel):
    """Normalized internal transcript (converted from OmiMemoryPayload)"""
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
