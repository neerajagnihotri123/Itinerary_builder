"""
Centralized context store for managing session state across agents
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class ContextStore:
    """Centralized context store for agent communication"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "profile": {},
                "persona": {},
                "trip_details": {},
                "itineraries": {},
                "customizations": [],
                "pricing": {},
                "bookings": [],
                "context": {}
            }
        return self._sessions[session_id]
    
    def update_session(self, session_id: str, key: str, value: Any):
        """Update session context"""
        session = self.get_session(session_id)
        session[key] = value
        session["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Updated session {session_id} key: {key}")
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        session = self.get_session(session_id)
        message = {
            "id": f"{session_id}_{len(session['messages'])}",
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        session["messages"].append(message)
        logger.info(f"Added {role} message to session {session_id}")
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages from session"""
        session = self.get_session(session_id)
        return session["messages"]
    
    def set_profile(self, session_id: str, profile_data: Dict[str, Any]):
        """Set profile data"""
        self.update_session(session_id, "profile", profile_data)
    
    def get_profile(self, session_id: str) -> Dict[str, Any]:
        """Get profile data"""
        session = self.get_session(session_id)
        return session.get("profile", {})
    
    def set_persona(self, session_id: str, persona_data: Dict[str, Any]):
        """Set persona data"""
        self.update_session(session_id, "persona", persona_data)
    
    def get_persona(self, session_id: str) -> Dict[str, Any]:
        """Get persona data"""
        session = self.get_session(session_id)
        return session.get("persona", {})
    
    def set_trip_details(self, session_id: str, trip_details: Dict[str, Any]):
        """Set trip details"""
        self.update_session(session_id, "trip_details", trip_details)
    
    def get_trip_details(self, session_id: str) -> Dict[str, Any]:
        """Get trip details"""
        session = self.get_session(session_id)
        return session.get("trip_details", {})
    
    def add_itinerary(self, session_id: str, itinerary_id: str, itinerary_data: Dict[str, Any]):
        """Add itinerary to session"""
        session = self.get_session(session_id)
        if "itineraries" not in session:
            session["itineraries"] = {}
        session["itineraries"][itinerary_id] = itinerary_data
        self.update_session(session_id, "itineraries", session["itineraries"])
    
    def get_itinerary(self, session_id: str, itinerary_id: str) -> Optional[Dict[str, Any]]:
        """Get specific itinerary"""
        session = self.get_session(session_id)
        return session.get("itineraries", {}).get(itinerary_id)
    
    def get_all_itineraries(self, session_id: str) -> Dict[str, Any]:
        """Get all itineraries for session"""
        session = self.get_session(session_id)
        return session.get("itineraries", {})
    
    def add_customization(self, session_id: str, customization: Dict[str, Any]):
        """Add customization to session"""
        session = self.get_session(session_id)
        customization["timestamp"] = datetime.now(timezone.utc).isoformat()
        session["customizations"].append(customization)
        self.update_session(session_id, "customizations", session["customizations"])
    
    def get_customizations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all customizations for session"""
        session = self.get_session(session_id)
        return session.get("customizations", [])
    
    def set_pricing(self, session_id: str, pricing_data: Dict[str, Any]):
        """Set pricing data"""
        self.update_session(session_id, "pricing", pricing_data)
    
    def get_pricing(self, session_id: str) -> Dict[str, Any]:
        """Get pricing data"""
        session = self.get_session(session_id)
        return session.get("pricing", {})
    
    def add_booking(self, session_id: str, booking_data: Dict[str, Any]):
        """Add booking to session"""
        session = self.get_session(session_id)
        booking_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        session["bookings"].append(booking_data)
        self.update_session(session_id, "bookings", session["bookings"])
    
    def get_bookings(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all bookings for session"""
        session = self.get_session(session_id)
        return session.get("bookings", [])
    
    def set_context(self, session_id: str, key: str, value: Any):
        """Set context value"""
        session = self.get_session(session_id)
        if "context" not in session:
            session["context"] = {}
        session["context"][key] = value
        self.update_session(session_id, "context", session["context"])
    
    def get_context(self, session_id: str, key: str) -> Any:
        """Get context value"""
        session = self.get_session(session_id)
        return session.get("context", {}).get(key)
    
    def clear_session(self, session_id: str):
        """Clear session data"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared session {session_id}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get context store statistics"""
        return {
            "total_sessions": len(self._sessions),
            "sessions": list(self._sessions.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }