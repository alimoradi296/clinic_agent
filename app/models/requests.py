from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    """Request model for chat API."""
    message: str = Field(..., description="The user's message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversations")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What are my upcoming appointments?",
                "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
            }
        }

class SessionRequest(BaseModel):
    """Request model for creating a new session."""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the session")
    
    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "name": "John Doe",
                    "preferences": {
                        "notification_method": "email" 
                    }
                }
            }
        }

class AppointmentRequest(BaseModel):
    """Request model for creating appointments."""
    patient_id: str = Field(..., description="Patient ID")
    doctor_id: str = Field(..., description="Doctor ID")
    date_time: str = Field(..., description="Appointment date and time (ISO 8601 format)")
    duration: int = Field(30, description="Appointment duration in minutes")
    appointment_type: str = Field(..., description="Type of appointment")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        schema_extra = {
            "example": {
                "patient_id": "patient_id_here",
                "doctor_id": "doctor_id_here",
                "date_time": "2025-05-15T14:30:00",
                "duration": 30,
                "appointment_type": "check-up",
                "notes": "Initial consultation"
            }
        }

class PatientRequest(BaseModel):
    """Request model for creating patients."""
    first_name: str = Field(..., description="Patient's first name")
    last_name: str = Field(..., description="Patient's last name")
    date_of_birth: str = Field(..., description="Patient's date of birth (YYYY-MM-DD)")
    gender: str = Field(..., description="Patient's gender")
    email: Optional[str] = Field(None, description="Patient's email address")
    phone: Optional[str] = Field(None, description="Patient's phone number")
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-05-15",
                "gender": "male",
                "email": "john.doe@example.com",
                "phone": "555-123-4567"
            }
        }