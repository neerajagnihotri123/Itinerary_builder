"""
Profile Intake Agent - Conversationally collects traveler preferences, budget, constraints, and travel style
Uses dynamic questioning to build a travel persona
"""

import os
import logging
from typing import Dict, List, Any, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models.schemas import ChatResponse, UIAction, ProfileIntakeResponse
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class ProfileIntakeAgent:
    """Agent responsible for collecting traveler profiles through conversational interaction"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # LLM client will be initialized per session
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for session"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_system_message()
        ).with_model("openai", "gpt-4o-mini")
    
    def _get_system_message(self) -> str:
        """Get system message for LLM"""
        return """You are Travello.ai's Profile Intake Agent. Your role is to conversationally collect traveler preferences, budget, constraints, and travel style through natural dialogue.

KEY RESPONSIBILITIES:
1. Engage users in natural conversation to understand their travel preferences
2. Identify travel intent (planning, accommodation, general inquiry)
3. Collect essential trip details: destination, dates, travelers, budget
4. Understand travel style: adventurous, cultural, luxury, budget, eco-conscious
5. Gather constraints: mobility, dietary, time limitations
6. Build comprehensive traveler persona for downstream agents

CONVERSATION FLOW:
- Start with understanding basic trip intent
- If planning trip, collect destination preferences
- Ask about dates and group size
- Understand budget range and priorities
- Explore travel style and preferences
- Identify any special requirements

PERSONALITY:
- Friendly, enthusiastic, and genuinely helpful
- Natural conversationalist who builds rapport
- Progressive questioning (don't ask everything at once)
- Adaptive based on user responses

ACTIONS:
- Generate trip_planner_card when basic details needed
- Generate personalization_modal when profile intake required
- Provide destination suggestions when user is undecided
- Create follow-up questions to deepen understanding

Always provide helpful, specific, and engaging responses that move the conversation forward."""

    async def process_message(self, session_id: str, user_message: str) -> ChatResponse:
        """Process user message and manage profile intake flow"""
        try:
            logger.info(f"🏷️ Profile Intake processing message for session {session_id}")
            
            # Get current session context
            profile = self.context_store.get_profile(session_id)
            trip_details = self.context_store.get_trip_details(session_id)
            messages = self.context_store.get_messages(session_id)
            
            # Analyze message intent and determine next action
            intent_analysis = await self._analyze_intent(user_message, profile, trip_details)
            
            # Route based on intent
            if intent_analysis["intent"] == "trip_planning":
                return await self._handle_trip_planning(session_id, user_message, intent_analysis)
            elif intent_analysis["intent"] == "accommodation":
                return await self._handle_accommodation_request(session_id, user_message, intent_analysis)
            elif intent_analysis["intent"] == "general":
                return await self._handle_general_inquiry(session_id, user_message, intent_analysis)
            else:
                return await self._handle_profile_continuation(session_id, user_message, intent_analysis)
                
        except Exception as e:
            logger.error(f"Profile intake error: {e}")
            return ChatResponse(
                chat_text="I'd love to help you plan your trip! Could you tell me where you're thinking of going?",
                ui_actions=[],
                updated_profile={},
                followup_questions=["What destination interests you?"],
                analytics_tags=["profile_intake_error"]
            )

    async def _analyze_intent(self, message: str, profile: Dict, trip_details: Dict) -> Dict[str, Any]:
        """Analyze user message intent using LLM"""
        try:
            context = f"""
            Analyze this user message for travel intent:
            
            User message: "{message}"
            Current profile completeness: {len(profile)} fields collected
            Existing trip details: {trip_details}
            
            Classify the intent as one of:
            - trip_planning: User wants to plan a new trip or mentions destinations
            - accommodation: User specifically asking about hotels/stays
            - general: General questions, greetings, or non-specific inquiries
            - profile_continuation: User providing more profile information
            
            Extract any mentioned information:
            - destination (if mentioned)
            - travel_style preferences (adventurous, relaxing, cultural, etc.)
            - budget indicators (luxury, budget, mid-range)
            - group_size or travel companions
            - trip_duration hints
            
            Respond in JSON format:
            {{
                "intent": "trip_planning|accommodation|general|profile_continuation",
                "confidence": 0.0-1.0,
                "destination": "extracted destination or null",
                "travel_style": "extracted style or null",
                "budget_preference": "luxury|mid-range|budget or null",
                "group_info": "extracted group info or null",
                "reasoning": "brief explanation of classification"
            }}
            """
            
            user_msg = UserMessage(text=context)
            llm_client = self._get_llm_client("temp_session")  # Use temp session for intent analysis
            response = await llm_client.send_message(user_msg)
            
            # Parse JSON response (handle markdown-wrapped JSON)
            import json
            import re
            try:
                # Remove markdown code blocks if present
                json_text = response
                if '```json' in json_text:
                    json_match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                elif '```' in json_text:
                    json_match = re.search(r'```\s*(.*?)\s*```', json_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1)
                
                result = json.loads(json_text.strip())
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}, response: {response}")
                # Fallback parsing if JSON fails
                content = response.lower()
                intent = "general"
                
                if any(word in content for word in ["plan", "trip", "travel", "visit", "go to"]):
                    intent = "trip_planning"
                elif any(word in content for word in ["hotel", "stay", "accommodation", "resort"]):
                    intent = "accommodation"
                elif len(profile) > 0 and not trip_details:
                    intent = "profile_continuation"
                
                return {
                    "intent": intent,
                    "confidence": 0.7,
                    "destination": self._extract_destination(message),
                    "reasoning": "Fallback analysis due to JSON parsing error"
                }
            
        except Exception as e:
            logger.error(f"Intent analysis error: {e}")
            return {"intent": "general", "confidence": 0.5, "reasoning": f"Error: {str(e)}"}

    async def _handle_trip_planning(self, session_id: str, message: str, intent_analysis: Dict) -> ChatResponse:
        """Handle trip planning requests"""
        trip_details = self.context_store.get_trip_details(session_id)
        
        # Check if we have basic trip details
        has_destination = bool(trip_details.get("destination") or intent_analysis.get("destination"))
        has_dates = bool(trip_details.get("start_date") and trip_details.get("end_date"))
        has_travelers = bool(trip_details.get("adults"))
        
        if not (has_destination and has_dates and has_travelers):
            # Need trip planner card to collect basic details
            ui_actions = [
                UIAction(
                    type="trip_planner_card",
                    payload={
                        "destination": intent_analysis.get("destination") or trip_details.get("destination", ""),
                        "message": "I'd love to help you plan this trip! Let me get some basic details first."
                    }
                ).dict()
            ]
            
            response_text = f"Exciting! I'd love to help you plan your trip"
            if intent_analysis.get("destination"):
                response_text += f" to {intent_analysis['destination']}"
            response_text += ". Let me gather some basic details to create the perfect itinerary for you."
            
            return ChatResponse(
                chat_text=response_text,
                ui_actions=ui_actions,
                updated_profile={},
                followup_questions=[],
                analytics_tags=["trip_planning_started", "trip_planner_card_shown"]
            )
        else:
            # Have basic details, move to persona classification
            await self.event_bus.emit(EventTypes.PROFILE_INTAKE_COMPLETED, {
                "trip_details": trip_details,
                "message": message
            }, session_id)
            
            return ChatResponse(
                chat_text="Perfect! I have your trip details. Now let me learn about your travel style to create personalized recommendations.",
                ui_actions=[
                    UIAction(
                        type="personalization_modal",
                        payload={
                            "destination": trip_details.get("destination"),
                            "message": "Tell me about your travel preferences"
                        }
                    ).dict()
                ],
                updated_profile={},
                followup_questions=[],
                analytics_tags=["profile_intake_to_personalization"]
            )

    async def _handle_accommodation_request(self, session_id: str, message: str, intent_analysis: Dict) -> ChatResponse:
        """Handle accommodation-specific requests"""
        destination = intent_analysis.get("destination")
        
        if destination:
            # Generate accommodation recommendations
            accommodations = await self._generate_accommodation_suggestions(destination)
            
            ui_actions = []
            for hotel in accommodations:
                ui_actions.append(
                    UIAction(
                        type="card_add",
                        payload={
                            "category": "hotel",
                            "id": hotel["id"],
                            "title": hotel["name"],
                            "description": hotel["description"],
                            "image": hotel["image"],
                            "rating": hotel["rating"],
                            "price_estimate": hotel["price"],
                            "location": hotel["location"],
                            "amenities": hotel["amenities"]
                        }
                    ).dict()
                )
            
            return ChatResponse(
                chat_text=f"Here are some excellent accommodation options in {destination}. Each offers unique experiences perfect for different travel styles.",
                ui_actions=ui_actions,
                updated_profile={},
                followup_questions=[
                    f"Would you like luxury resorts in {destination}?",
                    f"Are you looking for budget-friendly options?",
                    f"Do you prefer boutique hotels or larger chains?"
                ],
                analytics_tags=["accommodation_search", destination.lower().replace(" ", "_")]
            )
        else:
            return ChatResponse(
                chat_text="I'd be happy to help you find great accommodations! Which destination are you considering?",
                ui_actions=[],
                updated_profile={},
                followup_questions=["What destination are you looking at?"],
                analytics_tags=["accommodation_no_destination"]
            )

    async def _handle_general_inquiry(self, session_id: str, message: str, intent_analysis: Dict) -> ChatResponse:
        """Handle general travel inquiries and greetings"""
        try:
            context = f"""
            You are Travello.ai, a friendly AI travel assistant. Respond naturally and helpfully to this user message:
            
            User message: "{message}"
            
            Guidelines:
            - Be enthusiastic and helpful about travel
            - If it's a greeting, respond warmly and introduce your capabilities
            - If it's a general travel question, provide helpful information
            - Always try to guide the conversation toward planning a trip
            - Keep responses concise but engaging
            - End with a question to continue the conversation
            
            Respond as if talking directly to the user, no JSON format needed.
            """
            
            user_msg = UserMessage(text=context)
            llm_client = self._get_llm_client(session_id)
            response = await llm_client.send_message(user_msg)
            
            return ChatResponse(
                chat_text=response,  # response is already a string
                ui_actions=[],
                updated_profile={},
                followup_questions=[
                    "Are you planning a trip somewhere?",
                    "What kind of travel experience interests you most?",
                    "Any particular destinations on your wishlist?"
                ],
                analytics_tags=["general_inquiry"]
            )
        except Exception as e:
            logger.error(f"General inquiry error: {e}")
            return ChatResponse(
                chat_text="Hello! I'm your AI travel assistant. I'd love to help you plan an amazing trip. Where would you like to explore?",
                ui_actions=[],
                updated_profile={},
                followup_questions=["What destination interests you?"],
                analytics_tags=["general_fallback"]
            )

    async def _handle_profile_continuation(self, session_id: str, message: str, intent_analysis: Dict) -> ChatResponse:
        """Handle continuation of profile building process"""
        profile = self.context_store.get_profile(session_id)
        
        # Update profile with new information
        extracted_info = intent_analysis.get("extracted_info", {})
        profile.update(extracted_info)
        self.context_store.set_profile(session_id, profile)
        
        # Determine next questions based on current profile completeness
        missing_fields = self._get_missing_profile_fields(profile)
        
        if missing_fields:
            next_question = self._generate_next_question(missing_fields[0], profile)
            return ChatResponse(
                chat_text=next_question,
                ui_actions=[],
                updated_profile=profile,
                followup_questions=[],
                analytics_tags=["profile_continuation"]
            )
        else:
            # Profile complete, trigger persona classification
            await self.event_bus.emit(EventTypes.PROFILE_INTAKE_COMPLETED, {
                "profile": profile
            }, session_id)
            
            return ChatResponse(
                chat_text="Perfect! I have a great understanding of your travel preferences. Let me create personalized itinerary options for you.",
                ui_actions=[],
                updated_profile=profile,
                followup_questions=[],
                analytics_tags=["profile_complete"]
            )

    async def process_profile_responses(self, session_id: str, responses: Dict[str, Any]) -> ProfileIntakeResponse:
        """Process profile responses from personalization modal"""
        try:
            logger.info(f"Processing profile responses for session {session_id}")
            
            # Store profile responses
            self.context_store.set_profile(session_id, responses)
            
            # Analyze responses to generate persona tags
            persona_tags = self._generate_persona_tags(responses)
            
            # Trigger persona classification
            await self.event_bus.emit(EventTypes.PROFILE_INTAKE_COMPLETED, {
                "profile": responses,
                "persona_tags": persona_tags
            }, session_id)
            
            return ProfileIntakeResponse(
                profile_complete=True,
                persona_tags=persona_tags,
                next_questions=[],
                ui_actions=[]
            )
            
        except Exception as e:
            logger.error(f"Profile response processing error: {e}")
            return ProfileIntakeResponse(
                profile_complete=False,
                persona_tags=[],
                next_questions=["Could you tell me more about your travel preferences?"],
                ui_actions=[]
            )

    def _extract_destination(self, message: str) -> Optional[str]:
        """Extract destination from message"""
        destinations = [
            "Goa", "Kerala", "Rajasthan", "Manali", "Rishikesh", "Kashmir", "Ladakh",
            "Andaman Islands", "Pondicherry", "Himachal Pradesh", "Mumbai", "Delhi",
            "Bangalore", "Chennai", "Hyderabad", "Pune", "Jaipur", "Udaipur", "Jodhpur"
        ]
        
        message_lower = message.lower()
        for dest in destinations:
            if dest.lower() in message_lower:
                return dest
        return None

    def _extract_trip_info(self, message: str) -> Dict[str, Any]:
        """Extract trip information from message"""
        info = {}
        message_lower = message.lower()
        
        # Extract budget indicators
        if any(word in message_lower for word in ["luxury", "premium", "high-end"]):
            info["budget_preference"] = "luxury"
        elif any(word in message_lower for word in ["budget", "cheap", "affordable"]):
            info["budget_preference"] = "budget"
        elif any(word in message_lower for word in ["mid-range", "moderate"]):
            info["budget_preference"] = "mid-range"
        
        # Extract travel style
        if any(word in message_lower for word in ["adventure", "exciting", "thrill"]):
            info["travel_style"] = "adventurous"
        elif any(word in message_lower for word in ["culture", "heritage", "history"]):
            info["travel_style"] = "cultural"
        elif any(word in message_lower for word in ["relax", "spa", "peaceful"]):
            info["travel_style"] = "relaxation"
        
        return info

    def _get_missing_profile_fields(self, profile: Dict[str, Any]) -> List[str]:
        """Get list of missing profile fields"""
        required_fields = [
            "travel_style", "budget_preference", "group_type", 
            "activity_preferences", "accommodation_preference"
        ]
        
        missing = []
        for field in required_fields:
            if field not in profile or not profile[field]:
                missing.append(field)
        
        return missing

    def _generate_next_question(self, missing_field: str, profile: Dict[str, Any]) -> str:
        """Generate next question based on missing field"""
        questions = {
            "travel_style": "What kind of travel experience excites you most - adventure and outdoor activities, cultural exploration and local experiences, or relaxation and luxury?",
            "budget_preference": "What's your preferred budget range for this trip? Are you looking for luxury experiences, mid-range comfort, or budget-friendly options?",
            "group_type": "Who will you be traveling with? Solo, as a couple, with family, or a group of friends?",
            "activity_preferences": "What activities interest you most? Outdoor adventures, cultural sites, nightlife, shopping, or local cuisine?",
            "accommodation_preference": "What type of accommodation do you prefer? Luxury resorts, boutique hotels, budget-friendly stays, or unique local experiences?"
        }
        
        return questions.get(missing_field, "Tell me more about your travel preferences!")

    def _generate_persona_tags(self, responses: Dict[str, Any]) -> List[str]:
        """Generate persona tags from profile responses"""
        tags = []
        
        # Analyze vacation style
        vacation_style = responses.get("vacation_style", "")
        if vacation_style == "adventurous":
            tags.extend(["adventure_seeker", "outdoor_enthusiast"])
        elif vacation_style == "relaxing":
            tags.extend(["relaxation_focused", "wellness_oriented"])
        elif vacation_style == "balanced":
            tags.extend(["balanced_traveler", "flexible"])
        
        # Analyze experience type
        experience_type = responses.get("experience_type", "")
        if experience_type == "nature":
            tags.extend(["nature_lover", "outdoor_activities"])
        elif experience_type == "culture":
            tags.extend(["cultural_explorer", "heritage_interested"])
        
        # Analyze attraction preference
        attraction_pref = responses.get("attraction_preference", "")
        if attraction_pref == "popular":
            tags.extend(["mainstream_attractions", "iconic_experiences"])
        elif attraction_pref == "local":
            tags.extend(["authentic_experiences", "local_culture"])
        elif attraction_pref == "both":
            tags.extend(["comprehensive_explorer", "diverse_interests"])
        
        # Analyze accommodation preferences
        accommodation = responses.get("accommodation", [])
        if "luxury_hotels" in accommodation:
            tags.append("luxury_oriented")
        if "budget_hotels" in accommodation or "hostels" in accommodation:
            tags.append("budget_conscious")
        if "boutique_hotels" in accommodation or "bnb" in accommodation:
            tags.append("unique_stays")
        
        return list(set(tags))  # Remove duplicates

    async def _generate_accommodation_suggestions(self, destination: str) -> List[Dict[str, Any]]:
        """Generate accommodation suggestions for destination using LLM"""
        try:
            context = f"""
            Generate 3 diverse accommodation recommendations for {destination} covering different budget ranges and styles:
            
            1. Luxury Option (₹15,000-25,000 per night)
            2. Mid-Range Option (₹8,000-15,000 per night) 
            3. Budget Option (₹3,000-6,000 per night)
            
            For each accommodation, provide:
            - name (realistic hotel/resort name)
            - description (2-3 sentences highlighting unique features)
            - location (specific area in {destination})
            - rating (4.0-5.0 realistic rating)
            - price_min and price_max (in INR per night)
            - 5 key amenities
            
            Respond in JSON array format:
            [
                {{
                    "name": "Hotel Name",
                    "description": "Detailed description",
                    "location": "Specific area in {destination}",
                    "rating": 4.5,
                    "price_min": 15000,
                    "price_max": 25000,
                    "amenities": ["amenity1", "amenity2", "amenity3", "amenity4", "amenity5"]
                }}
            ]
            """
            
            user_msg = UserMessage(text=context)
            llm_client = self._get_llm_client("temp_session")  # Use temp session for accommodation suggestions
            response = await llm_client.send_message(user_msg)
            
            # Parse JSON response
            import json
            try:
                accommodations_data = json.loads(response.content)
                
                # Convert to expected format
                accommodations = []
                for i, acc in enumerate(accommodations_data):
                    accommodations.append({
                        "id": f"hotel_{destination.lower().replace(' ', '_')}_{i+1}",
                        "name": acc["name"],
                        "description": acc["description"],
                        "image": f"https://images.unsplash.com/800x400/?{acc['name'].lower().replace(' ', '-')}-{destination.lower()}",
                        "rating": acc["rating"],
                        "price": {"min": acc["price_min"], "max": acc["price_max"]},
                        "location": acc["location"],
                        "amenities": acc["amenities"]
                    })
                
                return accommodations
                
            except json.JSONDecodeError:
                logger.error("Failed to parse accommodation JSON, using fallback")
                return self._get_fallback_accommodations(destination)
            
        except Exception as e:
            logger.error(f"Accommodation generation error: {e}")
            return self._get_fallback_accommodations(destination)

    def _get_fallback_accommodations(self, destination: str) -> List[Dict[str, Any]]:
        """Fallback accommodation data if LLM fails"""
        return [
            {
                "id": f"hotel_{destination.lower().replace(' ', '_')}_1",
                "name": f"Premium {destination} Resort",
                "description": f"Luxury accommodation in {destination} with world-class amenities",
                "image": f"https://images.unsplash.com/800x400/?luxury-resort-{destination.lower()}",
                "rating": 4.7,
                "price": {"min": 15000, "max": 25000},
                "location": f"Prime {destination}",
                "amenities": ["Pool", "Spa", "Fine Dining", "WiFi", "Room Service"]
            }
        ]