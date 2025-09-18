"""
Persona Classification Agent - Classifies travelers into predefined personas based on collected data
Feeds persona tags to downstream agents for personalized itinerary generation
"""

import os
import logging
from typing import Dict, List, Any, Optional
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models.schemas import PersonaClassificationResponse, PersonaType, UIAction
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class PersonaClassificationAgent:
    """Agent responsible for classifying travelers into personas and triggering itinerary generation"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Subscribe to profile intake completion events
        self.event_bus.subscribe(EventTypes.PROFILE_INTAKE_COMPLETED, self._handle_profile_completion)
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for session"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_system_message()
        ).with_model("openai", "gpt-4o-mini")
    
    def _get_system_message(self) -> str:
        return """You are Travello.ai's Persona Classification Agent. Your role is to analyze traveler profiles and classify them into specific personas that guide itinerary generation.

PERSONA TYPES:
1. ADVENTURER: Seeks thrills, outdoor activities, extreme sports, off-beat destinations
2. CULTURAL_EXPLORER: Interested in heritage, local traditions, museums, authentic experiences
3. LUXURY_CONNOISSEUR: Prefers premium experiences, fine dining, luxury accommodations, exclusive access
4. BUDGET_BACKPACKER: Cost-conscious, authentic local experiences, budget accommodations, street food
5. ECO_CONSCIOUS: Sustainable travel, eco-friendly options, nature conservation, minimal impact
6. FAMILY_ORIENTED: Kid-friendly activities, safe destinations, educational experiences, comfort
7. BUSINESS_TRAVELER: Efficient travel, meeting facilities, good connectivity, convenient locations

CLASSIFICATION CRITERIA:
- Budget preferences and spending patterns
- Activity preferences and travel style
- Accommodation choices and priorities
- Travel group composition and dynamics
- Values and motivations for travel
- Risk tolerance and adventure seeking
- Cultural engagement preferences

OUTPUT REQUIREMENTS:
- Primary persona type with confidence score
- Secondary persona traits as tags
- Explanation of classification reasoning
- Recommendations for itinerary customization
- Propensity-to-pay analysis for pricing strategy

PERSONALITY:
- Analytical and insightful
- Data-driven decision making
- Clear explanation of reasoning
- Actionable recommendations for downstream agents"""

    async def _handle_profile_completion(self, event):
        """Handle profile intake completion event"""
        try:
            session_id = event.session_id
            profile_data = event.data.get("profile", {})
            trip_details = self.context_store.get_trip_details(session_id)
            
            logger.info(f"🎭 Handling profile completion for session {session_id}")
            
            # Classify persona
            classification_result = await self.classify_persona(session_id, profile_data, trip_details)
            
            # Store persona classification
            self.context_store.set_persona(session_id, classification_result)
            
            # Trigger itinerary generation
            await self.event_bus.emit(EventTypes.PERSONA_CLASSIFIED, {
                "persona_type": classification_result["persona_type"],
                "persona_tags": classification_result["persona_tags"],
                "confidence": classification_result["confidence"],
                "trip_details": trip_details,
                "profile_data": profile_data
            }, session_id)
            
        except Exception as e:
            logger.error(f"Profile completion handling error: {e}")

    async def classify_and_generate(self, session_id: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> PersonaClassificationResponse:
        """Main endpoint for persona classification and itinerary generation trigger"""
        try:
            logger.info(f"🎭 Classifying persona for session {session_id}")
            
            # Perform persona classification
            classification_result = await self.classify_persona(session_id, profile_data, trip_details)
            
            # Store results
            self.context_store.set_persona(session_id, classification_result)
            self.context_store.set_trip_details(session_id, trip_details)
            
            # Trigger itinerary generation
            await self.event_bus.emit(EventTypes.ITINERARY_GENERATION_REQUESTED, {
                "persona_type": classification_result["persona_type"],
                "persona_tags": classification_result["persona_tags"],
                "trip_details": trip_details,
                "profile_data": profile_data,
                "propensity_to_pay": classification_result.get("propensity_to_pay", 0.5)
            }, session_id)
            
            # Generate UI actions for timeline display
            ui_actions = [
                UIAction(
                    type="itinerary_timeline",
                    payload={
                        "message": f"Perfect! Based on your preferences, I've classified you as a {classification_result['persona_type'].replace('_', ' ').title()}. Generating personalized itinerary variants...",
                        "persona_type": classification_result["persona_type"],
                        "confidence": classification_result["confidence"]
                    }
                ).dict()
            ]
            
            return PersonaClassificationResponse(
                persona_type=PersonaType(classification_result["persona_type"]),
                persona_tags=classification_result["persona_tags"],
                confidence=classification_result["confidence"],
                ui_actions=ui_actions
            )
            
        except Exception as e:
            logger.error(f"Persona classification error: {e}")
            return PersonaClassificationResponse(
                persona_type=PersonaType.BALANCED_TRAVELER,
                persona_tags=["general_traveler"],
                confidence=0.5,
                ui_actions=[]
            )

    async def classify_persona(self, session_id: str, profile_data: Dict[str, Any], trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """Classify traveler persona based on profile and trip data using LLM"""
        try:
            # Prepare comprehensive analysis context
            analysis_context = f"""
            Analyze this traveler profile and classify them into the most appropriate persona type.
            
            PROFILE DATA:
            - Vacation Style: {profile_data.get('vacation_style', 'unknown')}
            - Experience Type: {profile_data.get('experience_type', 'unknown')}
            - Attraction Preference: {profile_data.get('attraction_preference', 'unknown')}
            - Accommodation Preferences: {profile_data.get('accommodation', [])}
            - Interests: {profile_data.get('interests', [])}
            - Custom Preferences: {profile_data.get('custom_inputs', [])}
            
            TRIP DETAILS:
            - Destination: {trip_details.get('destination', 'unknown')}
            - Duration: {trip_details.get('start_date', '')} to {trip_details.get('end_date', '')}
            - Group Size: {trip_details.get('adults', 1)} adults, {trip_details.get('children', 0)} children
            - Budget per night: ₹{trip_details.get('budget_per_night', 0)}
            
            PERSONA TYPES TO CHOOSE FROM:
            1. adventurer - Seeks thrills, outdoor activities, extreme sports, off-beat destinations
            2. cultural_explorer - Interested in heritage, local traditions, museums, authentic experiences
            3. luxury_connoisseur - Prefers premium experiences, fine dining, luxury accommodations
            4. budget_backpacker - Cost-conscious, authentic local experiences, budget accommodations
            5. eco_conscious_traveler - Sustainable travel, eco-friendly options, nature conservation
            6. family_oriented - Kid-friendly activities, safe destinations, educational experiences
            7. business_traveler - Efficient travel, meeting facilities, good connectivity
            
            Based on the profile, classify this traveler and provide:
            - Primary persona type
            - Confidence score (0.0-1.0)
            - Supporting persona tags/traits
            - Propensity to pay score (0.0-1.0) for pricing strategy
            - Detailed reasoning for the classification
            
            Respond in JSON format:
            {{
                "persona_type": "adventurer|cultural_explorer|luxury_connoisseur|budget_backpacker|eco_conscious_traveler|family_oriented|business_traveler",
                "confidence": 0.85,
                "persona_tags": ["primary_persona", "secondary_trait1", "secondary_trait2"],
                "propensity_to_pay": 0.7,
                "reasoning": "Detailed explanation of why this classification was chosen"
            }}
            """
            
            user_msg = UserMessage(content=analysis_context)
            llm_client = self._get_llm_client(session_id)
            response = await llm_client.send_message(user_msg)
            
            # Parse LLM response
            import json
            try:
                llm_result = json.loads(response.content)
                
                # Validate and enhance the result
                persona_type = llm_result.get("persona_type", "cultural_explorer")
                confidence = max(0.1, min(1.0, float(llm_result.get("confidence", 0.5))))
                propensity_to_pay = max(0.1, min(1.0, float(llm_result.get("propensity_to_pay", 0.5))))
                
                # Add additional analysis
                rule_based_backup = await self._perform_rule_based_classification(profile_data, trip_details)
                
                # Combine LLM and rule-based insights
                final_classification = {
                    "persona_type": persona_type,
                    "persona_tags": llm_result.get("persona_tags", []) + rule_based_backup.get("persona_tags", []),
                    "confidence": confidence,
                    "propensity_to_pay": propensity_to_pay,
                    "reasoning": llm_result.get("reasoning", "LLM-based classification"),
                    "llm_analysis": llm_result,
                    "rule_based_backup": rule_based_backup
                }
                
                return final_classification
                
            except json.JSONDecodeError:
                logger.error("Failed to parse persona classification JSON, using rule-based fallback")
                return await self._perform_rule_based_classification(profile_data, trip_details)
            
        except Exception as e:
            logger.error(f"LLM persona classification error: {e}")
            return await self._perform_rule_based_classification(profile_data, trip_details)

    async def _perform_rule_based_classification(self, profile_data: Dict[str, Any], trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """Perform rule-based persona classification"""
        persona_scores = {
            PersonaType.ADVENTURER: 0,
            PersonaType.CULTURAL_EXPLORER: 0,
            PersonaType.LUXURY_CONNOISSEUR: 0,
            PersonaType.BUDGET_BACKPACKER: 0,
            PersonaType.ECO_CONSCIOUS: 0,
            PersonaType.FAMILY_ORIENTED: 0,
            PersonaType.BUSINESS_TRAVELER: 0
        }
        
        # Analyze vacation style
        vacation_style = profile_data.get('vacation_style', '')
        if vacation_style == 'adventurous':
            persona_scores[PersonaType.ADVENTURER] += 3
        elif vacation_style == 'relaxing':
            persona_scores[PersonaType.LUXURY_CONNOISSEUR] += 2
        elif vacation_style == 'balanced':
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 2
        
        # Analyze experience type
        experience_type = profile_data.get('experience_type', '')
        if experience_type == 'nature':
            persona_scores[PersonaType.ADVENTURER] += 2
            persona_scores[PersonaType.ECO_CONSCIOUS] += 2
        elif experience_type == 'culture':
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 3
        
        # Analyze attraction preference
        attraction_pref = profile_data.get('attraction_preference', '')
        if attraction_pref == 'local':
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 2
            persona_scores[PersonaType.BUDGET_BACKPACKER] += 1
        elif attraction_pref == 'popular':
            persona_scores[PersonaType.LUXURY_CONNOISSEUR] += 1
        
        # Analyze accommodation preferences
        accommodations = profile_data.get('accommodation', [])
        if 'luxury_hotels' in accommodations:
            persona_scores[PersonaType.LUXURY_CONNOISSEUR] += 3
        if 'budget_hotels' in accommodations or 'hostels' in accommodations:
            persona_scores[PersonaType.BUDGET_BACKPACKER] += 3
        if 'boutique_hotels' in accommodations or 'bnb' in accommodations:
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 2
        
        # Analyze interests
        interests = profile_data.get('interests', [])
        if 'hiking' in interests:
            persona_scores[PersonaType.ADVENTURER] += 2
            persona_scores[PersonaType.ECO_CONSCIOUS] += 1
        if 'museums' in interests:
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 2
        if 'nightlife' in interests:
            persona_scores[PersonaType.ADVENTURER] += 1
        if 'shopping' in interests:
            persona_scores[PersonaType.LUXURY_CONNOISSEUR] += 1
        if 'food' in interests:
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 1
        
        # Analyze budget
        budget_per_night = trip_details.get('budget_per_night', 0)
        if budget_per_night > 15000:
            persona_scores[PersonaType.LUXURY_CONNOISSEUR] += 3
        elif budget_per_night < 5000:
            persona_scores[PersonaType.BUDGET_BACKPACKER] += 3
        else:
            persona_scores[PersonaType.CULTURAL_EXPLORER] += 1
        
        # Analyze group composition
        children = trip_details.get('children', 0)
        if children > 0:
            persona_scores[PersonaType.FAMILY_ORIENTED] += 4
        
        # Determine primary persona
        primary_persona = max(persona_scores, key=persona_scores.get)
        confidence = min(persona_scores[primary_persona] / 10.0, 1.0)
        
        # Generate persona tags
        persona_tags = self._generate_persona_tags(persona_scores, primary_persona)
        
        # Calculate propensity to pay
        propensity_to_pay = self._calculate_propensity_to_pay(primary_persona, budget_per_night, accommodations)
        
        return {
            "persona_type": primary_persona.value,
            "persona_tags": persona_tags,
            "confidence": confidence,
            "persona_scores": {k.value: v for k, v in persona_scores.items()},
            "propensity_to_pay": propensity_to_pay,
            "reasoning": self._generate_reasoning(primary_persona, persona_scores, profile_data, trip_details)
        }

    def _combine_classifications(self, rule_based: Dict[str, Any], llm_response: str) -> Dict[str, Any]:
        """Combine rule-based and LLM classifications"""
        # For now, prioritize rule-based classification
        # In production, would implement more sophisticated fusion
        return rule_based

    def _generate_persona_tags(self, persona_scores: Dict[PersonaType, int], primary_persona: PersonaType) -> List[str]:
        """Generate persona tags based on scores"""
        tags = [primary_persona.value]
        
        # Add secondary traits
        sorted_personas = sorted(persona_scores.items(), key=lambda x: x[1], reverse=True)
        
        for persona, score in sorted_personas[1:3]:  # Top 2 secondary traits
            if score > 2:  # Significant score
                tags.append(f"secondary_{persona.value}")
        
        # Add specific behavioral tags
        if primary_persona == PersonaType.ADVENTURER:
            tags.extend(["thrill_seeker", "outdoor_enthusiast", "risk_tolerant"])
        elif primary_persona == PersonaType.CULTURAL_EXPLORER:
            tags.extend(["heritage_focused", "authentic_experiences", "local_culture"])
        elif primary_persona == PersonaType.LUXURY_CONNOISSEUR:
            tags.extend(["premium_experiences", "comfort_priority", "exclusive_access"])
        elif primary_persona == PersonaType.BUDGET_BACKPACKER:
            tags.extend(["cost_conscious", "local_experiences", "flexible_traveler"])
        elif primary_persona == PersonaType.ECO_CONSCIOUS:
            tags.extend(["sustainable_travel", "nature_conservation", "responsible_tourism"])
        elif primary_persona == PersonaType.FAMILY_ORIENTED:
            tags.extend(["kid_friendly", "safety_priority", "educational_focus"])
        
        return tags

    def _calculate_propensity_to_pay(self, persona: PersonaType, budget: float, accommodations: List[str]) -> float:
        """Calculate propensity to pay for pricing strategy"""
        base_propensity = 0.5
        
        # Persona-based adjustments
        if persona == PersonaType.LUXURY_CONNOISSEUR:
            base_propensity = 0.9
        elif persona == PersonaType.BUDGET_BACKPACKER:
            base_propensity = 0.2
        elif persona == PersonaType.ADVENTURER:
            base_propensity = 0.7
        elif persona == PersonaType.CULTURAL_EXPLORER:
            base_propensity = 0.6
        elif persona == PersonaType.FAMILY_ORIENTED:
            base_propensity = 0.5
        
        # Budget-based adjustments
        if budget > 15000:
            base_propensity += 0.2
        elif budget < 5000:
            base_propensity -= 0.2
        
        # Accommodation-based adjustments
        if 'luxury_hotels' in accommodations:
            base_propensity += 0.1
        elif 'hostels' in accommodations:
            base_propensity -= 0.1
        
        return min(max(base_propensity, 0.1), 1.0)

    def _generate_reasoning(self, primary_persona: PersonaType, persona_scores: Dict[PersonaType, int], 
                          profile_data: Dict[str, Any], trip_details: Dict[str, Any]) -> str:
        """Generate reasoning for classification"""
        reasoning_parts = []
        
        # Primary persona reasoning
        reasoning_parts.append(f"Classified as {primary_persona.value.replace('_', ' ').title()} based on:")
        
        # Key factors
        vacation_style = profile_data.get('vacation_style', '')
        if vacation_style:
            reasoning_parts.append(f"- Vacation style: {vacation_style}")
        
        budget = trip_details.get('budget_per_night', 0)
        if budget > 15000:
            reasoning_parts.append(f"- High budget preference (₹{budget}/night)")
        elif budget < 5000:
            reasoning_parts.append(f"- Budget-conscious approach (₹{budget}/night)")
        
        accommodations = profile_data.get('accommodation', [])
        if accommodations:
            reasoning_parts.append(f"- Accommodation preferences: {', '.join(accommodations)}")
        
        interests = profile_data.get('interests', [])
        if interests:
            reasoning_parts.append(f"- Key interests: {', '.join(interests)}")
        
        return " ".join(reasoning_parts)

    def _get_default_classification(self, profile_data: Dict[str, Any], trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """Get default classification when analysis fails"""
        return {
            "persona_type": PersonaType.CULTURAL_EXPLORER.value,
            "persona_tags": ["general_traveler", "balanced_preferences"],
            "confidence": 0.5,
            "propensity_to_pay": 0.5,
            "reasoning": "Default classification applied due to insufficient data"
        }