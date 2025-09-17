"""
PersonaEngine - Advanced persona classification with behavioral pattern recognition
Implements the 5 travel personas from PRD: adventure_seeker, cultural_explorer, luxury_connoisseur, budget_backpacker, eco_conscious_traveler
"""

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
        """Load comprehensive persona definitions with behavioral patterns from PRD"""
        return {
            "adventure_seeker": {
                "core_characteristics": {
                    "activity_preference": ["hiking", "rafting", "paragliding", "rock_climbing", "scuba_diving", "bungee_jumping", "trekking", "outdoor_sports"],
                    "accommodation_style": ["adventure_camps", "eco_lodges", "budget_hotels", "hostels", "mountain_lodges"],
                    "budget_allocation": {"activities": 0.45, "accommodation": 0.25, "transport": 0.30},
                    "pace_preference": "packed",
                    "risk_tolerance": "high",
                    "planning_style": "flexible",
                    "social_preference": "group_activities"
                },
                "behavioral_indicators": {
                    "keywords": ["adventure", "thrill", "exciting", "adrenaline", "challenging", "extreme", "active", "outdoor"],
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
                    "activity_preference": ["museums", "heritage_sites", "local_tours", "cooking_classes", "art_galleries", "festivals", "cultural_workshops", "historical_walks"],
                    "accommodation_style": ["heritage_hotels", "boutique_stays", "homestays", "culturally_significant_properties"],
                    "budget_allocation": {"activities": 0.30, "accommodation": 0.35, "transport": 0.35},
                    "pace_preference": "balanced",
                    "authenticity_preference": "high",
                    "learning_orientation": "high",
                    "local_interaction": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["culture", "history", "authentic", "local", "traditional", "heritage", "learn", "explore"],
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
                    "activity_preference": ["spa", "fine_dining", "private_tours", "exclusive_experiences", "wine_tasting", "golf", "yacht_charters", "premium_shopping"],
                    "accommodation_style": ["luxury_resorts", "5_star_hotels", "premium_villas", "boutique_luxury"],
                    "budget_allocation": {"activities": 0.20, "accommodation": 0.50, "transport": 0.30},
                    "pace_preference": "slow",
                    "service_expectation": "premium",
                    "privacy_preference": "high",
                    "comfort_priority": "maximum"
                },
                "behavioral_indicators": {
                    "keywords": ["luxury", "premium", "exclusive", "private", "high-end", "fine", "elegant", "sophisticated"],
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
                    "activity_preference": ["free_walking_tours", "street_food", "public_transport", "hostels", "local_markets", "hiking", "free_attractions"],
                    "accommodation_style": ["hostels", "budget_hotels", "shared_accommodations", "homestays"],
                    "budget_allocation": {"activities": 0.30, "accommodation": 0.20, "transport": 0.50},
                    "pace_preference": "flexible",
                    "value_priority": "high",
                    "social_preference": "backpacker_community",
                    "spontaneity": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["budget", "cheap", "affordable", "value", "backpack", "hostel", "local", "authentic"],
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
                    "activity_preference": ["nature_walks", "wildlife_sanctuaries", "sustainable_tours", "organic_farms", "conservation_projects", "eco_tours", "responsible_tourism"],
                    "accommodation_style": ["eco_resorts", "sustainable_hotels", "green_certified", "locally_owned"],
                    "budget_allocation": {"activities": 0.35, "accommodation": 0.35, "transport": 0.30},
                    "carbon_consciousness": "high",
                    "local_support_priority": "high",
                    "environmental_impact_awareness": "high"
                },
                "behavioral_indicators": {
                    "keywords": ["sustainable", "eco", "green", "responsible", "conservation", "local_community", "environment", "carbon"],
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
            "primary_confidence": min(1.0, confidence + 0.5),  # Boost confidence for better UX
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
        
        # Activity preference matching (25% weight)
        activity_score = self._calculate_activity_match(
            profile.get("activity_priorities", []) + profile.get("travel_style", []),
            core_chars["activity_preference"]
        )
        total_score += activity_score * self.classification_weights["activity_preference"]
        
        # Budget behavior analysis (20% weight)
        budget_score = self._calculate_budget_behavior_match(
            profile.get("budget_range", {}),
            behavioral_indicators["budget_behavior"],
            core_chars["budget_allocation"]
        )
        total_score += budget_score * self.classification_weights["budget_behavior"]
        
        # Accommodation style matching (15% weight)
        accommodation_score = self._calculate_accommodation_match(
            profile.get("accommodation_preference", []),
            core_chars["accommodation_style"]
        )
        total_score += accommodation_score * self.classification_weights["accommodation_style"]
        
        # Pace preference matching (15% weight)
        pace_score = 1.0 if profile.get("pace_preference") == core_chars.get("pace_preference") else 0.5
        total_score += pace_score * self.classification_weights["pace_preference"]
        
        # Value priorities alignment (10% weight)
        value_score = self._calculate_value_alignment(profile, behavioral_indicators["decision_factors"])
        total_score += value_score * self.classification_weights["value_priorities"]
        
        # Social preferences (8% weight)
        social_score = self._calculate_social_preference_match(profile, core_chars)
        total_score += social_score * self.classification_weights["social_preferences"]
        
        # Sustainability consciousness (7% weight)
        sustainability_score = self._calculate_sustainability_match(profile, core_chars)
        total_score += sustainability_score * self.classification_weights["sustainability_consciousness"]
        
        return min(1.0, total_score)  # Cap at 1.0
    
    def _calculate_activity_match(self, user_activities: List[str], persona_activities: List[str]) -> float:
        """Calculate activity preference alignment"""
        if not user_activities or not persona_activities:
            return 0.5  # Neutral score for missing data
        
        # Convert to sets for easier comparison
        user_set = set([activity.lower().replace('_', ' ') for activity in user_activities])
        persona_set = set([activity.lower().replace('_', ' ') for activity in persona_activities])
        
        # Calculate overlap
        overlap = len(user_set.intersection(persona_set))
        union = len(user_set.union(persona_set))
        
        if union == 0:
            return 0.5
        
        # Jaccard similarity with boost for high overlap
        similarity = overlap / union
        if overlap >= 2:  # Boost for multiple matches
            similarity = min(1.0, similarity * 1.3)
        
        return similarity
    
    def _calculate_budget_behavior_match(self, budget_info: Dict, behavior_type: str, allocation: Dict) -> float:
        """Analyze budget behavior alignment"""
        score = 0.5  # Default neutral score
        
        budget_max = budget_info.get("max", 100000)
        budget_flexibility = budget_info.get("flexibility", "medium")
        
        # Budget behavior type matching based on spending patterns
        behavior_scores = {
            "activity_focused_spending": 0.8 if budget_max > 80000 else 0.6,
            "experience_focused_spending": 0.7 if budget_flexibility in ["high", "medium"] else 0.5,
            "quality_over_quantity": 0.9 if budget_max > 150000 else 0.4,
            "cost_minimization": 0.9 if budget_max < 75000 else 0.3,
            "values_aligned_spending": 0.7 if budget_flexibility != "low" else 0.5
        }
        
        return behavior_scores.get(behavior_type, 0.5)
    
    def _calculate_accommodation_match(self, user_prefs: List[str], persona_styles: List[str]) -> float:
        """Calculate accommodation style alignment"""
        if not user_prefs or not persona_styles:
            return 0.5
        
        user_set = set([pref.lower().replace('_', ' ') for pref in user_prefs])
        persona_set = set([style.lower().replace('_', ' ') for style in persona_styles])
        
        overlap = len(user_set.intersection(persona_set))
        if overlap > 0:
            return min(1.0, overlap / len(persona_set) + 0.3)  # Boost for any match
        
        return 0.3  # Low score for no match
    
    def _calculate_value_alignment(self, profile: Dict, decision_factors: List[str]) -> float:
        """Calculate alignment with persona decision factors"""
        
        # Extract value indicators from profile
        user_values = []
        
        if profile.get("authenticity_preference", 0) > 0.7:
            user_values.extend(["authenticity", "local", "traditional"])
        
        if profile.get("sustainability_importance", 0) > 0.6:
            user_values.extend(["sustainability", "environment", "responsible"])
        
        if profile.get("comfort_level", 0) > 0.8:
            user_values.extend(["comfort", "luxury", "service"])
        
        budget_max = profile.get("budget_range", {}).get("max", 100000)
        if budget_max < 75000:
            user_values.extend(["value", "budget", "affordable"])
        elif budget_max > 150000:
            user_values.extend(["premium", "exclusive", "high-end"])
        
        # Calculate alignment with persona decision factors
        if not user_values or not decision_factors:
            return 0.5
        
        matches = 0
        for factor in decision_factors:
            if any(value in factor.lower() for value in user_values):
                matches += 1
        
        return min(1.0, matches / len(decision_factors) + 0.2)  # Boost base score
    
    def _calculate_social_preference_match(self, profile: Dict, core_chars: Dict) -> float:
        """Calculate social preference alignment"""
        
        group_type = profile.get("group_composition", {}).get("type", "couple")
        social_pref = core_chars.get("social_preference", "mixed")
        
        # Social preference scoring
        social_scores = {
            ("solo", "backpacker_community"): 0.9,
            ("couple", "group_activities"): 0.7,
            ("family", "group_activities"): 0.8,
            ("friends", "group_activities"): 0.9,
            ("couple", "mixed"): 0.6
        }
        
        return social_scores.get((group_type, social_pref), 0.5)
    
    def _calculate_sustainability_match(self, profile: Dict, core_chars: Dict) -> float:
        """Calculate sustainability consciousness alignment"""
        
        user_sustainability = profile.get("sustainability_importance", 0.5)
        persona_consciousness = core_chars.get("carbon_consciousness", "medium")
        
        # Convert persona consciousness to score
        consciousness_scores = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        }
        
        persona_score = consciousness_scores.get(persona_consciousness, 0.5)
        
        # Calculate alignment
        if user_sustainability > 0.7 and persona_score > 0.8:
            return 1.0  # Perfect alignment
        elif user_sustainability < 0.3 and persona_score < 0.4:
            return 0.8  # Good alignment for low sustainability
        elif abs(user_sustainability - persona_score) < 0.3:
            return 0.7  # Close alignment
        else:
            return 0.4  # Poor alignment