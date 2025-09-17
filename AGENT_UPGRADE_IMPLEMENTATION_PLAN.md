# Travello.ai Agent Upgrade Implementation Plan
## Transforming Current Agents to Match Enhanced PRD

---

## Current State Analysis

### Existing Agents Status
1. **ConversationManager** ✅ - Working, needs enhancement
2. **SlotAgent** ✅ - Working, needs persona integration  
3. **RetrievalAgent** ✅ - Working, needs service ranking
4. **PlannerAgent** ✅ - Working, needs 3-variant generation
5. **AccommodationAgent** ✅ - Working, needs integration into service ranking
6. **ValidatorAgent** ✅ - Working, minimal changes needed
7. **UXAgent** ❌ - Not implemented, needs creation

### Required New Agents
8. **ProfileAgent** ❌ - New: Persona classification & propensity assessment
9. **PersonaEngine** ❌ - New: Advanced persona matching
10. **ServiceRankingAgent** ❌ - New: Top-N selection with explainability
11. **CustomizationAgent** ❌ - New: Full editability & conflict resolution
12. **PersonalizationAgent** ❌ - New: Seasonality & sustainability
13. **DynamicPricingAgent** ❌ - New: Market-aware pricing
14. **ExternalBookingAgent** ❌ - New: Third-party integration
15. **ConfigurationAgent** ❌ - New: Business rules management

---

## Phase 1: Core Agent Enhancements (Immediate)

### 1.1 ConversationManager Enhancement

**Current Implementation**: Basic orchestration
**Required Enhancement**: Customer journey phases, persona-aware routing

```python
# File: /app/backend/agents/conversation_manager_v2.py

class ConversationManagerV2:
    """Enhanced conversation manager with customer journey phases"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Enhanced agent ecosystem
        self.profile_agent = ProfileAgent(llm_client)
        self.persona_engine = PersonaEngine()
        self.slot_agent = SlotAgent(llm_client)  # Enhanced
        self.service_ranking_agent = ServiceRankingAgent(llm_client)
        self.itinerary_generator = ItineraryGeneratorAgent(llm_client)
        self.customization_agent = CustomizationAgent(llm_client)
        self.dynamic_pricing_agent = DynamicPricingAgent(llm_client)
        
        # Customer journey state
        self.journey_phases = ["discover", "customize", "decide", "book"]
        
    async def process_message(self, message: str, session_context: dict) -> dict:
        """Enhanced message processing with journey phase awareness"""
        
        # Determine current journey phase
        current_phase = self._determine_journey_phase(session_context)
        
        if current_phase == "discover":
            return await self._handle_discover_phase(message, session_context)
        elif current_phase == "customize":
            return await self._handle_customize_phase(message, session_context)
        elif current_phase == "decide": 
            return await self._handle_decide_phase(message, session_context)
        elif current_phase == "book":
            return await self._handle_book_phase(message, session_context)
        else:
            # Fallback to existing logic
            return await self._handle_general_conversation(message, session_context)
    
    async def _handle_discover_phase(self, message: str, session_context: dict) -> dict:
        """Handle discovery phase with profile intake and persona classification"""
        
        # Check if we need profile intake
        if not session_context.get("traveler_profile"):
            return await self._initiate_profile_intake(message, session_context)
        
        # Check if persona is classified
        profile = session_context["traveler_profile"]
        if not profile.get("primary_persona"):
            return await self._complete_persona_classification(message, profile, session_context)
        
        # Generate initial itinerary variants
        if not session_context.get("itinerary_variants"):
            return await self._generate_itinerary_variants(message, profile, session_context)
        
        # Handle variant selection or questions
        return await self._handle_variant_discussion(message, session_context)
    
    async def _initiate_profile_intake(self, message: str, session_context: dict) -> dict:
        """Start the profile intake conversation"""
        
        # Extract destination if mentioned
        destination = await self.slot_agent.extract_destination(message)
        
        # Begin profile intake
        profile_result = await self.profile_agent.initiate_intake_conversation(
            message=message,
            destination=destination,
            session_id=session_context.get("session_id")
        )
        
        if profile_result["status"] == "intake_started":
            return {
                "chat_text": profile_result["next_question"],
                "ui_actions": [
                    {
                        "type": "profile_intake_card",
                        "payload": {
                            "stage": profile_result["current_stage"],
                            "progress": profile_result["progress"],
                            "question_type": profile_result["question_type"]
                        }
                    }
                ],
                "updated_slots": {
                    "journey_phase": "discover",
                    "profile_intake_stage": profile_result["current_stage"],
                    "destination": destination
                }
            }
        
        return profile_result
```

### 1.2 ProfileAgent Implementation

**New Agent**: Complete persona classification and propensity assessment

```python
# File: /app/backend/agents/profile_agent.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ProfileAgent:
    """Handles comprehensive traveler profiling and persona classification"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.persona_engine = PersonaEngine()
        
        # Profile intake stages
        self.intake_stages = [
            "destination_and_basics",
            "travel_style_assessment", 
            "budget_exploration",
            "preferences_deep_dive",
            "propensity_evaluation"
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
        
        # Generate contextual first question
        first_question = await self._generate_contextual_opening(message, destination)
        
        return {
            "status": "intake_started",
            "next_question": first_question,
            "current_stage": "destination_and_basics", 
            "progress": 0.2,
            "question_type": "travel_style",
            "profile": profile
        }
    
    async def _generate_contextual_opening(self, message: str, destination: str) -> str:
        """Generate personalized opening question based on context"""
        
        context = f"""
        User message: "{message}"
        Destination: {destination or "Not specified"}
        
        Generate a warm, conversational opening question that:
        1. Acknowledges their interest
        2. Begins understanding their travel style
        3. Feels natural and engaging
        4. Leads to persona classification
        
        Examples:
        - If destination mentioned: "Exciting! [Destination] is amazing for [key activities]. What draws you most to travel - the thrill of adventure, diving into local culture, or finding those perfect relaxing moments?"
        - If no destination: "I love helping plan amazing trips! What kind of experiences make you most excited when you travel - adventure activities, cultural discoveries, luxury relaxation, or something else entirely?"
        """
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await self.llm_client.send_message(user_message)
            
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"LLM question generation failed: {e}")
            # Fallback to context-aware default
            if destination:
                return f"Exciting! {destination} has so much to offer. What draws you most to travel - adventure activities, cultural experiences, luxury relaxation, or a mix of everything?"
            else:
                return "I'd love to help plan your perfect trip! What kind of experiences excite you most when you travel - adventure, culture, relaxation, or something else?"
    
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
    
    async def _complete_intake_and_classify(self, profile: dict) -> dict:
        """Complete intake process and perform persona classification"""
        
        # Extract structured data from responses
        structured_profile = await self._extract_structured_profile(profile["intake_responses"])
        
        # Classify persona
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
        
        return {
            "status": "intake_complete",
            "chat_text": await self._generate_completion_message(persona_result),
            "profile": complete_profile,
            "next_action": "generate_itinerary_variants"
        }
    
    async def _extract_structured_profile(self, responses: dict) -> dict:
        """Extract structured data from conversational responses using LLM"""
        
        context = f"""
        Extract structured travel profile data from these conversational responses:
        
        {json.dumps(responses, indent=2)}
        
        Return JSON with this structure:
        {{
            "travel_style": ["adventure", "culture", "relaxation", "luxury"],
            "budget_range": {{"min": 50000, "max": 150000, "currency": "INR", "flexibility": "medium"}},
            "pace_preference": "balanced",  // "slow", "balanced", "packed"
            "group_composition": {{"type": "couple", "adults": 2, "children": 0}},
            "accommodation_preference": ["boutique", "heritage", "luxury"],
            "activity_priorities": ["cultural_sites", "local_experiences", "adventure_sports"],
            "food_preferences": ["local_cuisine", "vegetarian"],
            "sustainability_importance": 0.7,  // 0.0-1.0
            "authenticity_preference": 0.8,   // 0.0-1.0
            "comfort_level": 0.6,             // 0.0-1.0
            "spontaneity_vs_planning": 0.4    // 0.0=highly planned, 1.0=very spontaneous
        }}
        """
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await self.llm_client.send_message(user_message)
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and parse JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Profile extraction failed: {e}")
            # Return fallback profile
            return self._generate_fallback_profile(responses)
    
    async def _assess_propensity_to_pay(self, profile: dict, persona_result: dict) -> dict:
        """Assess user's propensity to pay and spending patterns"""
        
        base_budget = profile.get("budget_range", {}).get("max", 100000)
        primary_persona = persona_result.get("primary_persona", "balanced_traveler")
        
        # Persona-based propensity multipliers
        persona_multipliers = {
            "luxury_connoisseur": {"upgrade": 0.9, "premium": 2.0, "discount_sensitivity": 0.2},
            "adventure_seeker": {"upgrade": 0.7, "premium": 1.2, "discount_sensitivity": 0.4},
            "cultural_explorer": {"upgrade": 0.8, "premium": 1.3, "discount_sensitivity": 0.3},
            "budget_backpacker": {"upgrade": 0.3, "premium": 0.6, "discount_sensitivity": 0.9},
            "eco_conscious_traveler": {"upgrade": 0.8, "premium": 1.4, "discount_sensitivity": 0.3}
        }
        
        multiplier = persona_multipliers.get(primary_persona, {"upgrade": 0.6, "premium": 1.0, "discount_sensitivity": 0.5})
        
        # Calculate spending thresholds
        propensity_assessment = {
            "base_budget": base_budget,
            "upgrade_willingness": multiplier["upgrade"],
            "premium_threshold": int(base_budget * multiplier["premium"]),
            "discount_sensitivity": multiplier["discount_sensitivity"],
            "spending_personality": primary_persona,
            "value_drivers": self._identify_value_drivers(profile, primary_persona)
        }
        
        return propensity_assessment
        
    def _identify_value_drivers(self, profile: dict, persona: str) -> List[str]:
        """Identify what drives spending decisions for this user"""
        drivers = []
        
        if persona == "luxury_connoisseur":
            drivers = ["premium_service", "exclusive_access", "comfort", "status"]
        elif persona == "adventure_seeker":
            drivers = ["unique_experiences", "safety_equipment", "expert_guides", "adrenaline_activities"]
        elif persona == "cultural_explorer":
            drivers = ["authenticity", "local_guides", "heritage_access", "cultural_immersion"]
        elif persona == "budget_backpacker":
            drivers = ["value_for_money", "essential_experiences", "cost_savings", "flexibility"]
        elif persona == "eco_conscious_traveler":
            drivers = ["sustainability", "local_community_support", "eco_certifications", "responsible_tourism"]
        
        # Add profile-specific drivers
        if profile.get("sustainability_importance", 0) > 0.7:
            drivers.append("environmental_impact")
        
        if profile.get("authenticity_preference", 0) > 0.7:
            drivers.append("authentic_experiences")
            
        return drivers
```

### 1.3 PersonaEngine Implementation

**New Agent**: Advanced persona classification with behavioral analysis

```python
# File: /app/backend/agents/persona_engine.py

import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class PersonaEngine:
    """Advanced persona classification engine with behavioral pattern recognition"""
    
    def __init__(self):
        self.persona_definitions = self._load_persona_definitions()
        self.classification_weights = {
            "activity_preference": 0.25,
            "budget_behavior": 0.20,
            "accommodation_style": 0.15,
            "pace_preference": 0.15,
            "value_priorities": 0.10,
            "social_preferences": 0.08,
            "sustainability_consciousness": 0.07
        }
    
    def _load_persona_definitions(self) -> Dict[str, Dict]:
        """Load comprehensive persona definitions with behavioral patterns"""
        return {
            "adventure_seeker": {
                "core_characteristics": {
                    "activity_preference": ["hiking", "rafting", "paragliding", "rock_climbing", "scuba_diving", "bungee_jumping"],
                    "accommodation_style": ["adventure_camps", "eco_lodges", "budget_hotels", "hostels"],
                    "budget_allocation": {"activities": 0.45, "accommodation": 0.25, "transport": 0.30},
                    "pace_preference": "packed",
                    "risk_tolerance": "high",
                    "planning_style": "flexible",
                    "social_preference": "group_activities"
                },
                "behavioral_indicators": {
                    "keywords": ["adventure", "thrill", "exciting", "adrenaline", "challenging", "extreme"],
                    "budget_behavior": "activity_focused_spending",
                    "decision_factors": ["uniqueness", "thrill_level", "safety_standards", "equipment_quality"],
                    "typical_concerns": ["weather_conditions", "safety_measures", "physical_requirements"]
                },
                "spending_patterns": {
                    "base_budget_multiplier": 1.0,
                    "activity_premium_tolerance": 1.5,
                    "accommodation_premium_tolerance": 0.8,
                    "upgrade_likelihood": 0.6,
                    "price_sensitivity": "medium"
                }
            },
            
            "cultural_explorer": {
                "core_characteristics": {
                    "activity_preference": ["museums", "heritage_sites", "local_tours", "cooking_classes", "art_galleries", "festivals"],
                    "accommodation_style": ["heritage_hotels", "boutique_stays", "homestays", "culturally_significant_properties"],
                    "budget_allocation": {"activities": 0.30, "accommodation": 0.35, "transport": 0.35},
                    "pace_preference": "balanced",
                    "authenticity_preference": "high",
                    "learning_orientation": "high",
                    "local_interaction": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["culture", "history", "authentic", "local", "traditional", "heritage", "learn"],
                    "budget_behavior": "experience_focused_spending",
                    "decision_factors": ["authenticity", "cultural_significance", "local_guides", "educational_value"],
                    "typical_concerns": ["cultural_sensitivity", "language_barriers", "local_customs"]
                },
                "spending_patterns": {
                    "base_budget_multiplier": 1.1,
                    "cultural_premium_tolerance": 1.3,
                    "local_experience_premium_tolerance": 1.4,
                    "upgrade_likelihood": 0.7,
                    "price_sensitivity": "low"
                }
            },
            
            "luxury_connoisseur": {
                "core_characteristics": {
                    "activity_preference": ["spa", "fine_dining", "private_tours", "exclusive_experiences", "wine_tasting", "golf"],
                    "accommodation_style": ["luxury_resorts", "5_star_hotels", "premium_villas", "boutique_luxury"],
                    "budget_allocation": {"activities": 0.20, "accommodation": 0.50, "transport": 0.30},
                    "pace_preference": "slow",
                    "service_expectation": "premium",
                    "privacy_preference": "high",
                    "comfort_priority": "maximum"
                },
                "behavioral_indicators": {
                    "keywords": ["luxury", "premium", "exclusive", "private", "high-end", "fine", "elegant"],
                    "budget_behavior": "quality_over_quantity",
                    "decision_factors": ["service_quality", "exclusivity", "comfort_level", "brand_reputation"],
                    "typical_concerns": ["service_standards", "privacy", "customization_options"]
                },
                "spending_patterns": {
                    "base_budget_multiplier": 2.0,
                    "luxury_premium_tolerance": 1.8,
                    "service_premium_tolerance": 1.6,
                    "upgrade_likelihood": 0.9,
                    "price_sensitivity": "very_low"
                }
            },
            
            "budget_backpacker": {
                "core_characteristics": {
                    "activity_preference": ["free_walking_tours", "street_food", "public_transport", "hostels", "local_markets"],
                    "accommodation_style": ["hostels", "budget_hotels", "shared_accommodations", "homestays"],
                    "budget_allocation": {"activities": 0.30, "accommodation": 0.20, "transport": 0.50},
                    "pace_preference": "flexible",
                    "value_priority": "high",
                    "social_preference": "backpacker_community",
                    "spontaneity": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["budget", "cheap", "affordable", "value", "backpack", "hostel", "local"],
                    "budget_behavior": "cost_minimization",
                    "decision_factors": ["price", "value_for_money", "flexibility", "social_opportunities"],
                    "typical_concerns": ["hidden_costs", "booking_flexibility", "safety_standards"]
                },
                "spending_patterns": {
                    "base_budget_multiplier": 0.6,
                    "value_premium_tolerance": 0.8,
                    "discount_sensitivity": 0.9,
                    "upgrade_likelihood": 0.2,
                    "price_sensitivity": "very_high"
                }
            },
            
            "eco_conscious_traveler": {
                "core_characteristics": {
                    "activity_preference": ["nature_walks", "wildlife_sanctuaries", "sustainable_tours", "organic_farms", "conservation_projects"],
                    "accommodation_style": ["eco_resorts", "sustainable_hotels", "green_certified", "locally_owned"],
                    "budget_allocation": {"activities": 0.35, "accommodation": 0.35, "transport": 0.30},
                    "carbon_consciousness": "high",
                    "local_support_priority": "high",
                    "environmental_impact_awareness": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["sustainable", "eco", "green", "responsible", "conservation", "local_community", "environment"],
                    "budget_behavior": "values_aligned_spending",
                    "decision_factors": ["environmental_impact", "local_community_benefit", "sustainability_certifications"],
                    "typical_concerns": ["carbon_footprint", "local_impact", "ethical_practices"]
                },
                "spending_patterns": {
                    "base_budget_multiplier": 1.2,
                    "sustainability_premium_tolerance": 1.4,
                    "local_premium_tolerance": 1.3,
                    "upgrade_likelihood": 0.8,
                    "price_sensitivity": "medium"
                }
            }
        }
    
    async def classify_persona(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced persona classification with multi-factor analysis"""
        
        persona_scores = {}
        
        for persona_name, persona_data in self.persona_definitions.items():
            score = await self._calculate_persona_score(profile, persona_data)
            persona_scores[persona_name] = score
        
        # Sort by score
        sorted_personas = sorted(persona_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate confidence and hybrid persona detection
        primary_score = sorted_personas[0][1]
        secondary_score = sorted_personas[1][1] if len(sorted_personas) > 1 else 0
        
        confidence = primary_score - secondary_score  # Higher gap = higher confidence
        
        result = {
            "primary_persona": sorted_personas[0][0],
            "primary_score": primary_score,
            "primary_confidence": min(1.0, confidence),
            "all_scores": persona_scores,
            "classification_timestamp": datetime.now().isoformat()
        }
        
        # Detect hybrid personas (when scores are close)
        if confidence < 0.15 and secondary_score > 0.6:
            result["secondary_persona"] = sorted_personas[1][0]
            result["secondary_score"] = secondary_score
            result["persona_type"] = "hybrid"
            result["hybrid_description"] = f"Primary {sorted_personas[0][0]} with strong {sorted_personas[1][0]} tendencies"
        else:
            result["persona_type"] = "primary"
        
        return result
    
    async def _calculate_persona_score(self, profile: Dict[str, Any], persona_data: Dict[str, Any]) -> float:
        """Calculate how well profile matches a specific persona"""
        
        total_score = 0.0
        core_chars = persona_data["core_characteristics"]
        behavioral_indicators = persona_data["behavioral_indicators"]
        
        # Activity preference matching
        activity_score = self._calculate_activity_match(
            profile.get("activity_priorities", []),
            core_chars["activity_preference"]
        )
        total_score += activity_score * self.classification_weights["activity_preference"]
        
        # Budget behavior analysis
        budget_score = self._calculate_budget_behavior_match(
            profile.get("budget_range", {}),
            behavioral_indicators["budget_behavior"],
            core_chars["budget_allocation"]
        )
        total_score += budget_score * self.classification_weights["budget_behavior"]
        
        # Accommodation style matching
        accommodation_score = self._calculate_accommodation_match(
            profile.get("accommodation_preference", []),
            core_chars["accommodation_style"]
        )
        total_score += accommodation_score * self.classification_weights["accommodation_style"]
        
        # Pace preference matching
        pace_score = 1.0 if profile.get("pace_preference") == core_chars.get("pace_preference") else 0.5
        total_score += pace_score * self.classification_weights["pace_preference"]
        
        # Value priorities alignment
        value_score = self._calculate_value_alignment(profile, behavioral_indicators["decision_factors"])
        total_score += value_score * self.classification_weights["value_priorities"]
        
        # Social preferences
        social_score = self._calculate_social_preference_match(profile, core_chars)
        total_score += social_score * self.classification_weights["social_preferences"]
        
        # Sustainability consciousness
        sustainability_score = self._calculate_sustainability_match(profile, core_chars)
        total_score += sustainability_score * self.classification_weights["sustainability_consciousness"]
        
        return min(1.0, total_score)  # Cap at 1.0
    
    def _calculate_activity_match(self, user_activities: List[str], persona_activities: List[str]) -> float:
        """Calculate activity preference alignment"""
        if not user_activities or not persona_activities:
            return 0.5  # Neutral score for missing data
        
        # Convert to sets for easier comparison
        user_set = set([activity.lower() for activity in user_activities])
        persona_set = set([activity.lower().replace('_', ' ') for activity in persona_activities])
        
        # Calculate overlap
        overlap = len(user_set.intersection(persona_set))
        union = len(user_set.union(persona_set))
        
        if union == 0:
            return 0.5
        
        # Jaccard similarity with boost for high overlap
        similarity = overlap / union
        if overlap >= 2:  # Boost for multiple matches
            similarity = min(1.0, similarity * 1.2)
        
        return similarity
    
    def _calculate_budget_behavior_match(self, budget_info: Dict, behavior_type: str, allocation: Dict) -> float:
        """Analyze budget behavior alignment"""
        score = 0.5  # Default neutral score
        
        budget_max = budget_info.get("max", 100000)
        budget_flexibility = budget_info.get("flexibility", "medium")
        
        # Budget behavior type matching
        behavior_scores = {
            "activity_focused_spending": 0.8 if budget_max > 80000 else 0.6,
            "experience_focused_spending": 0.7 if budget_flexibility == "high" else 0.5,
            "quality_over_quantity": 0.9 if budget_max > 150000 else 0.4,
            "cost_minimization": 0.9 if budget_max < 75000 else 0.3,
            "values_aligned_spending": 0.7 if budget_flexibility != "low" else 0.5
        }
        
        return behavior_scores.get(behavior_type, 0.5)
```

---

## Phase 2: Service Ranking and Recommendations

### 2.1 ServiceRankingAgent Implementation

**New Agent**: Intelligent service ranking with explainable recommendations

```python
# File: /app/backend/agents/service_ranking_agent.py

from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime, timezone

class ServiceRankingAgent:
    """Intelligent service ranking with multi-factor analysis and explainability"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Configurable ranking weights (can be adjusted via ConfigurationAgent)
        self.ranking_weights = {
            "persona_fit": 0.25,
            "price_value": 0.20,
            "location_convenience": 0.15,
            "user_ratings": 0.12,
            "sustainability_score": 0.10,
            "seasonality_fit": 0.08,
            "availability": 0.05,
            "uniqueness": 0.05
        }
        
        # Explanation templates
        self.explanation_templates = {
            "persona_fit": {
                "high": "Perfect match for {persona} travelers like you",
                "medium": "Good fit for your travel style",
                "low": "Different style but worth considering"
            },
            "price_value": {
                "excellent": "Exceptional value for money",
                "good": "Great value at this price point", 
                "premium": "Premium pricing for luxury experience",
                "budget": "Budget-friendly option"
            },
            "location": {
                "convenient": "Conveniently located near your other activities",
                "central": "Perfect central location",
                "remote": "Beautiful remote location for peaceful experience"
            }
        }
    
    async def get_top_services(self, 
                              destination: str, 
                              service_types: List[str],
                              profile: Dict[str, Any],
                              context: Dict[str, Any],
                              filters: Optional[Dict] = None,
                              top_n: int = 10) -> Dict[str, List[Dict]]:
        """Get top-N services for each type with explanations"""
        
        results = {}
        
        for service_type in service_types:
            print(f"🔍 Ranking {service_type} services for {destination}")
            
            # Get all available services
            all_services = await self._fetch_services(destination, service_type, filters)
            
            # Rank services
            ranked_services = await self._rank_services(all_services, profile, context, service_type)
            
            # Select top N and generate explanations
            top_services = []
            for service in ranked_services[:top_n]:
                explained_service = await self._add_explanations(service, profile, context)
                top_services.append(explained_service)
            
            results[service_type] = top_services
            print(f"✅ Ranked {len(top_services)} {service_type} services")
        
        return results
    
    async def _fetch_services(self, destination: str, service_type: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch available services from various sources"""
        
        services = []
        
        if service_type == "hotels":
            services.extend(await self._fetch_hotel_services(destination, filters))
        elif service_type == "activities":
            services.extend(await self._fetch_activity_services(destination, filters))
        elif service_type == "restaurants":
            services.extend(await self._fetch_restaurant_services(destination, filters))
        elif service_type == "transport":
            services.extend(await self._fetch_transport_services(destination, filters))
        
        return services
    
    async def _rank_services(self, services: List[Dict], profile: Dict, context: Dict, service_type: str) -> List[Dict]:
        """Rank services using multi-factor algorithm"""
        
        ranked_services = []
        
        for service in services:
            # Calculate individual factor scores
            scores = {}
            
            # Persona fit scoring
            scores["persona_fit"] = await self._calculate_persona_fit(service, profile, service_type)
            
            # Price-value analysis
            scores["price_value"] = self._calculate_price_value_score(service, profile)
            
            # Location convenience
            scores["location_convenience"] = self._calculate_location_score(service, context)
            
            # User ratings
            scores["user_ratings"] = self._normalize_rating_score(service.get("rating", 4.0))
            
            # Sustainability score
            scores["sustainability_score"] = self._calculate_sustainability_score(service, profile)
            
            # Seasonality fit
            scores["seasonality_fit"] = self._calculate_seasonality_score(service, context)
            
            # Availability score
            scores["availability"] = service.get("availability_score", 1.0)
            
            # Uniqueness score
            scores["uniqueness"] = self._calculate_uniqueness_score(service, service_type)
            
            # Calculate weighted final score
            final_score = sum(
                scores[factor] * weight 
                for factor, weight in self.ranking_weights.items()
            )
            
            service["ranking_score"] = final_score
            service["factor_scores"] = scores
            ranked_services.append(service)
        
        # Sort by final score
        ranked_services.sort(key=lambda x: x["ranking_score"], reverse=True)
        return ranked_services
    
    async def _calculate_persona_fit(self, service: Dict, profile: Dict, service_type: str) -> float:
        """Calculate how well service matches user's persona"""
        
        primary_persona = profile.get("persona_classification", {}).get("primary_persona", "balanced_traveler")
        
        # Service characteristics analysis
        service_characteristics = await self._analyze_service_characteristics(service, service_type)
        
        # Persona preference mapping
        persona_preferences = {
            "adventure_seeker": {
                "hotels": ["adventure_camps", "eco_lodges", "activity_focused"],
                "activities": ["outdoor", "thrill", "sports", "adventure"],
                "restaurants": ["local", "casual", "outdoor_dining"],
                "transport": ["adventure_vehicles", "scenic_routes"]
            },
            "cultural_explorer": {
                "hotels": ["heritage", "boutique", "culturally_significant"],
                "activities": ["cultural", "historical", "educational", "local_experiences"],
                "restaurants": ["traditional", "local_cuisine", "authentic"],
                "transport": ["cultural_tours", "local_transport"]
            },
            "luxury_connoisseur": {
                "hotels": ["luxury", "5_star", "premium", "exclusive"],
                "activities": ["private", "exclusive", "luxury", "premium"],
                "restaurants": ["fine_dining", "michelin", "upscale"],
                "transport": ["private", "luxury", "chauffeur"]
            },
            "budget_backpacker": {
                "hotels": ["hostel", "budget", "shared", "affordable"],
                "activities": ["free", "budget", "walking_tours", "public"],
                "restaurants": ["street_food", "local", "cheap_eats"],
                "transport": ["public", "budget", "shared"]
            },
            "eco_conscious_traveler": {
                "hotels": ["eco", "sustainable", "green_certified", "locally_owned"],
                "activities": ["nature", "conservation", "sustainable", "educational"],
                "restaurants": ["organic", "local", "sustainable", "farm_to_table"],
                "transport": ["eco_friendly", "electric", "low_carbon"]
            }
        }
        
        preferred_characteristics = persona_preferences.get(primary_persona, {}).get(service_type, [])
        
        # Calculate overlap between service characteristics and persona preferences
        overlap_score = 0.0
        for pref in preferred_characteristics:
            if any(pref.lower() in char.lower() for char in service_characteristics):
                overlap_score += 1.0
        
        # Normalize score
        if preferred_characteristics:
            return min(1.0, overlap_score / len(preferred_characteristics))
        else:
            return 0.5  # Neutral score for unknown persona
    
    async def _analyze_service_characteristics(self, service: Dict, service_type: str) -> List[str]:
        """Analyze service characteristics using LLM"""
        
        context = f"""
        Analyze this {service_type} service and extract key characteristics:
        
        Service: {json.dumps(service, indent=2)}
        
        Return a JSON list of characteristic keywords that describe this service.
        Focus on style, target market, experience type, and unique features.
        
        Examples:
        - Hotels: ["luxury", "boutique", "heritage", "eco_friendly", "business", "resort"]
        - Activities: ["adventure", "cultural", "educational", "outdoor", "family_friendly", "romantic"]
        - Restaurants: ["fine_dining", "casual", "local_cuisine", "international", "vegetarian"]
        """
        
        try:
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=10.0
            )
            
            content = response.content if hasattr(response, 'content') else str(response)
            content = content.strip()
            
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            characteristics = json.loads(content)
            return characteristics if isinstance(characteristics, list) else []
            
        except Exception as e:
            print(f"Service characteristic analysis failed: {e}")
            # Fallback to basic analysis
            return self._basic_characteristic_analysis(service, service_type)
    
    def _basic_characteristic_analysis(self, service: Dict, service_type: str) -> List[str]:
        """Fallback characteristic analysis"""
        characteristics = []
        
        name = service.get("name", "").lower()
        description = service.get("description", "").lower()
        tags = service.get("tags", [])
        
        # Add tags if available
        if tags:
            characteristics.extend(tags)
        
        # Basic keyword matching
        if service_type == "hotels":
            if any(word in name for word in ["luxury", "premium", "grand", "palace"]):
                characteristics.append("luxury")
            if any(word in name for word in ["heritage", "palace", "haveli"]):
                characteristics.append("heritage")
            if any(word in name for word in ["eco", "green", "sustainable"]):
                characteristics.append("eco_friendly")
        
        elif service_type == "activities":
            if any(word in description for word in ["adventure", "thrill", "exciting"]):
                characteristics.append("adventure")
            if any(word in description for word in ["culture", "heritage", "history"]):
                characteristics.append("cultural")
            if any(word in description for word in ["nature", "wildlife", "outdoor"]):
                characteristics.append("outdoor")
        
        return characteristics
    
    async def _add_explanations(self, service: Dict, profile: Dict, context: Dict) -> Dict:
        """Add explanations for why this service was recommended"""
        
        explanations = []
        factor_scores = service.get("factor_scores", {})
        
        # Persona fit explanation
        persona_score = factor_scores.get("persona_fit", 0)
        if persona_score > 0.7:
            explanations.append(self.explanation_templates["persona_fit"]["high"].format(
                persona=profile.get("persona_classification", {}).get("primary_persona", "your travel style")
            ))
        elif persona_score > 0.5:
            explanations.append(self.explanation_templates["persona_fit"]["medium"])
        
        # Price-value explanation
        price_score = factor_scores.get("price_value", 0)
        if price_score > 0.8:
            explanations.append(self.explanation_templates["price_value"]["excellent"])
        elif price_score > 0.6:
            explanations.append(self.explanation_templates["price_value"]["good"])
        elif price_score < 0.4:
            explanations.append(self.explanation_templates["price_value"]["premium"])
        
        # Location explanation
        location_score = factor_scores.get("location_convenience", 0)
        if location_score > 0.8:
            explanations.append(self.explanation_templates["location"]["convenient"])
        
        # Sustainability explanation
        if profile.get("structured_data", {}).get("sustainability_importance", 0) > 0.6:
            sustainability_score = factor_scores.get("sustainability_score", 0)
            if sustainability_score > 0.7:
                explanations.append("Eco-certified with strong sustainability practices")
        
        service["explanations"] = explanations
        service["why_recommended"] = self._generate_primary_recommendation_reason(service, explanations)
        
        return service
    
    def _generate_primary_recommendation_reason(self, service: Dict, explanations: List[str]) -> str:
        """Generate primary reason for recommendation"""
        
        ranking_score = service.get("ranking_score", 0)
        
        if ranking_score > 0.8:
            primary = "Highly recommended"
        elif ranking_score > 0.6:
            primary = "Great choice"
        elif ranking_score > 0.4:
            primary = "Good option"
        else:
            primary = "Worth considering"
        
        if explanations:
            return f"{primary}: {explanations[0]}"
        else:
            return f"{primary} for your trip"
```

This implementation plan provides a comprehensive upgrade path for transforming the current Travello.ai system into the sophisticated AI travel concierge described in the enhanced PRD. Each phase builds upon the previous one, ensuring a smooth transition while adding powerful new capabilities.

Would you like me to continue with the implementation details for the remaining agents (CustomizationAgent, DynamicPricingAgent, etc.) or would you prefer to focus on a specific aspect of this upgrade plan?