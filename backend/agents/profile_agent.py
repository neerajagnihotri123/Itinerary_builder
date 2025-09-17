"""
ProfileAgent - Comprehensive traveler profiling and persona classification
Handles the "Discover" phase of customer journey with intelligent intake conversation
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from .persona_engine import PersonaEngine

class ProfileAgent:
    """Handles comprehensive traveler profiling and persona classification"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.persona_engine = PersonaEngine()
        
        # Profile intake stages for progressive profiling
        self.intake_stages = [
            "destination_and_basics",      # Travel destination and basic intent
            "travel_style_assessment",     # Adventure, culture, relaxation preferences
            "budget_exploration",          # Budget range and spending priorities
            "preferences_deep_dive",       # Specific preferences and constraints
            "propensity_evaluation"        # Willingness to pay and upgrade preferences
        ]
    
    async def initiate_intake_conversation(self, message: str, destination: str, session_id: str) -> dict:
        """Start comprehensive profile intake conversation"""
        
        # Initialize profile structure
        profile = {
            "session_id": session_id,
            "destination": destination,
            "intake_responses": {},
            "stage": "destination_and_basics",
            "progress": 0.2,  # 20% complete
            "created_at": datetime.now().isoformat()
        }
        
        # Generate contextual first question based on user's initial message
        first_question = await self._generate_contextual_opening(message, destination)
        
        return {
            "status": "intake_started",
            "next_question": first_question,
            "current_stage": "destination_and_basics", 
            "progress": 0.2,
            "question_type": "travel_style",
            "profile": profile
        }
    
    async def process_intake_response(self, response: str, current_profile: dict) -> dict:
        """Process user response and advance intake conversation"""
        
        current_stage = current_profile.get("stage", "destination_and_basics")
        
        # Store response
        current_profile["intake_responses"][current_stage] = response
        
        # Determine next stage
        next_stage_index = self.intake_stages.index(current_stage) + 1
        
        if next_stage_index < len(self.intake_stages):
            # Continue to next stage
            next_stage = self.intake_stages[next_stage_index]
            next_question = await self._generate_stage_question(next_stage, current_profile)
            
            return {
                "status": "intake_continuing",
                "next_question": next_question,
                "current_stage": next_stage,
                "progress": (next_stage_index + 1) / len(self.intake_stages),
                "profile": {
                    **current_profile,
                    "stage": next_stage,
                    "progress": (next_stage_index + 1) / len(self.intake_stages)
                }
            }
        else:
            # Complete intake and classify persona
            return await self._complete_intake_and_classify(current_profile)
    
    async def _generate_contextual_opening(self, message: str, destination: str) -> str:
        """Generate personalized opening question based on context"""
        
        context = f"""
        User message: "{message}"
        Destination: {destination or "Not specified"}
        
        You are a friendly travel concierge. Generate a warm, conversational opening question that:
        1. Acknowledges their travel interest enthusiastically
        2. Begins understanding their travel style (adventure, culture, luxury, budget, eco-conscious)
        3. Feels natural and engaging, not like a survey
        4. Leads to persona classification
        5. Is specific to their destination if mentioned
        
        Examples:
        - If destination mentioned: "Exciting! {destination} is amazing for {key activities}. What draws you most to travel - the thrill of adventure, diving into local culture, luxury relaxation, or finding great value experiences?"
        - If no destination: "I love helping plan amazing trips! What kind of experiences make you most excited when you travel - adventure activities, cultural discoveries, luxury relaxation, budget-friendly authentic experiences, or eco-conscious sustainable travel?"
        
        Keep it conversational and under 2 sentences.
        """
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=15.0
            )
            
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"LLM question generation failed: {e}")
            # Fallback to context-aware default
            if destination:
                return f"Exciting! {destination} has so much to offer. What draws you most to travel - adventure activities, cultural experiences, luxury relaxation, budget-friendly discoveries, or sustainable eco-conscious travel?"
            else:
                return "I'd love to help plan your perfect trip! What kind of experiences excite you most - adventure, culture, luxury, budget-friendly authentic experiences, or sustainable travel?"
    
    async def _generate_stage_question(self, stage: str, profile: dict) -> str:
        """Generate contextual question for specific intake stage"""
        
        stage_contexts = {
            "travel_style_assessment": f"""
            Based on their previous response: "{profile['intake_responses'].get('destination_and_basics', '')}"
            Generate a follow-up question to understand their travel pace and style preferences.
            Ask about: slow vs packed pace, group vs solo preferences, planning vs spontaneity.
            Keep it conversational and engaging.
            """,
            
            "budget_exploration": f"""
            Previous responses: {json.dumps(profile['intake_responses'], indent=2)}
            Generate a tactful question about their budget and spending priorities.
            Don't ask for exact amounts - ask about budget comfort level and what they prioritize spending on.
            Examples: "When it comes to your trip budget, what matters most to you - amazing accommodations, unique experiences, great food, or getting the best overall value?"
            """,
            
            "preferences_deep_dive": f"""
            Profile so far: {json.dumps(profile['intake_responses'], indent=2)}
            Ask about specific preferences: food, accessibility, sustainability importance.
            Make it relevant to their destination: {profile.get('destination', 'their chosen destination')}
            """,
            
            "propensity_evaluation": f"""
            Complete responses: {json.dumps(profile['intake_responses'], indent=2)}
            Ask about their willingness to upgrade or splurge on special experiences.
            Frame it positively: "If you found the perfect once-in-a-lifetime experience during your trip, how important is it to you to go for it even if it's a bit more than originally planned?"
            """
        }
        
        context = stage_contexts.get(stage, "Generate an appropriate follow-up question.")
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=15.0
            )
            
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"Stage question generation failed: {e}")
            return self._get_fallback_question(stage)
    
    def _get_fallback_question(self, stage: str) -> str:
        """Fallback questions for each stage"""
        fallback_questions = {
            "travel_style_assessment": "How do you like to experience a new place - with a packed itinerary full of activities, or taking it slow to really soak in the atmosphere?",
            "budget_exploration": "When planning your trip budget, what's most important to you - comfortable accommodations, amazing experiences, great food, or maximizing value?",
            "preferences_deep_dive": "Are there any specific preferences I should know about - dietary requirements, accessibility needs, or how important is sustainable/eco-friendly travel to you?",
            "propensity_evaluation": "If you discovered an amazing once-in-a-lifetime experience during your trip, how likely would you be to splurge a bit to make it happen?"
        }
        return fallback_questions.get(stage, "Tell me more about what you're looking for in this trip.")
    
    async def _complete_intake_and_classify(self, profile: dict) -> dict:
        """Complete intake process and perform persona classification"""
        
        # Extract structured data from responses
        structured_profile = await self._extract_structured_profile(profile["intake_responses"])
        
        # Classify persona using PersonaEngine
        persona_result = await self.persona_engine.classify_persona(structured_profile)
        
        # Assess propensity to pay
        propensity_result = await self._assess_propensity_to_pay(structured_profile, persona_result)
        
        # Complete profile
        complete_profile = {
            **profile,
            "structured_data": structured_profile,
            "persona_classification": persona_result,
            "propensity_assessment": propensity_result,
            "status": "complete",
            "completed_at": datetime.now().isoformat()
        }
        
        completion_message = await self._generate_completion_message(persona_result, structured_profile)
        
        return {
            "status": "intake_complete",
            "chat_text": completion_message,
            "profile": complete_profile,
            "next_action": "generate_itinerary_variants"
        }
    
    async def _extract_structured_profile(self, responses: dict) -> dict:
        """Extract structured data from conversational responses using LLM"""
        
        context = f"""
        Extract structured travel profile data from these conversational responses:
        
        {json.dumps(responses, indent=2)}
        
        Return JSON with this exact structure:
        {{
            "travel_style": ["adventure", "culture", "relaxation", "luxury", "budget", "eco_conscious"],
            "budget_range": {{"min": 50000, "max": 150000, "currency": "INR", "flexibility": "medium"}},
            "pace_preference": "balanced",
            "group_composition": {{"type": "couple", "adults": 2, "children": 0}},
            "accommodation_preference": ["boutique", "heritage", "luxury", "budget", "eco_friendly"],
            "activity_priorities": ["cultural_sites", "adventure_sports", "local_experiences", "nature", "food"],
            "food_preferences": ["local_cuisine", "vegetarian", "fine_dining", "street_food"],
            "sustainability_importance": 0.7,
            "authenticity_preference": 0.8,
            "comfort_level": 0.6,
            "spontaneity_vs_planning": 0.4
        }}
        
        Guidelines:
        - travel_style: Extract multiple styles if mentioned
        - budget_range: Infer from spending preferences, use INR
        - pace_preference: "slow", "balanced", or "packed"
        - All scores are 0.0-1.0 where 1.0 is maximum
        - Infer reasonable defaults if not explicitly stated
        """
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=15.0
            )
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and parse JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Profile extraction failed: {e}")
            # Return fallback profile based on responses
            return self._generate_fallback_profile(responses)
    
    def _generate_fallback_profile(self, responses: dict) -> dict:
        """Generate fallback profile when LLM extraction fails"""
        
        # Analyze responses for keywords
        all_text = ' '.join(responses.values()).lower()
        
        travel_style = []
        if any(word in all_text for word in ['adventure', 'thrill', 'exciting', 'active']):
            travel_style.append('adventure')
        if any(word in all_text for word in ['culture', 'history', 'heritage', 'local']):
            travel_style.append('culture')
        if any(word in all_text for word in ['relax', 'calm', 'peaceful', 'spa']):
            travel_style.append('relaxation')
        if any(word in all_text for word in ['luxury', 'premium', 'high-end', 'fine']):
            travel_style.append('luxury')
        if any(word in all_text for word in ['budget', 'cheap', 'affordable', 'value']):
            travel_style.append('budget')
        if any(word in all_text for word in ['eco', 'sustainable', 'green', 'environment']):
            travel_style.append('eco_conscious')
        
        # Default to balanced if no clear style
        if not travel_style:
            travel_style = ['culture', 'relaxation']
        
        return {
            "travel_style": travel_style,
            "budget_range": {"min": 50000, "max": 100000, "currency": "INR", "flexibility": "medium"},
            "pace_preference": "balanced",
            "group_composition": {"type": "couple", "adults": 2, "children": 0},
            "accommodation_preference": ["boutique", "heritage"],
            "activity_priorities": ["cultural_sites", "local_experiences"],
            "food_preferences": ["local_cuisine"],
            "sustainability_importance": 0.5,
            "authenticity_preference": 0.7,
            "comfort_level": 0.6,
            "spontaneity_vs_planning": 0.4
        }
    
    async def _assess_propensity_to_pay(self, profile: dict, persona_result: dict) -> dict:
        """Assess user's propensity to pay and spending patterns"""
        
        base_budget = profile.get("budget_range", {}).get("max", 100000)
        primary_persona = persona_result.get("primary_persona", "balanced_traveler")
        
        # Persona-based propensity multipliers from PRD requirements
        persona_multipliers = {
            "luxury_connoisseur": {
                "upgrade_willingness": 0.9, 
                "premium_multiplier": 2.0, 
                "discount_sensitivity": 0.2
            },
            "adventure_seeker": {
                "upgrade_willingness": 0.7, 
                "premium_multiplier": 1.2, 
                "discount_sensitivity": 0.4
            },
            "cultural_explorer": {
                "upgrade_willingness": 0.8, 
                "premium_multiplier": 1.3, 
                "discount_sensitivity": 0.3
            },
            "budget_backpacker": {
                "upgrade_willingness": 0.3, 
                "premium_multiplier": 0.6, 
                "discount_sensitivity": 0.9
            },
            "eco_conscious_traveler": {
                "upgrade_willingness": 0.8, 
                "premium_multiplier": 1.4, 
                "discount_sensitivity": 0.3
            }
        }
        
        multiplier = persona_multipliers.get(primary_persona, {
            "upgrade_willingness": 0.6, 
            "premium_multiplier": 1.0, 
            "discount_sensitivity": 0.5
        })
        
        # Calculate spending thresholds
        propensity_assessment = {
            "base_budget": base_budget,
            "upgrade_willingness": multiplier["upgrade_willingness"],
            "premium_threshold": int(base_budget * multiplier["premium_multiplier"]),
            "discount_sensitivity": multiplier["discount_sensitivity"],
            "spending_personality": primary_persona,
            "value_drivers": self._identify_value_drivers(profile, primary_persona),
            "budget_flexibility": profile.get("budget_range", {}).get("flexibility", "medium")
        }
        
        return propensity_assessment
        
    def _identify_value_drivers(self, profile: dict, persona: str) -> List[str]:
        """Identify what drives spending decisions for this user"""
        
        # Value drivers based on persona from PRD requirements
        persona_drivers = {
            "luxury_connoisseur": ["premium_service", "exclusive_access", "comfort", "status", "personalization"],
            "adventure_seeker": ["unique_experiences", "safety_equipment", "expert_guides", "adrenaline_activities", "equipment_quality"],
            "cultural_explorer": ["authenticity", "local_guides", "heritage_access", "cultural_immersion", "educational_value"],
            "budget_backpacker": ["value_for_money", "essential_experiences", "cost_savings", "flexibility", "social_opportunities"],
            "eco_conscious_traveler": ["sustainability", "local_community_support", "eco_certifications", "responsible_tourism", "environmental_impact"]
        }
        
        drivers = persona_drivers.get(persona, ["authentic_experiences", "good_value", "memorable_moments"])
        
        # Add profile-specific drivers
        if profile.get("sustainability_importance", 0) > 0.7:
            drivers.append("environmental_impact")
        
        if profile.get("authenticity_preference", 0) > 0.7:
            drivers.append("authentic_local_experiences")
            
        return drivers
    
    async def _generate_completion_message(self, persona_result: dict, profile: dict) -> str:
        """Generate completion message with persona insights"""
        
        primary_persona = persona_result.get("primary_persona", "traveler")
        confidence = persona_result.get("primary_confidence", 0.8)
        
        # Persona-specific completion messages
        persona_messages = {
            "adventure_seeker": "Perfect! I can see you're an adventure seeker who loves thrill and excitement. I'll create action-packed itineraries with the best adventure activities and experiences.",
            
            "cultural_explorer": "Wonderful! You're a cultural explorer who values authentic experiences and local immersion. I'll focus on heritage sites, local culture, and meaningful connections.",
            
            "luxury_connoisseur": "Excellent! As a luxury connoisseur, you appreciate the finer things in travel. I'll curate premium experiences with exceptional service and exclusive access.",
            
            "budget_backpacker": "Great! You're a savvy budget traveler who values authentic experiences and great value. I'll find amazing experiences that don't break the bank.",
            
            "eco_conscious_traveler": "Fantastic! Your commitment to sustainable travel is admirable. I'll prioritize eco-friendly options and experiences that support local communities."
        }
        
        base_message = persona_messages.get(primary_persona, 
            "Perfect! I have a great understanding of your travel style and preferences.")
        
        # Add confidence and next steps
        if confidence > 0.8:
            confidence_text = "I'm very confident about"
        elif confidence > 0.6:
            confidence_text = "I have a good sense of"
        else:
            confidence_text = "I understand"
        
        travel_style = ', '.join(profile.get('travel_style', ['your travel style']))
        
        completion_message = f"{base_message} {confidence_text} your preferences for {travel_style}. \n\nNow let me create three amazing itinerary options for you - an adventurous packed schedule, a balanced mix of activities and relaxation, and a luxury premium experience. Which would you like to see first?"
        
        return completion_message