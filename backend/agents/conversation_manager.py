"""
Conversation Manager - Main orchestrator for the multi-agent travel system
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .slot_agents import DestinationAgent, DatesAgent, TravelersAgent, BudgetAgent, SlotAgent
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
        
        # Primary slot agent for intent detection flow
        self.slot_agent = SlotAgent(llm_client)
        
        # Individual slot agents for backward compatibility
        self.destination_agent = DestinationAgent(llm_client)
        self.dates_agent = DatesAgent(llm_client)
        self.travelers_agent = TravelersAgent(llm_client)
        self.budget_agent = BudgetAgent(llm_client)
        
        # Downstream agents
        self.retrieval_agent = RetrievalAgent(llm_client)
        self.planner_agent = PlannerAgent(llm_client)
        self.accommodation_agent = AccommodationAgent(llm_client)
        self.validator_agent = ValidatorAgent(llm_client)
        self.ux_agent = UXAgent(llm_client)
    
    async def process_message(self, message: str, session_id: str, current_slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        ROUTING FLOW: conversation_agent → slot_agent → retrieval_agent → route to appropriate agent
        Planner flow: slot_agent → retrieval_agent → planner_agent → validator_agent → conversation_agent
        Accommodation flow: retrieval_agent → accommodation_agent → booking flow
        Pre-generation mode: when intent = generate/plan → planner mode with trip-planner card
        """
        try:
            print(f"🔄 Processing message: {message[:50]}...")
            
            # STEP 1: Intent detection - conversation_agent → slot_agent
            slot_result = await self.slot_agent.extract_intent_and_destination(message)
            
            intent = slot_result.get('intent', 'general')
            destination = slot_result.get('destination_name')
            canonical_place_id = slot_result.get('canonical_place_id')
            confidence = slot_result.get('confidence', 0.5)
            clarify = slot_result.get('clarify')
            
            print(f"🎯 Intent: {intent}, Destination: {destination}, Confidence: {confidence:.2f}")
            
            # Handle clarification needed
            if clarify:
                return await self._generate_clarification_response(clarify, slot_result)
            
            # Update slots with detected destination
            slots = UserSlots(**current_slots) if current_slots else UserSlots()
            if destination:
                slots.destination = destination
                slots.canonical_place_id = canonical_place_id
            
            # STEP 2: Always call retrieval_agent first (unless brief reply expected)
            retrieval_facts = []
            if intent != 'general' or destination:
                try:
                    retrieval_facts = await self.retrieval_agent.get_facts(slots)
                    print(f"📋 Retrieved {len(retrieval_facts)} facts")
                except Exception as e:
                    print(f"❌ Retrieval agent error: {e}")
                    retrieval_facts = []
            
            # STEP 3: Route to appropriate agent based on intent
            if intent == 'plan':
                # Planner flow: slot_agent → retrieval_agent → planner_agent → validator_agent → conversation_agent
                return await self._handle_planner_flow(message, slots, retrieval_facts, session_id)
            
            elif intent == 'accommodation':
                # Accommodation flow: retrieval_agent → accommodation_agent → booking flow
                return await self._handle_accommodation_flow(message, slots, retrieval_facts, session_id)
            
            elif intent == 'find':
                # Find flow: retrieval_agent → conversation_agent (render cards)
                return await self._handle_find_flow(message, slots, retrieval_facts, session_id)
            
            else:
                # General conversation flow
                return await self._handle_general_flow(message, slots, retrieval_facts, session_id)
            
        except Exception as e:
            print(f"❌ ConversationManager error: {e}")
            return await self._generate_error_response(str(e))
    
    async def _generate_clarification_response(self, clarify: str, slot_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response when clarification is needed"""
        return {
            "chat_text": clarify,
            "ui_actions": [
                {
                    "type": "question_chip",
                    "payload": {
                        "id": f"clarify_{hash(clarify) % 1000}",
                        "question": "Please specify your destination",
                        "category": "clarification"
                    }
                }
            ],
            "metadata": {
                "intent": slot_result.get('intent', 'general'),
                "needs_clarification": True,
                "confidence": slot_result.get('confidence', 0.3)
            }
        }
    
    async def _handle_planner_flow(self, message: str, slots: UserSlots, retrieval_facts: List[Dict], session_id: str) -> Dict[str, Any]:
        """
        Planner flow: slot_agent → retrieval_agent → planner_agent → validator_agent → conversation_agent
        Pre-generation mode: when intent = generate/plan → treat as planner mode with trip-planner card
        """
        print(f"🗓️ Handling planner flow")
        
        # Check if we have enough information to generate itinerary
        missing_slots = []
        if not slots.destination:
            missing_slots.append("destination")
        if not slots.start_date:
            missing_slots.append("dates")
        if not slots.budget_per_night:
            missing_slots.append("budget")
        
        # Pre-generation mode: Present trip-planner card if missing essentials
        if missing_slots:
            return await self._present_trip_planner_card(message, slots, missing_slots)
        
        try:
            # Step 1: Generate itinerary using planner_agent
            planner_output = await self.planner_agent.generate_itinerary(slots, retrieval_facts)
            
            # Step 2: Validate using validator_agent
            validation_result = await self.validator_agent.validate(planner_output, retrieval_facts)
            
            # Step 3: Format response using ux_agent (conversation_agent render)
            ux_response = await self.ux_agent.format_response(planner_output, validation_result)
            
            # Step 4: Create UI actions for itinerary + hotel cards
            ui_actions = self._create_itinerary_ui_actions(planner_output)
            ui_actions.extend(self._create_hotel_ui_actions(planner_output.get('hotel_recommendations', [])))
            
            return {
                "chat_text": ux_response.get('human_text', 'Here\'s your personalized itinerary!'),
                "ui_actions": ui_actions,
                "metadata": {
                    "intent": "plan",
                    "planner_output": planner_output,
                    "validation": validation_result,
                    "confidence": validation_result.get('confidence', 0.8)
                }
            }
            
        except Exception as e:
            print(f"❌ Planner flow error: {e}")
            return await self._generate_error_response(f"Error generating itinerary: {str(e)}")
    
    async def _handle_accommodation_flow(self, message: str, slots: UserSlots, retrieval_facts: List[Dict], session_id: str) -> Dict[str, Any]:
        """Accommodation flow: retrieval_agent → accommodation_agent → booking flow"""
        print(f"🏨 Handling accommodation flow")
        
        if not slots.destination:
            return {
                "chat_text": "Which destination would you like to find accommodations for?",
                "ui_actions": [
                    {
                        "type": "question_chip",
                        "payload": {
                            "id": "destination_clarify",
                            "question": "Please specify your destination",
                            "category": "destination"
                        }
                    }
                ],
                "metadata": {"intent": "accommodation", "needs_destination": True}
            }
        
        try:
            # Get hotels using accommodation_agent
            hotels = await self.accommodation_agent.get_hotels_for_destination(slots.destination, slots)
            
            if hotels:
                # Create hotel cards
                ui_actions = self._create_hotel_ui_actions(hotels)
                
                # Generate contextual response
                response_text = f"Found {len(hotels)} great hotel options in {slots.destination}! Each one offers unique experiences perfect for your stay."
                
                # Add question chips for further assistance
                ui_actions.extend([
                    {
                        "type": "question_chip",
                        "payload": {
                            "id": f"hotel_compare_{hash(slots.destination) % 1000}",
                            "question": "Compare these hotels",
                            "category": "accommodation"
                        }
                    },
                    {
                        "type": "question_chip",
                        "payload": {
                            "id": f"hotel_budget_{hash(slots.destination) % 1000}",
                            "question": "Show budget-friendly options",
                            "category": "accommodation"
                        }
                    }
                ])
                
                return {
                    "chat_text": response_text,
                    "ui_actions": ui_actions,
                    "metadata": {
                        "intent": "accommodation",
                        "hotels_found": len(hotels),
                        "destination": slots.destination
                    }
                }
            else:
                return {
                    "chat_text": f"I couldn't find specific hotels in {slots.destination} right now. Let me help you with general accommodation information.",
                    "ui_actions": [
                        {
                            "type": "question_chip",
                            "payload": {
                                "id": "accommodation_help",
                                "question": "Show nearby destinations with hotels",
                                "category": "accommodation"
                            }
                        }
                    ],
                    "metadata": {"intent": "accommodation", "hotels_found": 0}
                }
                
        except Exception as e:
            print(f"❌ Accommodation flow error: {e}")
            return await self._generate_error_response(f"Error finding accommodations: {str(e)}")
    
    async def _handle_find_flow(self, message: str, slots: UserSlots, retrieval_facts: List[Dict], session_id: str) -> Dict[str, Any]:
        """Find flow: retrieval_agent → conversation_agent (render cards)"""
        print(f"🔍 Handling find flow")
        
        if slots.destination:
            # Generate destination card with information
            destination_cards = self._create_destination_cards([{
                'id': slots.canonical_place_id or f"dest_{hash(slots.destination) % 1000}",
                'name': slots.destination,
                'description': f"Explore the wonderful {slots.destination} with its unique attractions and experiences.",
                'highlights': ['Beautiful scenery', 'Rich culture', 'Adventure activities', 'Local cuisine'],
                'hero_image': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop'
            }])
            
            # Generate contextual response
            response_text = f"{slots.destination} offers incredible experiences! From stunning landscapes to rich cultural heritage, it's a perfect destination for travelers seeking adventure and beauty."
            
            # Add question chips
            question_chips = [
                {
                    "type": "question_chip",
                    "payload": {
                        "id": f"hotels_{hash(slots.destination) % 1000}",
                        "question": f"Hotels in {slots.destination}",
                        "category": "accommodation"
                    }
                },
                {
                    "type": "question_chip",
                    "payload": {
                        "id": f"plan_{hash(slots.destination) % 1000}",
                        "question": f"Plan a trip to {slots.destination}",
                        "category": "planning"
                    }
                }
            ]
            
            return {
                "chat_text": response_text,
                "ui_actions": destination_cards + question_chips,
                "metadata": {
                    "intent": "find",
                    "destination": slots.destination,
                    "cards_generated": len(destination_cards)
                }
            }
        else:
            # General discovery - show popular destinations
            popular_destinations = [
                {'name': 'Kerala, India', 'id': 'kerala_backwaters', 'description': 'God\'s Own Country with serene backwaters'},
                {'name': 'Rajasthan, India', 'id': 'rajasthan_india', 'description': 'Land of kings with majestic palaces'},
                {'name': 'Manali, India', 'id': 'manali_himachal', 'description': 'Mountain paradise in Himachal Pradesh'},
                {'name': 'Andaman Islands, India', 'id': 'andaman_islands', 'description': 'Tropical paradise with pristine beaches'},
                {'name': 'Rishikesh, India', 'id': 'rishikesh_uttarakhand', 'description': 'Yoga capital with adventure sports'}
            ]
            
            destination_cards = self._create_destination_cards(popular_destinations)
            
            return {
                "chat_text": "Here are some amazing destinations perfect for your next adventure! Each offers unique experiences and unforgettable memories.",
                "ui_actions": destination_cards,
                "metadata": {
                    "intent": "find",
                    "cards_generated": len(destination_cards),
                    "type": "discovery"
                }
            }
    
    async def _handle_general_flow(self, message: str, slots: UserSlots, retrieval_facts: List[Dict], session_id: str) -> Dict[str, Any]:
        """General conversation flow"""
        print(f"💬 Handling general flow")
        
        # Use UX agent to format general response
        ux_response = await self.ux_agent.format_general_response(message)
        
        return {
            "chat_text": ux_response.get('human_text', 'Hello! I\'m here to help you plan amazing trips. Where would you like to explore?'),
            "ui_actions": self._convert_ux_actions_to_ui_actions(ux_response.get('actions', [])),
            "metadata": {
                "intent": "general",
                "conversational": True
            }
        }
    
    async def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "chat_text": "I apologize, but I encountered an issue processing your request. Let me help you with travel planning in a different way.",
            "ui_actions": [
                {
                    "type": "question_chip",
                    "payload": {
                        "id": "help_destinations",
                        "question": "Show popular destinations",
                        "category": "help"
                    }
                },
                {
                    "type": "question_chip",
                    "payload": {
                        "id": "help_planning",
                        "question": "Help me plan a trip",
                        "category": "help"
                    }
                }
            ],
            "metadata": {
                "intent": "error",
                "error": error_message,
                "fallback": True
            }
        }
    
    async def _present_trip_planner_card(self, message: str, slots: UserSlots, missing_slots: List[str]) -> Dict[str, Any]:
        """Present trip planner card when essential information is missing"""
        return {
            "chat_text": f"I'd love to help you plan your trip! To create the perfect itinerary, I need a few more details.",
            "ui_actions": [
                {
                    "type": "trip_planner_card",
                    "payload": {
                        "id": "trip_planner_main",
                        "title": "Plan Your Perfect Trip",
                        "missing_slots": missing_slots,
                        "current_destination": slots.destination,
                        "current_dates": f"{slots.start_date} to {slots.end_date}" if slots.start_date and slots.end_date else None,
                        "current_budget": slots.budget_per_night
                    }
                }
            ],
            "metadata": {
                "intent": "plan",
                "pre_generation_mode": True,
                "missing_slots": missing_slots
            }
        }
    
    def _create_itinerary_ui_actions(self, planner_output: Dict) -> List[Dict[str, Any]]:
        """Create itinerary UI actions"""
        itinerary = planner_output.get('itinerary', [])
        if not itinerary:
            return []
        
        return [{
            "type": "itinerary_display",
            "payload": {
                "id": "generated_itinerary",
                "itinerary": itinerary,
                "total_days": len(itinerary),
                "highlights": [
                    activity.get('title', '') 
                    for day in itinerary[:3] 
                    for activity in day.get('activities', [])[:2]
                    if activity.get('title')
                ][:6]
            }
        }]
    
    def _create_hotel_ui_actions(self, hotels: List[Dict]) -> List[Dict[str, Any]]:
        """Create hotel card UI actions"""
        ui_actions = []
        for hotel in hotels:
            ui_actions.append({
                "type": "card_add", 
                "payload": {
                    "id": hotel.get('id', f"hotel_{hash(hotel.get('name', '')) % 1000}"),
                    "category": "hotel",
                    "title": hotel.get('name', 'Hotel'),
                    "rating": hotel.get('rating', 4.0),
                    "price_estimate": hotel.get('price_estimate', 5000),
                    "amenities": hotel.get('amenities', []),
                    "hero_image": hotel.get('hero_image', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'),
                    "booking_available": hotel.get('booking_link_estimate', True),
                    "distance_info": f"{hotel.get('distance_to_day1_km', 2.0)} km from center"
                }
            })
        return ui_actions
    
    def _create_destination_cards(self, destinations: List[Dict]) -> List[Dict[str, Any]]:
        """Create destination card UI actions"""
        cards = []
        for dest in destinations:
            cards.append({
                "type": "card_add",
                "payload": {
                    "id": dest['id'],
                    "category": "destination",
                    "title": dest['name'],
                    "description": dest.get('description', ''),
                    "highlights": dest.get('highlights', []),
                    "hero_image": dest.get('hero_image', 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=400&fit=crop'),
                    "plan_trip_button": True
                }
            })
        return cards
    
    def _convert_ux_actions_to_ui_actions(self, ux_actions: List[Dict]) -> List[Dict[str, Any]]:
        """Convert UX agent actions to UI actions format"""
        ui_actions = []
        for action in ux_actions:
            if action.get('action') == 'set_destination':
                ui_actions.append({
                    "type": "question_chip",
                    "payload": {
                        "id": f"dest_{hash(action.get('data', '')) % 1000}",
                        "question": action.get('label', 'Explore'),
                        "category": "destination"
                    }
                })
            else:
                ui_actions.append({
                    "type": "question_chip",
                    "payload": {
                        "id": f"action_{hash(action.get('label', '')) % 1000}",
                        "question": action.get('label', 'Learn More'),
                        "category": "general"
                    }
                })
        return ui_actions

    async def _build_smart_context(self, message: str, slots: UserSlots, session_id: str) -> str:
        """Build intelligent context for LLM based on user query"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mock_data import MOCK_DESTINATIONS, MOCK_HOTELS, MOCK_ACTIVITIES
            
            context_parts = []
            context_parts.append(f"User Query: '{message}'")
            
            # Add user context if available
            if slots.destination:
                context_parts.append(f"User is interested in: {slots.destination}")
            
            # Smart content matching - not rigid word matching
            message_words = message.lower().split()
            relevant_content = []
            
            # Check destinations (flexible matching)
            for dest in MOCK_DESTINATIONS:
                dest_name_words = dest.get('name', '').lower().split()
                dest_categories = [cat.lower() for cat in dest.get('category', [])]
                
                # Flexible matching logic
                name_match = any(word in dest_name_words for word in message_words)
                reverse_match = any(word in message_words for word in dest_name_words)
                category_match = any(cat_word in message.lower() for cat in dest_categories for cat_word in cat.split())
                
                if name_match or reverse_match or category_match:
                    relevant_content.append(f"Destination: {dest.get('name')} - {dest.get('pitch', '')} (Rating: {dest.get('rating', 4.5)}/5)")
            
            # Check hotels (flexible matching)
            for hotel in MOCK_HOTELS:
                hotel_location_words = hotel.get('location', '').lower().split()
                location_match = any(word in hotel_location_words for word in message_words)
                reverse_location_match = any(word in message_words for word in hotel_location_words)
                
                if location_match or reverse_location_match or 'hotel' in message.lower():
                    relevant_content.append(f"Hotel: {hotel.get('name')} in {hotel.get('location')} - ₹{hotel.get('price_per_night', 5000)}/night (Rating: {hotel.get('rating', 4.5)}/5)")
            
            # Check activities (flexible matching)
            for activity in MOCK_ACTIVITIES:
                activity_words = activity.get('title', '').lower().split()
                activity_location_words = activity.get('location', '').lower().split()
                
                activity_match = any(word in activity_words for word in message_words)
                location_match = any(word in activity_location_words for word in message_words)
                
                if activity_match or location_match:
                    relevant_content.append(f"Activity: {activity.get('title')} in {activity.get('location')} - {activity.get('description', '')}")
            
            # Add relevant content to context
            if relevant_content:
                context_parts.append("Relevant Travel Information:")
                for content in relevant_content[:5]:  # Top 5 matches
                    context_parts.append(f"- {content}")
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            print(f"❌ Error building context: {e}")
            return f"User is asking: '{message}'"
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent for metadata - matching server.py expectations"""
        message_lower = message.lower().strip()
        
        # Check for destination-specific queries (like "tell me about kerala")
        if self._is_destination_specific_query(message):
            return "destination_specific"
        
        # Check for destination discovery queries (like "popular destinations")
        elif self._is_destination_discovery_query(message):
            return "destination_discovery"
        
        # Check for accommodation queries (like "hotels in goa")
        elif self._is_accommodation_query(message):
            return "accommodation_query"
        
        # Activity-related intents  
        elif any(word in message_lower for word in ['activity', 'adventure', 'things to do', 'experience', 'attractions', 'sightseeing']):
            return "activity_inquiry"
        
        # Planning-related intents
        elif any(word in message_lower for word in ['plan', 'trip', 'itinerary', 'travel', 'vacation']):
            return "planning_inquiry"
        
        else:
            return "general_inquiry"
    
    async def _generate_smart_ui_actions(self, message: str, ai_response: str) -> list:
        """Generate contextually appropriate UI actions"""
        intent = self._classify_intent(message)
        
        if intent == "destination_inquiry":
            return [
                {"label": "🏖️ Beach Destinations", "action": "beaches"},
                {"label": "🏔️ Mountain Getaways", "action": "mountains"},
                {"label": "🏛️ Cultural Sites", "action": "cultural"},
                {"label": "🌴 Plan Trip", "action": "plan_trip"}
            ]
        elif intent == "hotel_inquiry":
            return [
                {"label": "🏨 Luxury Hotels", "action": "luxury_hotels"},
                {"label": "💰 Budget-Friendly", "action": "budget_hotels"},
                {"label": "⭐ Top Rated", "action": "top_rated"},
                {"label": "🔍 More Options", "action": "more_hotels"}
            ]
        elif intent == "activity_inquiry":
            return [
                {"label": "🏄‍♂️ Adventure Sports", "action": "adventure"},
                {"label": "🎭 Cultural Experiences", "action": "cultural_activities"},
                {"label": "🌅 Sightseeing Tours", "action": "sightseeing"},
                {"label": "📅 Book Now", "action": "book_activity"}
            ]
        else:
            return [
                {"label": "🗺️ Explore Places", "action": "explore_destinations"},
                {"label": "🏨 Find Hotels", "action": "find_hotels"},
                {"label": "🎯 Plan Custom Trip", "action": "custom_planning"}
            ]
    
    async def _generate_smart_hotel_cards(self, message: str, slots: UserSlots) -> list:
        """Generate hotel cards when relevant using AccommodationAgent"""
        intent = self._classify_intent(message)
        if intent not in ["accommodation_query"]:
            return []
        
        try:
            # Extract destination from message or slots
            destination = slots.destination if slots.destination else self._extract_destination_from_message(message)
            
            if not destination:
                print("❌ No destination found for hotel query")
                return []
            
            # Use AccommodationAgent to get hotels for the destination
            hotels = await self.accommodation_agent.get_hotels_for_destination(destination, slots)
            
            print(f"🏨 AccommodationAgent returned {len(hotels)} hotels for {destination}")
            return hotels
            
        except Exception as e:
            print(f"❌ Error generating hotel cards: {e}")
            return []
    
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
        """Handle general travel queries using LLM with comprehensive context"""
        
        try:
            # Use LLM to generate informative response with travel context
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import os
            
            # Get travel context and recommendations
            travel_context = self._get_general_travel_context(message)
            
            # Create comprehensive context for LLM
            context = f"""
User is asking: "{message}"

Provide a helpful travel-related response based on:
{travel_context}

Generate a response that:
1. Directly addresses their question/request
2. Provides specific, actionable travel advice
3. Includes relevant destination or activity suggestions when appropriate
4. Uses engaging, knowledgeable language
5. Encourages further exploration or planning

Be informative, friendly, and travel-focused in your response.
"""
            
            # Create LLM client for this call
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=session_id,
                system_message="You are an expert travel consultant with extensive knowledge of destinations, activities, and travel planning. Provide comprehensive, helpful advice for any travel-related query."
            ).with_model("openai", "gpt-4o-mini")
            
            # Generate response
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                ai_text = response.content
            else:
                ai_text = str(response)
            
            print(f"✅ Generated general travel response: {len(ai_text)} chars")
            
            return {
                "human_text": ai_text.strip(),
                "rr_payload": {
                    "session_id": session_id,
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "general_query",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ LLM general query failed: {e}")
            # Fallback response
            return {
                "human_text": "I'm here to help you plan amazing travel experiences! Whether you're looking for destinations, activities, accommodations, or planning advice, I can assist you. What would you like to explore?",
                "rr_payload": {
                    "session_id": session_id,
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "general_query",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.7
                    }
                }
            }
    
    def _get_general_travel_context(self, message: str) -> str:
        """Get relevant travel context for general queries"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mock_data import MOCK_DESTINATIONS, MOCK_HOTELS, MOCK_TOURS, MOCK_ACTIVITIES
            
            context_parts = []
            context_parts.append(f"User Query: {message}")
            
            # Analyze query for keywords and provide relevant context
            message_lower = message.lower()
            
            # Check for destination-related queries
            destination_keywords = ['destination', 'place', 'where', 'visit', 'travel', 'go']
            if any(keyword in message_lower for keyword in destination_keywords):
                popular_destinations = MOCK_DESTINATIONS[:3]
                context_parts.append("Popular Indian Destinations:")
                for dest in popular_destinations:
                    context_parts.append(f"- {dest.get('name')}: {dest.get('pitch', '')}")
            
            # Check for activity-related queries
            activity_keywords = ['activity', 'things to do', 'adventure', 'experience', 'fun']
            if any(keyword in message_lower for keyword in activity_keywords):
                popular_activities = MOCK_ACTIVITIES[:3]
                context_parts.append("Popular Activities:")
                for activity in popular_activities:
                    context_parts.append(f"- {activity.get('title')}: {activity.get('description', '')}")
            
            # Check for budget/planning queries
            planning_keywords = ['budget', 'cost', 'price', 'plan', 'itinerary', 'trip']
            if any(keyword in message_lower for keyword in planning_keywords):
                context_parts.append("Travel Planning Tips:")
                context_parts.append("- Budget varies by destination and season")
                context_parts.append("- Best time to visit depends on weather and activities")
                context_parts.append("- Book accommodations and transport in advance")
            
            # Check for seasonal queries
            seasonal_keywords = ['weather', 'season', 'time', 'when', 'best time']
            if any(keyword in message_lower for keyword in seasonal_keywords):
                context_parts.append("Seasonal Travel Information:")
                context_parts.append("- Winter (Nov-Feb): Best for Goa, Rajasthan, Kerala backwaters")
                context_parts.append("- Summer (Mar-May): Best for hill stations like Manali, Shimla")
                context_parts.append("- Monsoon (Jun-Sep): Best for Kerala, Northeast, Western Ghats")
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            print(f"❌ Error getting general travel context: {e}")
            return f"User is asking about travel: {message}"
    
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
        """Handle accommodation-specific queries using LLM with rich context"""
        
        try:
            # Use LLM to generate accommodation recommendations with context
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import os
            
            # Get accommodation context from mock data and LLM knowledge
            accommodation_context = self._get_accommodation_context(message, slots)
            
            # Create comprehensive context for LLM
            context = f"""
User is asking: "{message}"

Provide detailed accommodation recommendations based on:
{accommodation_context}

Generate a response that:
1. Acknowledges their accommodation request
2. Provides 2-3 specific hotel recommendations with details
3. Includes pricing, ratings, and key amenities
4. Mentions why each hotel is suitable for their needs
5. Uses engaging, helpful language

Focus on quality accommodations that match the destination and user preferences.
"""
            
            # Create LLM client for this call
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=session_id,
                system_message="You are an expert travel consultant specializing in accommodation recommendations. Provide detailed, helpful suggestions based on user needs and destination knowledge."
            ).with_model("openai", "gpt-4o-mini")
            
            # Generate response
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                ai_text = response.content
            else:
                ai_text = str(response)
            
            print(f"✅ Generated accommodation response: {len(ai_text)} chars")
            
            # Also generate hotel cards from available data
            hotel_cards = self._generate_hotel_cards_from_context(message, slots)
            
            return {
                "human_text": ai_text.strip(),
                "rr_payload": {
                    "session_id": session_id,
                    "hotels": hotel_cards,
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "accommodation_query",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.9
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ LLM accommodation query failed: {e}")
            # Fallback to basic response
            return {
                "human_text": "Here are some great accommodation options based on your request:",
                "rr_payload": {
                    "session_id": session_id,
                    "hotels": self._generate_hotel_cards_from_context(message, slots),
                    "ui_actions": [],
                    "metadata": {
                        "query_type": "accommodation_query",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "llm_confidence": 0.7
                    }
                }
            }
    
    def _get_accommodation_context(self, message: str, slots: UserSlots) -> str:
        """Get rich accommodation context from mock data and user query"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mock_data import MOCK_HOTELS, MOCK_DESTINATIONS
            
            # Extract destination from message or slots
            destination = slots.destination if slots.destination else self._extract_destination_from_message(message)
            
            context_parts = []
            context_parts.append(f"User Query: {message}")
            
            if destination:
                context_parts.append(f"Destination: {destination}")
                
                # Get destination info
                dest_info = None
                for dest in MOCK_DESTINATIONS:
                    if destination.lower() in dest.get('name', '').lower():
                        dest_info = dest
                        break
                
                if dest_info:
                    context_parts.append(f"Destination Details: {dest_info.get('pitch', '')}")
                    context_parts.append(f"Destination Category: {', '.join(dest_info.get('category', []))}")
                
                # Get available hotels for this destination
                relevant_hotels = [h for h in MOCK_HOTELS if destination.lower() in h.get('location', '').lower()]
                if relevant_hotels:
                    context_parts.append(f"Available Hotels in {destination}:")
                    for hotel in relevant_hotels[:3]:
                        context_parts.append(f"- {hotel.get('name')}: {hotel.get('description', '')} (₹{hotel.get('price_per_night', 0)}/night)")
            
            # Add user preferences if available
            if slots.budget_per_night:
                context_parts.append(f"Budget: ₹{slots.budget_per_night} per night")
            if slots.adults or slots.children:
                context_parts.append(f"Travelers: {slots.adults} adults, {slots.children} children")
            
            return '\n'.join(context_parts)
            
        except Exception as e:
            print(f"❌ Error getting accommodation context: {e}")
            return f"User is looking for accommodations: {message}"
    
    def _generate_hotel_cards_from_context(self, message: str, slots: UserSlots) -> list:
        """Generate hotel cards based on context and available data"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from mock_data import MOCK_HOTELS
            
            # Extract destination
            destination = slots.destination if slots.destination else self._extract_destination_from_message(message)
            
            if not destination:
                return []
            
            # Find relevant hotels
            relevant_hotels = [h for h in MOCK_HOTELS if destination.lower() in h.get('location', '').lower()]
            
            # Convert to card format
            hotel_cards = []
            for hotel in relevant_hotels[:3]:  # Limit to 3 hotels
                hotel_cards.append({
                    "id": hotel.get("id"),
                    "name": hotel.get("name"),
                    "rating": hotel.get("rating", 4.5),
                    "price_estimate": hotel.get("price_per_night", 5000),
                    "reason": hotel.get("description", "Great location and amenities"),
                    "amenities": hotel.get("amenities", []),
                    "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=300&fit=crop"
                })
            
            return hotel_cards
            
        except Exception as e:
            print(f"❌ Error generating hotel cards: {e}")
            return []
    
    def _extract_destination_from_message(self, message: str) -> str:
        """Extract destination from user message"""
        destinations = [
            "kerala", "goa", "rajasthan", "himachal", "uttarakhand", "kashmir",
            "manali", "shimla", "rishikesh", "haridwar", "dharamshala", "mcleodganj",
            "andaman", "lakshadweep", "mumbai", "delhi", "bangalore", "chennai",
            "kolkata", "pune", "hyderabad", "jaipur", "udaipur", "jodhpur",
            "agra", "varanasi", "pushkar", "mount abu", "ooty", "kodaikanal",
            "munnar", "alleppey", "kochi", "thekkady", "wayanad", "coorg",
            "hampi", "mysore", "darjeeling", "gangtok", "shillong", "kaziranga"
        ]
        
        message_lower = message.lower()
        for dest in destinations:
            if dest in message_lower:
                return dest.title()
        return None