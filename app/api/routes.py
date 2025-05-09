from fastapi import APIRouter, HTTPException, Depends, Header, Query
from typing import Optional, Dict, Any
from app.models.requests import ChatRequest, SessionRequest
from app.models.responses import ChatResponse, SessionResponse
from app.core.orchestrator import orchestrator
from app.core.context import context_manager
from app.api.dependencies import verify_api_key, get_user_from_query
from app.integrations.backend_api import backend_client

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_data: Dict = Depends(verify_api_key),
    # Optional query parameters for testing (would remove in production)
    test_user_id: Optional[str] = Query(None, description="Test user ID (for development only)"),
    test_user_type: Optional[str] = Query(None, description="Test user type (for development only)")
):
    """
    Process a chat message from a user.
    
    The user can be either a doctor or a patient.
    """
    try:
        # Override user data with test parameters if provided (for development only)
        user_id = test_user_id if test_user_id else user_data.get("user_id")
        user_type = test_user_type if test_user_type else user_data.get("user_type")
        
        response = await orchestrator.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=user_id,
            user_type=user_type
        )
        
        return ChatResponse(
            message=response["text"],
            session_id=response["session_id"],
            actions=response["actions"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionRequest,
    user_data: Dict = Depends(verify_api_key),
    # Optional query parameters for testing (would remove in production)
    test_user_id: Optional[str] = Query(None, description="Test user ID (for development only)"),
    test_user_type: Optional[str] = Query(None, description="Test user type (for development only)")
):
    """Create a new chat session."""
    try:
        # Override user data with test parameters if provided (for development only)
        user_id = test_user_id if test_user_id else user_data.get("user_id")
        user_type = test_user_type if test_user_type else user_data.get("user_type")
        
        session_id = context_manager.create_session(user_id, user_type)
        
        # If metadata was provided in the request, store it in the session
        if request.metadata:
            session = context_manager.get_session(session_id)
            if session and "metadata" in session:
                session["metadata"].update(request.metadata)
                context_manager.update_session(session_id, session)
        
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    user_data: Dict = Depends(verify_api_key)
):
    """Get session details."""
    try:
        session = context_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}", response_model=Dict[str, str])
async def delete_session(
    session_id: str,
    user_data: Dict = Depends(verify_api_key)
):
    """Delete a session."""
    try:
        result = context_manager.delete_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint (useful for API validation)
@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Verify the API is functioning and can connect to the backend."""
    try:
        # Check connection to the backend
        is_connected = await backend_client.check_connection()
        
        if is_connected:
            return {"status": "healthy", "backend_connection": "connected"}
        else:
            return {"status": "degraded", "backend_connection": "disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}