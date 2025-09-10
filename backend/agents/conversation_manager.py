"""
Conversation Manager - Main orchestrator for the multi-agent travel system
"""
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
            print(f"🤖 ConversationManager processing: '{message}'")
            
            # Convert current_slots to UserSlots object
            slots = UserSlots(**current_slots) if current_slots else UserSlots()
            print(f"📋 Current slots: {asdict(slots)}")
            
            # Check for destination discovery queries first
            if self._is_destination_discovery_query(message):
                print("🏞️ Path: Destination discovery query -> Generate destination cards")
                return await self._handle_destination_discovery(message, session_id)
                
            # Check for specific destination queries (e.g., "tell me about kerala")
            if self._is_destination_specific_query(message):
                print("🏙️ Path: Destination specific query -> Generate destination card")
                return await self._handle_destination_specific_query(message, session_id)
            
            # Check for accommodation queries  
            if self._is_accommodation_query(message):
                print("🏨 Path: Accommodation query -> Generate hotel cards")
                return await self._handle_accommodation_query(message, session_id, slots)
            
            # Determine which slots need filling/updating for trip planning
            missing_slots = self._identify_missing_slots(message, slots)
            print(f"❓ Missing slots: {missing_slots}")
            
            # If we have missing critical slots, handle slot filling first
            if missing_slots:
                print(f"📝 Path: Missing slots {missing_slots} -> Handle slot filling")
                return await self._handle_slot_filling(message, slots, missing_slots)
            
            # If all slots are filled, proceed with planning
            # But for general queries without destination, provide helpful response
            if not slots.destination:
                print("🎯 Path: General query without destination -> Generate helpful response")
                return await self._handle_general_query(message, session_id)
            
            print("🎯 Path: Complete slots -> Generate full response")
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
    
    async def _handle_general_query(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle general queries without specific destination (like 'popular destinations')"""
        
        # Use UX agent to provide helpful general travel information
        ux_result = await self.ux_agent.format_general_response(message)
        
        return {
            "human_text": ux_result.get("human_text", "Here are some popular travel destinations and tips!"),
            "rr_payload": {
                "session_id": session_id,
                "slots": asdict(UserSlots()),  # Empty slots for general queries
                "ui_actions": ux_result.get("actions", [
                    {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                    {"label": "Manali", "action": "set_destination", "data": "Manali"},
                    {"label": "Andaman Islands", "action": "set_destination", "data": "Andaman Islands"},
                    {"label": "Goa", "action": "set_destination", "data": "Goa"}
                ]),
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "llm_confidence": 0.9,
                    "query_type": "general"
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
    
    def _is_destination_discovery_query(self, message: str) -> bool:
        """Check if the message is asking for destination discovery/recommendations"""
        message_lower = message.lower()
        destination_keywords = [
            "popular destinations", "recommend destinations", "suggest places", 
            "where to go", "best places to visit", "travel destinations",
            "weekend getaway", "holiday destinations", "vacation spots",
            "places to travel", "destinations to visit", "travel ideas"
        ]
        return any(keyword in message_lower for keyword in destination_keywords)
    
    def _is_destination_specific_query(self, message: str) -> bool:
        """Check if the message is asking about a specific destination"""
        message_lower = message.lower().strip()
        
        # Common patterns for destination-specific queries
        specific_patterns = [
            "tell me about", "what about", "about", "information about",
            "details about", "know about", "learn about", "explore"
        ]
        
        # Common destination names in India (can be expanded)
        destinations = [
            "kerala", "goa", "rajasthan", "himachal", "uttarakhand", "kashmir",
            "manali", "shimla", "rishikesh", "haridwar", "dharamshala", "mcleodganj",
            "andaman", "lakshadweep", "mumbai", "delhi", "bangalore", "chennai",
            "kolkata", "pune", "hyderabad", "jaipur", "udaipur", "jodhpur",
            "agra", "varanasi", "pushkar", "mount abu", "ooty", "kodaikanal",
            "munnar", "alleppey", "kochi", "thekkady", "wayanad", "coorg",
            "hampi", "mysore", "darjeeling", "gangtok", "shillong", "kaziranga"
        ]
        
        # Check if message contains both a specific pattern and a destination
        has_pattern = any(pattern in message_lower for pattern in specific_patterns)
        has_destination = any(dest in message_lower for dest in destinations)
        
        # NEW: Also treat single destination names as destination-specific queries
        # This handles cases like user just saying "kerala" to learn about Kerala
        is_single_destination = message_lower in destinations
        
        return (has_pattern and has_destination) or is_single_destination
    
    def _is_accommodation_query(self, message: str) -> bool:
        """Check if the message is specifically asking about hotels/accommodation"""
        message_lower = message.lower()
        accommodation_keywords = [
            "hotels", "accommodation", "stay", "resort", "lodge",
            "where to stay", "book hotel", "hotel booking", "places to stay",
            "best hotels", "hotel recommendations", "accommodation options"
        ]
        return any(keyword in message_lower for keyword in accommodation_keywords)
    
    async def _handle_destination_discovery(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle destination discovery queries by showing popular destinations"""
        # Use UX agent to provide destination recommendations
        ux_result = await self.ux_agent.format_general_response(message)
        
        return {
            "human_text": ux_result.get("human_text", "Here are some amazing destinations you might love!"),
            "rr_payload": {
                "session_id": session_id,
                "slots": asdict(UserSlots()),
                "ui_actions": ux_result.get("actions", [
                    {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                    {"label": "Manali", "action": "set_destination", "data": "Manali"},
                    {"label": "Andaman Islands", "action": "set_destination", "data": "Andaman Islands"},
                    {"label": "Goa", "action": "set_destination", "data": "Goa"},
                    {"label": "Kerala", "action": "set_destination", "data": "Kerala"},
                    {"label": "Rajasthan", "action": "set_destination", "data": "Rajasthan"}
                ]),
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "llm_confidence": 0.9,
                    "query_type": "destination_discovery"
                }
            }
        }
    
    async def _handle_destination_specific_query(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle destination-specific queries like 'kerala', 'tell me about goa'"""
        
        # Extract destination from message
        destinations = [
            "kerala", "goa", "rajasthan", "himachal", "uttarakhand", "kashmir",
            "manali", "shimla", "rishikesh", "haridwar", "dharamshala", "mcleodganj",
            "andaman", "lakshadweep", "mumbai", "delhi", "bangalore", "chennai",
            "kolkata", "pune", "hyderabad", "jaipur", "udaipur", "jodhpur",
            "agra", "varanasi", "pushkar", "mount abu", "ooty", "kodaikanal",
            "munnar", "alleppey", "kochi", "thekkady", "wayanad", "coorg",
            "hampi", "mysore", "darjeeling", "gangtok", "shillong", "kaziranga"
        ]
        
        detected_destination = None
        message_lower = message.lower().strip()
        
        for dest in destinations:
            if dest in message_lower:
                detected_destination = dest.title()
                break
        
        if not detected_destination:
            return await self._handle_general_query(message, session_id)
        
        try:
            # Use LLM to generate informative response about the destination
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import os
            
            # Get detailed destination data from mock_data
            destination_context = self._get_destination_context(detected_destination)
            
            # Create context for LLM
            context = f"""
User is asking about {detected_destination}. Provide an engaging, informative response about this destination.

Context about {detected_destination}:
{destination_context}

Create a response that:
1. Highlights why {detected_destination} is special
2. Mentions 2-3 key attractions or experiences
3. Keeps it conversational and exciting
4. Ends with encouraging them to plan a trip

Keep response to 2-3 sentences maximum.
"""
            
            # Create LLM client for this call
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=session_id,
                system_message="You are a knowledgeable travel guide who provides engaging, concise information about destinations."
            ).with_model("openai", "gpt-4o-mini")
            
            # Generate response
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                ai_text = response.content
            else:
                ai_text = str(response)
            
            print(f"✅ Generated destination response for {detected_destination}: {len(ai_text)} chars")
            
            return {
                "human_text": ai_text.strip(),
                "rr_payload": {
                    "session_id": session_id,
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "destination_specific",
                        "detected_destination": detected_destination,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ LLM destination query failed: {e}")
            # Fallback response
            return {
                "human_text": f"{detected_destination}, known for its natural beauty and rich culture, is perfect for an unforgettable getaway. Would you like me to help you plan a trip there?",
                "rr_payload": {
                    "session_id": session_id,
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "destination_specific",
                        "detected_destination": detected_destination,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.7
                    }
                }
            }
    
    def _get_destination_context(self, destination: str) -> str:
        """Get rich context about a destination from mock data"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mock_data import MOCK_DESTINATIONS, MOCK_HOTELS, MOCK_TOURS, MOCK_ACTIVITIES
            
            # Find destination in mock data
            dest_info = None
            for dest in MOCK_DESTINATIONS:
                if destination.lower() in dest.get('name', '').lower():
                    dest_info = dest
                    break
            
            if not dest_info:
                return f"{destination} is a beautiful destination in India."
            
            # Get related activities and hotels
            related_activities = [a for a in MOCK_ACTIVITIES if destination.lower() in a.get('location', '').lower()]
            related_hotels = [h for h in MOCK_HOTELS if destination.lower() in h.get('location', '').lower()]
            
            context_parts = []
            context_parts.append(f"Name: {dest_info.get('name')}")
            context_parts.append(f"Description: {dest_info.get('pitch', '')}")
            context_parts.append(f"Highlights: {', '.join(dest_info.get('highlights', [])[:3])}")
            context_parts.append(f"Rating: {dest_info.get('rating')}/5")
            
            if related_activities:
                context_parts.append(f"Popular activities: {', '.join([a.get('title', '') for a in related_activities[:2]])}")
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            print(f"❌ Error getting destination context: {e}")
            return f"{destination} is a popular travel destination in India."
    
    async def _handle_accommodation_query(self, message: str, session_id: str, slots: UserSlots) -> Dict[str, Any]:
        """Handle accommodation-specific queries"""
        
        # Try to extract destination from the message if not already in slots
        if not slots.destination:
            # Extract destination from accommodation query (e.g., "hotels in goa")
            message_lower = message.lower()
            destinations = [
                "kerala", "goa", "rajasthan", "himachal", "uttarakhand", "kashmir",
                "manali", "shimla", "rishikesh", "haridwar", "dharamshala", "mcleodganj",
                "andaman", "lakshadweep", "mumbai", "delhi", "bangalore", "chennai",
                "kolkata", "pune", "hyderabad", "jaipur", "udaipur", "jodhpur",
                "agra", "varanasi", "pushkar", "mount abu", "ooty", "kodaikanal",
                "munnar", "alleppey", "kochi", "thekkady", "wayanad", "coorg",
                "hampi", "mysore", "darjeeling", "gangtok", "shillong", "kaziranga"
            ]
            
            # Find destination mentioned in the message
            detected_destination = None
            for dest in destinations:
                if dest in message_lower:
                    detected_destination = dest.title()
                    slots.destination = detected_destination
                    break
        
        if not slots.destination:
            return {
                "human_text": "I'd be happy to help you find great accommodation! First, could you let me know which destination you're interested in?",
                "rr_payload": {
                    "session_id": session_id,
                    "slots": asdict(slots),
                    "ui_actions": [
                        {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                        {"label": "Manali", "action": "set_destination", "data": "Manali"},
                        {"label": "Goa", "action": "set_destination", "data": "Goa"}
                    ],
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.8,
                        "query_type": "accommodation_query"
                    }
                }
            }
        
        # If we have a destination, get hotel recommendations
        try:
            print(f"🏨 Getting hotels for destination: {slots.destination}")
            # Get hotel recommendations using the accommodation agent
            hotel_recommendations = await self.accommodation_agent.get_hotels_for_destination(
                slots.destination, slots
            )
            
            print(f"🏨 Retrieved {len(hotel_recommendations)} hotel recommendations")
            
            return {
                "human_text": f"Here are some great accommodation options in {slots.destination}:",
                "rr_payload": {
                    "session_id": session_id,
                    "slots": asdict(slots),
                    "hotels": hotel_recommendations,
                    "ui_actions": [
                        {"label": "Book Now", "action": "book_hotel"},
                        {"label": "See More Options", "action": "more_hotels"},
                        {"label": "Plan Full Trip", "action": "plan_trip"}
                    ],
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.8,
                        "query_type": "accommodation_query"
                    }
                }
            }
        except Exception as e:
            print(f"🏨 Error getting hotels: {e}")
            return {
                "human_text": f"I'm looking into accommodation options for {slots.destination}. Let me help you plan a complete trip instead!",
                "rr_payload": {
                    "session_id": session_id,
                    "slots": asdict(slots),
                    "ui_actions": [
                        {"label": "Plan Trip", "action": "plan_trip"},
                        {"label": "Set Dates", "action": "set_dates"}
                    ],
                    "metadata": {
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.7,
                        "query_type": "accommodation_query",
                        "error": str(e)
                    }
                }
            }