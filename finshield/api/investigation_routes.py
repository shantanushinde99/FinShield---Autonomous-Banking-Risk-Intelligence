from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import logging
import asyncio

from finshield.services.investigation import InvestigationWorkflowService
from finshield.models.workflow import InvestigationState
from finshield.models.api import APIError, ErrorDetails
from finshield.exceptions import CustomerNotFoundError

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
    
    try:
        # Run the workflow in a separate thread because Lyzr uses asyncio.run() internally
        # which will crash if run inside the FastAPI event loop directly.
        state = await asyncio.to_thread(workflow_service.run_investigation, req.customer_id)
        return state
        
    except CustomerNotFoundError:
        logger.warning(f"Customer not found: {req.customer_id}")
        # We will let the global exception handler handle this, but if we want to handle it directly:
        raise
        
    except Exception as e:
        logger.error(f"Investigation failed for {req.customer_id}: {e}", exc_info=True)
        raise
