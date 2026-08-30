import re
import logging
from typing import Dict, Optional, Tuple

from finshield.models.voice import (
    VoiceTranscript, 
    VoiceInvestigationRequest, 
    VoiceSession, 
    VoiceSessionState,
    VoiceResponse
)
from finshield.services.investigation import InvestigationWorkflowService

logger = logging.getLogger(__name__)

class VoiceCommandParser:
    """Parses intent and parameters from natural language voice transcripts"""
    
    # Word-to-digit mapping for STT that transcribes numbers as words
    WORD_TO_DIGIT = {
        "zero": "0", "oh": "0", "o": "0",
        "one": "1", "won": "1",
        "two": "2", "to": "2", "too": "2",
        "three": "3", "tree": "3",
        "four": "4", "for": "4",
        "five": "5",
        "six": "6", "sicks": "6",
        "seven": "7",
        "eight": "8", "ate": "8",
        "nine": "9", "niner": "9",
    }
    
    # Matches variations: "FIN 1", "Finn 5", "FIN 384425", "fin_000001"
    # Accepts even a single digit — _normalize_digits will zero-pad to 6
    CUSTOMER_ID_REGEX = re.compile(r'(?:finn?|customer|id|number)[-_\s:]*(\d[\d\s]*)', re.IGNORECASE)
    
    # Matches keywords for risk investigation
    INVESTIGATE_KEYWORDS = ["investigate", "investigation", "check", "risk profile", "fraud risk"]

    @classmethod
    def _words_to_digits(cls, text: str) -> str:
        """Convert spoken number words to digit characters.
        'three eight four four two six' → '3 8 4 4 2 6'
        """
        words = text.split()
        result = []
        for word in words:
            clean = word.strip(".,!?").lower()
            if clean in cls.WORD_TO_DIGIT:
                result.append(cls.WORD_TO_DIGIT[clean])
            else:
                result.append(word)
        return " ".join(result)

    @classmethod
    def _normalize_digits(cls, raw_digits: str) -> Optional[str]:
        """Remove spaces/dashes from digit groups and pad to 6 digits"""
        digits_only = re.sub(r'\D', '', raw_digits)
        if len(digits_only) < 1 or len(digits_only) > 6:
            return None
        # Pad to 6 digits
        return digits_only.zfill(6)

    @classmethod
    def extract_customer_id(cls, text: str) -> Optional[str]:
        # First, convert any spoken number words to digits
        converted_text = cls._words_to_digits(text)
        logger.info(f"After word-to-digit conversion: '{converted_text}'")
        
        match = cls.CUSTOMER_ID_REGEX.search(converted_text)
        if match:
            normalized = cls._normalize_digits(match.group(1))
            if normalized:
                logger.info(f"Extracted customer ID: FIN_{normalized}")
                return f"FIN_{normalized}"
        
        return None

    @classmethod
    def is_investigation_intent(cls, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.INVESTIGATE_KEYWORDS)
        
    @classmethod
    def parse_command(cls, transcript: VoiceTranscript) -> Tuple[bool, Optional[VoiceInvestigationRequest], Optional[str]]:
        """
        Parses the command.
        Returns (is_valid_intent, request, clarification_message)
        """
        if not cls.is_investigation_intent(transcript.text):
            return False, None, "I can only help with banking risk investigations. How can I assist you today?"
            
        customer_id = cls.extract_customer_id(transcript.text)
        if not customer_id:
            return True, None, "Which customer should I investigate? Please provide the FinShield customer ID, for example FIN 000001."
            
        request = VoiceInvestigationRequest(
            session_id=transcript.session_id,
            customer_id=customer_id,
            command=transcript.text
        )
        return True, request, None


class VoiceInvestigationService:
    """Manages voice sessions and orchestrates voice-driven investigations"""
    
    def __init__(self):
        # In-memory session store
        self._sessions: Dict[str, VoiceSession] = {}
        # Buffer for accumulating transcript segments per session
        self._transcript_buffer: Dict[str, str] = {}
        self._latest_session_id: Optional[str] = None
        self.workflow_service = InvestigationWorkflowService()

    def get_latest_session(self) -> Optional[VoiceSession]:
        if self._latest_session_id:
            return self._sessions.get(self._latest_session_id)
        return None

    def get_or_create_session(self, session_id: str) -> VoiceSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = VoiceSession(session_id=session_id)
        self._latest_session_id = session_id
        return self._sessions[session_id]

    def accumulate_transcript(self, session_id: str, text: str) -> str:
        """Accumulate transcript segments for a session and return full buffer"""
        if session_id not in self._transcript_buffer:
            self._transcript_buffer[session_id] = ""
        self._transcript_buffer[session_id] = (self._transcript_buffer[session_id] + " " + text).strip()
        return self._transcript_buffer[session_id]

    def clear_buffer(self, session_id: str):
        """Clear the transcript buffer for a session"""
        self._transcript_buffer.pop(session_id, None)

    async def process_transcript(self, transcript: VoiceTranscript) -> VoiceResponse:
        session = self.get_or_create_session(transcript.session_id)
        
        # Simple duplicate/idempotency protection
        if session.state == VoiceSessionState.INVESTIGATING:
            return VoiceResponse(
                status="processing",
                spoken_summary="I am currently investigating a customer. Please wait."
            )
            
        if session.state == VoiceSessionState.COMPLETED and session.last_transcript == transcript.text:
            if session.last_response:
                return session.last_response

        # Accumulate this segment into the session buffer
        accumulated_text = self.accumulate_transcript(transcript.session_id, transcript.text)
        logger.info(f"Accumulated buffer (session={transcript.session_id}): '{accumulated_text}'")
        
        # Create a merged transcript for parsing
        merged_transcript = VoiceTranscript(
            text=accumulated_text,
            session_id=transcript.session_id,
            speaker=transcript.speaker,
            is_final=transcript.is_final
        )

        # Parse command from accumulated text
        is_intent, request, clarification = VoiceCommandParser.parse_command(merged_transcript)
        
        if not is_intent:
            # No investigation intent yet — keep buffering, respond softly
            session.state = VoiceSessionState.IDLE
            response = VoiceResponse(status="rejected", spoken_summary=clarification)
            session.last_response = response
            return response
            
        if not request:
            # Has intent but no customer ID yet — keep buffering, ask for clarification
            session.state = VoiceSessionState.NEEDS_CLARIFICATION
            response = VoiceResponse(status="needs_clarification", spoken_summary=clarification)
            session.last_response = response
            return response
            
        # We have a valid request to investigate — clear buffer and go!
        self.clear_buffer(transcript.session_id)
        session.state = VoiceSessionState.INVESTIGATING
        session.customer_id = request.customer_id
        session.last_transcript = accumulated_text
        
        import asyncio
        
        # Execute investigation in a separate thread because Phase 5 internally 
        # uses asyncio.run() which would crash if run in the main event loop
        logger.info(f"Starting voice-triggered investigation for {request.customer_id}")
        try:
            final_state = await asyncio.to_thread(self.workflow_service.run_investigation, request.customer_id)
            
            session.investigation_id = final_state.investigation_id
            
            if final_state.final_decision:
                decision = final_state.final_decision
                summary = (
                    f"Investigation complete for customer {decision.customer_id}. "
                    f"The overall risk is {decision.risk_level.replace('_', ' ').lower()}. "
                    f"The recommended action is {decision.recommendation.replace('_', ' ').lower()}."
                )
                
                response = VoiceResponse(
                    status="completed",
                    investigation_id=session.investigation_id,
                    customer_id=decision.customer_id,
                    risk_level=decision.risk_level,
                    recommendation=decision.recommendation,
                    spoken_summary=summary,
                    confidence=decision.confidence
                )
                session.state = VoiceSessionState.COMPLETED
            else:
                response = VoiceResponse(
                    status="failed",
                    spoken_summary="The investigation failed to complete successfully."
                )
                session.state = VoiceSessionState.FAILED
                
        except Exception as e:
            logger.error(f"Investigation Failed: {e}")
            response = VoiceResponse(
                status="failed",
                spoken_summary="I'm sorry, there was a system error during the investigation."
            )
            session.state = VoiceSessionState.FAILED
            
        session.last_response = response
        return response
