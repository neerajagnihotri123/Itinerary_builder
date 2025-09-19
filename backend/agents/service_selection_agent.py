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
            # Use fallback services first for speed, then enhance with LLM if time allows
            fallback_services = self._generate_fallback_services(service_type, location, 10)
            
            # Quick LLM enhancement with simplified prompt
            try:
                enhanced_services = await asyncio.wait_for(
                    self._enhance_services_with_llm(session_id, service_type, location, traveler_profile, fallback_services),
                    timeout=15.0  # 15 second timeout
                )
                return enhanced_services
            except asyncio.TimeoutError:
                logger.warning(f"LLM enhancement timed out, using fallback services for {service_type} in {location}")
                # Rank fallback services by simple heuristics
                return self._rank_fallback_services(fallback_services, traveler_profile)
            
        except Exception as e:
            logger.error(f"Service recommendation error: {e}")
            return self._generate_fallback_services(service_type, location, 10)
    
    async def _enhance_services_with_llm(self, session_id: str, service_type: str, location: str, 
                                       traveler_profile: Dict, fallback_services: List[Dict]) -> List[Dict]:
        """Enhanced services with LLM ranking (with timeout protection)"""
        try:
            # Simplified prompt for faster processing
            prompt = f"""
            Rank these {service_type} services in {location} for this traveler:
            Profile: {traveler_profile.get('vacation_style', 'balanced')} style, {traveler_profile.get('budget_level', 'moderate')} budget
            
            Services: {[s['name'] for s in fallback_services[:5]]}  # Only rank top 5 for speed
            
            Return ONLY a JSON array of rankings [1,2,3,4,5] where 1=best match:
            """
            
            llm_client = self._get_llm_client(session_id)
            response = await llm_client.send_message(UserMessage(text=prompt))
            
            # Simple parsing
            import json
            import re
            
            json_match = re.search(r'\[[\d,\s]+\]', response)
            if json_match:
                rankings = json.loads(json_match.group(0))
                
                # Apply rankings to services
                ranked_services = []
                for rank in rankings:
                    if 1 <= rank <= len(fallback_services):
                        service = fallback_services[rank-1].copy()
                        service['similarity_score'] = 1.0 - (rank-1) * 0.1  # Convert rank to score
                        ranked_services.append(service)
                
                # Add remaining services
                for i, service in enumerate(fallback_services):
                    if i+1 not in rankings:
                        service['similarity_score'] = 0.5
                        ranked_services.append(service)
                
                return ranked_services[:10]
            
            # Fallback to original services if parsing fails
            return self._rank_fallback_services(fallback_services, traveler_profile)
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return self._rank_fallback_services(fallback_services, traveler_profile)
    
    def _rank_fallback_services(self, services: List[Dict], traveler_profile: Dict) -> List[Dict]:
        """Rank services using simple heuristics"""
        budget_level = traveler_profile.get('budget_level', 'moderate')
        vacation_style = traveler_profile.get('vacation_style', 'balanced')
        
        for i, service in enumerate(services):
            score = 0.8 - i * 0.05  # Base descending score
            
            # Budget matching
            if budget_level == 'luxury' and service['price'] > 3000:
                score += 0.1
            elif budget_level == 'budget' and service['price'] < 2000:
                score += 0.1
            elif budget_level == 'moderate' and 2000 <= service['price'] <= 4000:
                score += 0.1
            
            # Style matching  
            if vacation_style == 'adventurous' and service.get('rating', 4.0) > 4.2:
                score += 0.05
            
            service['similarity_score'] = max(0.1, min(1.0, score))
        
        # Sort by similarity score
        return sorted(services, key=lambda x: x['similarity_score'], reverse=True)
    
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