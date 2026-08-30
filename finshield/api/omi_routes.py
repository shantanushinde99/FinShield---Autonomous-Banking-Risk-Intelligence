from fastapi import APIRouter, Request
import logging
import json

from finshield.models.voice import VoiceTranscript, VoiceResponse
from finshield.services.voice import VoiceInvestigationService

logger = logging.getLogger(__name__)

router = APIRouter()
voice_service = VoiceInvestigationService()

@router.post("/omi/webhook")
async def handle_omi_webhook(request: Request):
    """
    Receives real-time memory/transcript events from Omi.
    Omi sends: {"segments": [...], "session_id": "..."}
    Each segment has: {"text": "...", "speaker": "SPEAKER_00", ...}
    """
    raw_body = await request.body()
    uid = request.query_params.get("uid", "unknown")
    
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from Omi (uid={uid})")
        return VoiceResponse(status="error", spoken_summary="Invalid payload received.")
    
    logger.info(f"Received Omi Webhook (uid={uid}), keys: {list(payload.keys())}")
    
    # Extract transcript text from Omi's real payload format
    # Omi sends: {"segments": [{"text": "...", "speaker": "SPEAKER_00", ...}], "session_id": "..."}
    segments = payload.get("segments") or payload.get("transcript_segments") or []
    session_id = payload.get("session_id") or payload.get("id") or uid
    
    # Log raw segments for debugging
    logger.info(f"Segments count: {len(segments)}")
    if segments:
        logger.info(f"First segment sample: {json.dumps(segments[0]) if isinstance(segments[0], dict) else segments[0]}")
    
    # Build full transcript from segments
    full_text = ""
    speaker = None
    
    if segments:
        texts = []
        for seg in segments:
            if isinstance(seg, dict):
                t = seg.get("text", "")
                if t:
                    texts.append(t)
                if not speaker:
                    speaker = seg.get("speaker_name") or seg.get("speaker")
            elif isinstance(seg, str):
                texts.append(seg)
        full_text = " ".join(texts).strip()
    elif "text" in payload:
        # Flat payload fallback (from demo script)
        full_text = payload.get("text", "").strip()
        session_id = payload.get("session_id", session_id)
        speaker = payload.get("speaker")
    
    if not full_text:
        logger.warning(f"Empty transcript from Omi (session={session_id})")
        return VoiceResponse(status="skipped", spoken_summary="No transcript content received.")
    
    # Convert to internal VoiceTranscript
    transcript = VoiceTranscript(
        text=full_text,
        session_id=session_id,
        speaker=speaker,
        is_final=True
    )
    
    logger.info(f"Omi transcript (session={session_id}): '{full_text}'")
    
    # Process through FinShield voice pipeline
    response = await voice_service.process_transcript(transcript)
    return response

@router.get("/omi/health")
async def omi_health_check():
    return {"status": "ok", "service": "finshield-omi-gateway"}

@router.get("/omi/status")
async def get_omi_status():
    """Returns the state of the latest voice session for UI updates"""
    session = voice_service.get_latest_session()
    if not session:
        return {"status": "IDLE", "transcript": "", "spoken_summary": ""}
        
    return {
        "status": session.state,
        "transcript": session.last_transcript or "",
        "spoken_summary": session.last_response.spoken_summary if session.last_response else "",
        "customer_id": session.customer_id
    }
