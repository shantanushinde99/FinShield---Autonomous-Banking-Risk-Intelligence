from fastapi import APIRouter, Request
from pydantic import BaseModel
import logging
import asyncio

from finshield.services.investigation import InvestigationWorkflowService
from finshield.models.workflow import InvestigationState

logger = logging.getLogger(__name__)

router = APIRouter()
workflow_service = InvestigationWorkflowService()

class InvestigateRequest(BaseModel):
    customer_id: str

@router.post("/investigate", response_model=InvestigationState)
async def run_investigation(req: InvestigateRequest, request: Request):
    """
    Run the end-to-end investigation workflow for a given customer.
    Returns the full investigation state including the execution trace.
    """
    request_id = request.state.request_id if hasattr(request.state, "request_id") else "unknown"
    logger.info(f"Received API investigation request for customer {req.customer_id} (req_id={request_id})")
    
    # Run the workflow in a separate thread because Lyzr uses asyncio.run() internally
    # which will crash if run inside the FastAPI event loop directly.
    # CustomerNotFoundError propagates to the 404 handler in main.py.
    return await asyncio.to_thread(workflow_service.run_investigation, req.customer_id)
