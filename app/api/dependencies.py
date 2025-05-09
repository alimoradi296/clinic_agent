from fastapi import HTTPException, Depends, Header
from typing import Optional, Dict
from config import config

async def verify_api_key(api_key: Optional[str] = Header(None, alias="api-key")) -> Dict:
    """
    Verify API key from the header.
    
    Returns user details data if valid.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check if the API key matches the expected value
    if api_key != config.backend.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # In a real-world scenario, we might look up the user associated with this API key
    # For simplicity, we'll return a basic user dict with defaults
    # This simulates getting user information from a token or API key lookup
    
    # You can modify this to return different user types for different API keys
    # or implement a more sophisticated lookup mechanism
    return {
        "user_id": "default_user",
        "user_type": "doctor"  # Default user type
    }

# Optional function to extract user details from query parameters for testing
async def get_user_from_query(
    user_id: Optional[str] = None, 
    user_type: Optional[str] = None
) -> Dict:
    """
    Get user details from query parameters.
    
    This is primarily for testing purposes.
    In production, always use API key authentication.
    """
    if not user_id or not user_type:
        raise HTTPException(
            status_code=400,
            detail="Missing user_id or user_type parameters",
        )
    
    if user_type not in ["doctor", "patient"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid user type. Must be 'doctor' or 'patient'",
        )
    
    return {
        "user_id": user_id,
        "user_type": user_type
    }