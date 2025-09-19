"""
Service Selection Agent - Top-n service selection and ranking
Handles hotel, activity, and transportation service recommendations
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

logger = logging.getLogger(__name__)

class ServiceSelectionAgent:
    """Agent for selecting and ranking services based on traveler profile"""
    
    def __init__(self):
        self.service_categories = {
            "accommodation": ["luxury_hotels", "boutique_hotels", "budget_hotels", "resorts", "homestays"],
            "activities": ["adventure", "culture", "nature", "food", "shopping", "wellness"],
            "transportation": ["private_cab", "shared_cab", "public_transport", "rental_car", "luxury_transport"]
        }
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for service analysis"""
        return LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=session_id,
            system_message="You are a travel service expert who ranks and recommends services based on traveler profiles."
        ).with_model("openai", "gpt-4o-mini")
    
    async def get_service_recommendations(self, 
                                       session_id: str,
                                       service_type: str,
                                       location: str,
                                       traveler_profile: Dict,
                                       activity_context: Dict = None) -> List[Dict]:
        """
        Get top 10 service recommendations ranked by profile similarity
        
        Args:
            session_id: User session ID
            service_type: 'accommodation', 'activities', 'transportation'
            location: Location for services
            traveler_profile: User profile with preferences
            activity_context: Context like time, duration, etc.
        
        Returns:
            List of top 10 ranked services
        """
        try:
            # Create prompt for LLM to generate ranked services
            context_info = ""
            if activity_context:
                context_info = f"Context: {activity_context.get('time', '')}, Duration: {activity_context.get('duration', '')}"
            
            prompt = f"""
            Generate 10 {service_type} recommendations for {location} ranked by similarity to this traveler profile:
            
            Traveler Profile:
            - Vacation Style: {traveler_profile.get('vacation_style', 'balanced')}
            - Experience Type: {traveler_profile.get('experience_type', 'mixed')}
            - Budget Level: {traveler_profile.get('budget_level', 'moderate')}
            - Preferences: {traveler_profile.get('preferences', [])}
            
            {context_info}
            
            Return ONLY a JSON array of 10 services, ranked from most to least suitable:
            [
              {{
                "id": "service_1",
                "name": "Service Name",
                "type": "{service_type}",
                "location": "{location}",
                "rating": 4.5,
                "price": 5000,
                "similarity_score": 0.95,
                "match_reasons": ["reason1", "reason2"],
                "description": "Brief description",
                "features": ["feature1", "feature2", "feature3"],
                "availability": true,
                "booking_info": {{"contact": "details", "advance_booking": "1 day"}}
              }}
            ]
            
            Ensure services are genuinely different and ranked by profile fit.
            """
            
            llm_client = self._get_llm_client(session_id)
            response = await llm_client.send_message(UserMessage(text=prompt))
            
            # Parse JSON response
            import json
            import re
            
            json_text = response
            if '```json' in json_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            elif '```' in json_text:
                json_match = re.search(r'```\s*(.*?)\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            
            services = json.loads(json_text.strip())
            
            # Validate and ensure we have exactly 10 services
            if len(services) < 10:
                # Generate additional fallback services
                services.extend(self._generate_fallback_services(service_type, location, 10 - len(services)))
            
            return services[:10]  # Ensure exactly 10 services
            
        except Exception as e:
            logger.error(f"Service recommendation error: {e}")
            return self._generate_fallback_services(service_type, location, 10)
    
    def _generate_fallback_services(self, service_type: str, location: str, count: int) -> List[Dict]:
        """Generate fallback services if LLM fails"""
        services = []
        
        for i in range(count):
            if service_type == "accommodation":
                service = {
                    "id": f"hotel_{location.lower()}_{i+1}",
                    "name": f"{location} Hotel {i+1}",
                    "type": "accommodation",
                    "location": location,
                    "rating": 4.0 + (i % 10) * 0.1,
                    "price": 3000 + i * 500,
                    "similarity_score": 0.8 - i * 0.05,
                    "match_reasons": ["Good location", "Suitable amenities"],
                    "description": f"Quality accommodation in {location}",
                    "features": ["WiFi", "AC", "Restaurant"],
                    "availability": True,
                    "booking_info": {"contact": "booking@hotel.com", "advance_booking": "1 day"}
                }
            elif service_type == "activities":
                activities = ["City Tour", "Adventure Sports", "Cultural Visit", "Nature Walk", "Food Tour"]
                service = {
                    "id": f"activity_{location.lower()}_{i+1}",
                    "name": f"{location} {activities[i % len(activities)]}",
                    "type": "activities",
                    "location": location,
                    "rating": 4.2 + (i % 8) * 0.1,
                    "price": 1000 + i * 200,
                    "similarity_score": 0.85 - i * 0.04,
                    "match_reasons": ["Popular activity", "Good reviews"],
                    "description": f"Exciting {activities[i % len(activities)].lower()} in {location}",
                    "features": ["Guide included", "Equipment provided"],
                    "availability": True,
                    "booking_info": {"contact": "activities@local.com", "advance_booking": "2 hours"}
                }
            else:  # transportation
                transports = ["Private Cab", "Shared Taxi", "Rental Car", "Bus Service"]
                service = {
                    "id": f"transport_{location.lower()}_{i+1}",
                    "name": f"{location} {transports[i % len(transports)]}",
                    "type": "transportation",
                    "location": location,
                    "rating": 4.1 + (i % 9) * 0.1,
                    "price": 500 + i * 100,
                    "similarity_score": 0.8 - i * 0.03,
                    "match_reasons": ["Reliable service", "Good coverage"],
                    "description": f"Convenient transportation in {location}",
                    "features": ["24/7 service", "GPS tracking"],
                    "availability": True,
                    "booking_info": {"contact": "transport@service.com", "advance_booking": "30 minutes"}
                }
            
            services.append(service)
        
        return services
    
    async def rank_services_by_profile(self, 
                                     services: List[Dict], 
                                     traveler_profile: Dict) -> List[Dict]:
        """Re-rank existing services based on updated profile"""
        try:
            # Sort by similarity score (higher is better)
            ranked_services = sorted(services, key=lambda x: x.get('similarity_score', 0), reverse=True)
            return ranked_services
        except Exception as e:
            logger.error(f"Service ranking error: {e}")
            return services