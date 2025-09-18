"""
Event-driven pipeline for agent communication
"""

from typing import Dict, List, Any, Callable, Optional
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class Event:
    """Event class for agent communication"""
    
    def __init__(self, event_type: str, data: Dict[str, Any], session_id: str):
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.id = f"{session_id}_{event_type}_{self.timestamp}"

class EventBus:
    """Event bus for managing agent communication"""
    
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register an agent with the event bus"""
        self._agents[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"Subscribed handler to event: {event_type}")
    
    async def publish(self, event: Event):
        """Publish an event to all subscribers"""
        logger.info(f"Publishing event: {event.event_type} for session {event.session_id}")
        
        # Store event in history
        self._event_history.append(event)
        
        # Notify subscribers
        if event.event_type in self._event_handlers:
            tasks = []
            for handler in self._event_handlers[event.event_type]:
                tasks.append(handler(event))
            
            if tasks:
                await asyncio.gather(*tasks)
    
    async def emit(self, event_type: str, data: Dict[str, Any], session_id: str):
        """Convenience method to create and publish an event"""
        event = Event(event_type, data, session_id)
        await self.publish(event)
    
    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get registered agent by name"""
        return self._agents.get(agent_name)
    
    def get_event_history(self, session_id: Optional[str] = None) -> List[Event]:
        """Get event history, optionally filtered by session"""
        if session_id:
            return [event for event in self._event_history if event.session_id == session_id]
        return self._event_history
    
    def clear_event_history(self, session_id: Optional[str] = None):
        """Clear event history"""
        if session_id:
            self._event_history = [event for event in self._event_history if event.session_id != session_id]
        else:
            self._event_history.clear()
        logger.info(f"Cleared event history for session: {session_id or 'all'}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "total_agents": len(self._agents),
            "agents": list(self._agents.keys()),
            "event_types": list(self._event_handlers.keys()),
            "total_events": len(self._event_history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Event type constants
class EventTypes:
    """Event type constants"""
    
    # Profile events
    PROFILE_INTAKE_STARTED = "profile_intake_started"
    PROFILE_INTAKE_COMPLETED = "profile_intake_completed"
    
    # Persona events
    PERSONA_CLASSIFIED = "persona_classified"
    
    # Itinerary events
    ITINERARY_GENERATION_REQUESTED = "itinerary_generation_requested"
    ITINERARY_VARIANT_GENERATED = "itinerary_variant_generated"
    ITINERARY_GENERATION_COMPLETED = "itinerary_generation_completed"
    
    # Customization events
    CUSTOMIZATION_REQUESTED = "customization_requested"
    CUSTOMIZATION_APPLIED = "customization_applied"
    
    # Pricing events
    PRICING_UPDATE_REQUESTED = "pricing_update_requested"
    PRICING_UPDATED = "pricing_updated"
    
    # Booking events
    BOOKING_REQUESTED = "booking_requested"
    BOOKING_COMPLETED = "booking_completed"
    
    # General events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    ERROR_OCCURRED = "error_occurred"