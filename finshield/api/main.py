from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import uuid
import os

from finshield.api.omi_routes import router as omi_router
from finshield.api.investigation_routes import router as investigation_router
from finshield.models.api import APIError, ErrorDetails, HealthResponse
from finshield.exceptions import CustomerNotFoundError

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinShield API",
    description="Backend API for FinShield Autonomous Banking Risk & Fraud Investigator",
    version="1.0.0"
)

# CORS middleware for potential frontend access
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:8000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://127.0.0.1:8000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for Request IDs
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Exception Handlers
@app.exception_handler(CustomerNotFoundError)
async def customer_not_found_handler(request: Request, exc: CustomerNotFoundError):
    request_id = getattr(request.state, "request_id", None)
    error = APIError(error=ErrorDetails(
        code="CUSTOMER_NOT_FOUND",
        message=f"The requested customer could not be found.",
        request_id=request_id
    ))
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=error.model_dump())

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled exception (req_id={request_id}): {exc}", exc_info=True)
    error = APIError(error=ErrorDetails(
        code="INTERNAL_ERROR",
        message="An internal system error occurred.",
        request_id=request_id
    ))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error.model_dump())

# Include Routes
app.include_router(omi_router, prefix="/api/v1")
app.include_router(investigation_router, prefix="/api/v1")

# Health Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")

@app.get("/health/dependencies", response_model=HealthResponse)
async def health_dependencies():
    # In a real system, we'd ping DuckDB, Qdrant, etc.
    # For now, we assume they are ok if the app started.
    dependencies = {
        "FastAPI": "available",
        "DuckDB": "available", 
        "Qdrant": "available",
        "Mistral": "available",
        "Lyzr": "available",
    }
    return HealthResponse(status="healthy", dependencies=dependencies)

# Serve Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
os.makedirs(frontend_dir, exist_ok=True) # Ensure it exists so StaticFiles doesn't crash on startup if missing

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_dir, "index.html"))
