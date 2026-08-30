import pytest
from finshield.models.voice import VoiceTranscript, VoiceInvestigationRequest, VoiceSessionState
from finshield.services.voice import VoiceCommandParser, VoiceInvestigationService
from unittest.mock import patch, MagicMock

def test_extract_customer_id_valid():
    assert VoiceCommandParser.extract_customer_id("Investigate fin000001 please") == "FIN_000001"
    assert VoiceCommandParser.extract_customer_id("check FIN_000001") == "FIN_000001"
    assert VoiceCommandParser.extract_customer_id("risk profile for FIN 000001") == "FIN_000001"
    assert VoiceCommandParser.extract_customer_id("fraud check fin-000001") == "FIN_000001"
    # Whisper speech variations
    assert VoiceCommandParser.extract_customer_id("Investigate customer Finn 384425") == "FIN_384425"
    assert VoiceCommandParser.extract_customer_id("Investigate customer Finn 38 4425") == "FIN_384425"


def test_extract_customer_id_invalid():
    assert VoiceCommandParser.extract_customer_id("Investigate customer John") is None
    assert VoiceCommandParser.extract_customer_id("check fin00") is None

def test_is_investigation_intent():
    assert VoiceCommandParser.is_investigation_intent("Can you investigate FIN_000001?") is True
    assert VoiceCommandParser.is_investigation_intent("fraud risk for this user") is True
    assert VoiceCommandParser.is_investigation_intent("transfer money to John") is False

def test_parse_command_valid():
    transcript = VoiceTranscript(text="investigate fin 123456", session_id="s1")
    is_intent, request, clarification = VoiceCommandParser.parse_command(transcript)
    assert is_intent is True
    assert request.customer_id == "FIN_123456"
    assert clarification is None

def test_parse_command_unsupported():
    transcript = VoiceTranscript(text="transfer 500 dollars", session_id="s1")
    is_intent, request, clarification = VoiceCommandParser.parse_command(transcript)
    assert is_intent is False
    assert request is None
    assert clarification == "I can only help with banking risk investigations. How can I assist you today?"

def test_parse_command_missing_id():
    transcript = VoiceTranscript(text="investigate this customer", session_id="s1")
    is_intent, request, clarification = VoiceCommandParser.parse_command(transcript)
    assert is_intent is True
    assert request is None
    assert "Which customer should I investigate" in clarification

@pytest.mark.asyncio
@patch("finshield.services.voice.InvestigationWorkflowService")
async def test_duplicate_protection(mock_workflow_service):
    service = VoiceInvestigationService()
    session = service.get_or_create_session("s1")
    session.state = VoiceSessionState.INVESTIGATING
    
    transcript = VoiceTranscript(text="investigate fin 000001", session_id="s1")
    response = await service.process_transcript(transcript)
    
    assert response.status == "processing"
    assert "currently investigating" in response.spoken_summary

@pytest.mark.asyncio
@patch("finshield.services.voice.InvestigationWorkflowService")
async def test_duplicate_completed_protection(mock_workflow_service):
    service = VoiceInvestigationService()
    session = service.get_or_create_session("s1")
    session.state = VoiceSessionState.COMPLETED
    session.last_transcript = "investigate fin 000001"
    
    mock_response = MagicMock(status="completed", spoken_summary="done")
    session.last_response = mock_response
    
    transcript = VoiceTranscript(text="investigate fin 000001", session_id="s1")
    response = await service.process_transcript(transcript)
    
    # Should return the cached response
    assert response == mock_response
