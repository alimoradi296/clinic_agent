import json
import redis
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from config import config

class ContextManager:
    """Manages conversation context using Redis."""
    
    def __init__(self):
        self.redis = redis.Redis(
            host=config.redis.host,
            port=config.redis.port,
            password=config.redis.password,
            db=config.redis.db,
            decode_responses=True
        )
        self.context_ttl = 60 * 60 * 24  # 24 hours
    
    def create_session(self, user_id: str, user_type: str) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "user_id": user_id,
            "user_type": user_type,  # 'doctor' or 'patient'
            "created_at": datetime.now().isoformat(),
            "history": [],
            "metadata": {}
        }
        
        # Store session in Redis
        self.redis.setex(
            f"session:{session_id}", 
            self.context_ttl, 
            json.dumps(session_data)
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID."""
        session_data = self.redis.get(f"session:{session_id}")
        if not session_data:
            return None
        
        # Refresh TTL
        self.redis.expire(f"session:{session_id}", self.context_ttl)
        
        return json.loads(session_data)
    
    def update_session(self, session_id: str, session_data: Dict) -> bool:
        """Update an existing session."""
        # Check if session exists
        if not self.redis.exists(f"session:{session_id}"):
            return False
        
        # Update the session
        self.redis.setex(
            f"session:{session_id}", 
            self.context_ttl, 
            json.dumps(session_data)
        )
        
        return True
    
    def add_message_to_history(
        self, session_id: str, role: str, content: str
    ) -> bool:
        """Add a message to the session history."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Add message to history
        message = {
            "role": role,  # 'user' or 'assistant'
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session_data["history"].append(message)
        
        # Limit history size (keep last 20 messages)
        if len(session_data["history"]) > 20:
            session_data["history"] = session_data["history"][-20:]
        
        # Update session
        return self.update_session(session_id, session_data)
    
    def get_history(self, session_id: str) -> List[Dict]:
        """Get the message history for a session."""
        session_data = self.get_session(session_id)
        if not session_data:
            return []
        
        return session_data["history"]
    
    def set_metadata(self, session_id: str, key: str, value: Any) -> bool:
        """Set metadata for a session."""
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["metadata"][key] = value
        return self.update_session(session_id, session_data)
    
    def get_metadata(self, session_id: str, key: str) -> Optional[Any]:
        """Get metadata for a session."""
        session_data = self.get_session(session_id)
        if not session_data or key not in session_data["metadata"]:
            return None
        
        return session_data["metadata"][key]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        return bool(self.redis.delete(f"session:{session_id}"))

# Create a singleton instance
context_manager = ContextManager()