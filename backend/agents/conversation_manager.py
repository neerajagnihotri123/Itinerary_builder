"""
Conversation Manager - Main orchestrator for the multi-agent travel system
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .slot_agents import DestinationAgent, DatesAgent, TravelersAgent, BudgetAgent
from .retrieval_agent import RetrievalAgent
from .planner_agent import PlannerAgent
from .accommodation_agent import AccommodationAgent
from .validator_agent import ValidatorAgent
from .ux_agent import UXAgent

@dataclass
class UserSlots:
    destination: Optional[str] = None
    canonical_place_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    adults: int = 2
    children: int = 0
    infants: int = 0
    rooms: int = 1
    currency: str = "INR"
    budget_total: Optional[float] = None
    budget_per_night: Optional[float] = None
    budget_type: str = "unknown"

class ConversationManager:
    """
    Professional travel concierge assistant (persona: friendly, concise, helpful)
    Orchestrates all other agents to provide comprehensive travel planning
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.destination_agent = DestinationAgent(llm_client)
        self.dates_agent = DatesAgent(llm_client)
        self.travelers_agent = TravelersAgent(llm_client)
        self.budget_agent = BudgetAgent(llm_client)
        self.retrieval_agent = RetrievalAgent()
        self.planner_agent = PlannerAgent(llm_client)
        self.accommodation_agent = AccommodationAgent(llm_client)
        self.validator_agent = ValidatorAgent(llm_client)
        self.ux_agent = UXAgent(llm_client)
    
    async def process_message(self, message: str, session_id: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method that orchestrates all agents
        Returns both human_text and rr_payload
        """
        try:
            # Convert current_slots to UserSlots object
            slots = UserSlots(**current_slots) if current_slots else UserSlots()
            
            # Determine which slots need filling/updating
            missing_slots = self._identify_missing_slots(message, slots)
            
            # If we have missing critical slots, handle slot filling first
            if missing_slots:
                return await self._handle_slot_filling(message, slots, missing_slots)
            
            # If all slots are filled, proceed with planning
            # But for general queries without destination, provide helpful response
            if not slots.destination:
                return await self._handle_general_query(message, session_id)
            
            return await self._handle_planning(message, slots, session_id)
            
        except Exception as e:
            return {
                "human_text": "I apologize, but I encountered an issue. Could you please try rephrasing your request?",
                "rr_payload": {
                    "session_id": session_id,
                    "slots": asdict(slots),
                    "error": str(e),
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.1
                    }
                }
            }
    
    def _identify_missing_slots(self, message: str, slots: UserSlots) -> List[str]:
        """Identify which required slots are missing"""
        missing = []
        message_lower = message.lower()
        
        # Don't force slot filling for general queries
        if any(phrase in message_lower for phrase in [
            "popular destinations", "recommend", "suggest", "what are", "show me", 
            "weekend getaway", "plan a trip", "best places", "destinations right now"
        ]):
            return []  # Skip slot filling for general queries
        
        if not slots.destination:
            missing.append("destination")
        if not slots.start_date or not slots.end_date:
            missing.append("dates")
        
        # Optional but helpful slots
        if slots.adults == 2 and slots.children == 0 and "travel" in message.lower():
            if any(word in message.lower() for word in ["family", "kids", "children", "group", "alone", "solo"]):
                missing.append("travelers")
        
        return missing
    
    async def _handle_slot_filling(self, message: str, slots: UserSlots, missing_slots: List[str]) -> Dict[str, Any]:
        """Handle slot filling with priority order"""
        
        # Priority order: destination -> dates -> travelers -> budget
        if "destination" in missing_slots:
            result = await self.destination_agent.extract_destination(message)
            if result.get("clarify"):
                return {
                    "human_text": result["clarify"],
                    "rr_payload": {
                        "session_id": str(uuid.uuid4()),
                        "slots": asdict(slots),
                        "ui_actions": [
                            {"label": "Continue", "action": "clarify_destination", "data": result}
                        ],
                        "metadata": {
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "llm_confidence": 0.8
                        }
                    }
                }
            else:
                slots.destination = result.get("destination_name")
                slots.canonical_place_id = result.get("canonical_place_id")
        
        if "dates" in missing_slots:
            result = await self.dates_agent.extract_dates(message)
            if result.get("clarify"):
                return {
                    "human_text": result["clarify"],
                    "rr_payload": {
                        "session_id": str(uuid.uuid4()),
                        "slots": asdict(slots),
                        "ui_actions": [
                            {"label": "Set Dates", "action": "set_dates"},
                            {"label": "Flexible Dates", "action": "flexible_dates"}
                        ],
                        "metadata": {
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "llm_confidence": 0.8
                        }
                    }
                }
            else:
                slots.start_date = result.get("start_date")
                slots.end_date = result.get("end_date")
        
        if "travelers" in missing_slots:
            result = await self.travelers_agent.extract_travelers(message)
            if result.get("clarify"):
                return {
                    "human_text": result["clarify"],
                    "rr_payload": {
                        "session_id": str(uuid.uuid4()),
                        "slots": asdict(slots),
                        "ui_actions": [
                            {"label": "2 Adults", "action": "set_travelers", "data": {"adults": 2, "children": 0}},
                            {"label": "Family", "action": "set_travelers", "data": {"adults": 2, "children": 2}}
                        ],
                        "metadata": {
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "llm_confidence": 0.8
                        }
                    }
                }
            else:
                slots.adults = result.get("adults", 2)
                slots.children = result.get("children", 0)
                slots.infants = result.get("infants", 0)
                slots.rooms = result.get("rooms", 1)
        
        # Continue processing if all slots are now filled
        remaining_missing = self._identify_missing_slots("", slots)
        if not remaining_missing:
            return await self._handle_planning("", slots, str(uuid.uuid4()))
        
        # Generate appropriate response for remaining missing slots
        return await self._generate_slot_prompt(slots, remaining_missing)
    
    async def _handle_planning(self, message: str, slots: UserSlots, session_id: str) -> Dict[str, Any]:
        """Handle full planning when all slots are filled"""
        
        # Step 1: Retrieve relevant facts
        retrieval_candidates = await self.retrieval_agent.get_facts(slots)
        
        # Step 2: Generate itinerary
        print(f"🎯 Calling planner agent with slots: {asdict(slots)}")
        print(f"📊 Retrieved {len(retrieval_candidates)} candidates")
        planner_result = await self.planner_agent.generate_itinerary(slots, retrieval_candidates)
        print(f"📋 Planner generated: {len(planner_result.get('itinerary', []))} days, {len(planner_result.get('hotel_recommendations', []))} hotels")
        
        # Step 3: Rank accommodations
        hotel_recommendations = await self.accommodation_agent.rank_hotels(
            planner_result.get("hotel_recommendations", []), 
            slots
        )
        
        # Step 4: Validate results
        validation_result = await self.validator_agent.validate(planner_result, retrieval_candidates)
        
        # Step 5: Generate UX response
        ux_result = await self.ux_agent.format_response(planner_result, validation_result)
        
        # Construct final response
        return {
            "human_text": ux_result.get("human_text", "Here's your personalized itinerary!"),
            "rr_payload": {
                "session_id": session_id,
                "slots": asdict(slots),
                "itinerary": planner_result.get("itinerary", []),
                "hotels": hotel_recommendations,
                "followups": planner_result.get("followups", []),
                "ui_actions": ux_result.get("actions", [
                    {"label": "Accept", "action": "accept_itinerary"},
                    {"label": "Modify", "action": "edit_itinerary"}
                ]),
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "llm_confidence": validation_result.get("confidence", 0.8)
                }
            }
        }
    
    async def _generate_slot_prompt(self, slots: UserSlots, missing_slots: List[str]) -> Dict[str, Any]:
        """Generate appropriate prompt for missing slots"""
        
        if "destination" in missing_slots:
            return {
                "human_text": "Where would you like to travel? I can help you explore amazing destinations in India!",
                "rr_payload": {
                    "session_id": str(uuid.uuid4()),
                    "slots": asdict(slots),
                    "ui_actions": [
                        {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                        {"label": "Manali", "action": "set_destination", "data": "Manali"},
                        {"label": "Andaman", "action": "set_destination", "data": "Andaman Islands"}
                    ],
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }
        
        elif "dates" in missing_slots:
            return {
                "human_text": f"When would you like to visit {slots.destination}? Please share your travel dates.",
                "rr_payload": {
                    "session_id": str(uuid.uuid4()),
                    "slots": asdict(slots),
                    "ui_actions": [
                        {"label": "This Weekend", "action": "set_dates", "data": "weekend"},
                        {"label": "Next Month", "action": "set_dates", "data": "next_month"},
                        {"label": "Choose Dates", "action": "open_calendar"}
                    ],
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }
        
        else:
            return {
                "human_text": "Perfect! Let me create a personalized itinerary for you.",
                "rr_payload": {
                    "session_id": str(uuid.uuid4()),
                    "slots": asdict(slots),
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }