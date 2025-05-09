from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatResponse(BaseModel):
    """Response model for chat API."""
    message: str = Field(..., description="The AI's response message")
    session_id: str = Field(..., description="The session ID")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested actions or UI updates")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "You have 2 upcoming appointments. The next one is with Dr. Smith on May 15, 2025 at 2:30 PM.",
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "actions": [
                    {
                        "type": "display_appointments",
                        "data": [
                            {
                                "id": "appt123",
                                "doctor_id": "dr-smith",
                                "date_time": "2025-05-15T14:30:00",
                                "status": "confirmed"
                            }
                        ]
                    }
                ]
            }
        }

class SessionResponse(BaseModel):
    """Response model for session creation API."""
    session_id: str = Field(..., description="The created session ID")
    message: str = Field(..., description="Response message")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "message": "Session created successfully."
            }
        }

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": 404,
                    "message": "Resource not found",
                    "timestamp": "2025-05-02T14:30:45Z",
                    "request_id": "6c84fb90-12c4-11e1-840d-7b25c5ee775a"
                }
            }
        }

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="API health status")
    backend_connection: Optional[str] = Field(None, description="Backend connection status")
    message: Optional[str] = Field(None, description="Additional message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "backend_connection": "connected"
            }
        }