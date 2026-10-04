from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime, timezone

class ErrorDetails(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class APIError(BaseModel):
    error: ErrorDetails

class HealthResponse(BaseModel):
    status: str
    dependencies: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
