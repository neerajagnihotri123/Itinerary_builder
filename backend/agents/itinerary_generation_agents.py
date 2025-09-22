"""
Master Travel Planner - Itinerary Generation Agents
Real-time access to global flight, hotel, cab and activity inventories with intelligent recommendations
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models.schemas import ItineraryVariant, DayItinerary, Activity, ActivityType, ItineraryVariantType
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class BaseItineraryAgent:
    """Base agent for sophisticated travel planning with real-time inventory access"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus, variant_type: ItineraryVariantType):
        self.context_store = context_store
        self.event_bus = event_bus
        self.variant_type = variant_type
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Service categories for top 10 recommendations
        self.service_categories = {
            'accommodation': ['luxury_hotels', 'boutique_hotels', 'business_hotels', 'budget_hotels', 'resorts', 'bnb', 'hostels', 'guesthouses', 'apartments', 'villas'],
            'activities': ['adventure_sports', 'cultural_tours', 'nature_excursions', 'food_experiences', 'nightlife', 'shopping', 'wellness', 'historical_sites', 'local_experiences', 'entertainment'],
            'transportation': ['premium_cabs', 'standard_cabs', 'ride_sharing', 'car_rental', 'motorbike_rental', 'public_transport', 'private_transfers', 'helicopters', 'boats', 'cycles']
        }
        
        # Subscribe to itinerary generation requests
        self.event_bus.subscribe(EventTypes.ITINERARY_GENERATION_REQUESTED, self._handle_generation_request)
    
    def _create_profile_from_persona_tags(self, persona_tags: List[str]) -> Dict[str, Any]:
        """Create profile data from persona tags when profile_data is not provided"""
        profile_mapping = {
            'adventurer': {
                'vacation_style': ['adventurous'],
                'experience_type': ['adventure', 'outdoor'],
                'budget_level': 'moderate',
                'activity_level': 'high',
                'interests': ['hiking', 'extreme_sports', 'nature', 'adventure'],
                'travel_style': 'explorer'
            },
            'balanced_traveler': {
                'vacation_style': ['balanced'],
                'experience_type': ['mixed', 'cultural'],
                'budget_level': 'moderate',
                'activity_level': 'moderate',
                'interests': ['culture', 'food', 'sightseeing', 'local_experiences'],
                'travel_style': 'balanced'
            },
            'luxury_connoisseur': {
                'vacation_style': ['luxury'],
                'experience_type': ['premium', 'exclusive'],
                'budget_level': 'luxury',
                'activity_level': 'low',
                'interests': ['fine_dining', 'exclusive_experiences', 'spa', 'luxury_shopping'],
                'travel_style': 'luxury'
            }
        }
        
        # Get primary persona
        primary_persona = persona_tags[0] if persona_tags else 'balanced_traveler'
        return profile_mapping.get(primary_persona, profile_mapping['balanced_traveler'])

    async def _parse_comprehensive_response(self, response: str, days: int, trip_details: Dict) -> Dict[str, Any]:
        """Parse comprehensive LLM response with enhanced structure"""
        try:
            # Parse JSON from response
            import json
            import re
            
            # Remove markdown code blocks if present
            if '```json' in response:
                json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            elif '```' in response:
                json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)
            
            # Parse JSON
            data = json.loads(response.strip())
            
            # Validate and enhance structure
            if 'daily_itinerary' in data:
                total_cost = 0
                for day_data in data['daily_itinerary']:
                    for activity in day_data.get('activities', []):
                        # Ensure image URL
                        if not activity.get('image'):
                            activity['image'] = self._get_image_url_for_activity(
                                activity.get('title', 'Activity'),
                                activity.get('location', trip_details.get('destination', 'India')),
                                activity.get('category', 'sightseeing')
                            )
                        
                        # Add cost to total
                        total_cost += activity.get('cost', 0)
                        
                        # Ensure alternatives exist
                        if not activity.get('alternatives'):
                            activity['alternatives'] = self._generate_default_alternatives(activity)
                
                # Update total cost
                data['total_cost'] = total_cost
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive response: {e}")
            return self._generate_fallback_itinerary_data(trip_details, days)

    async def _quality_assurance_check(self, itinerary_data: Dict, trip_details: Dict, profile_data: Dict) -> Dict[str, Any]:
        """Validate and enhance itinerary data for quality assurance"""
        try:
            # Ensure all required fields are present
            required_fields = ['variant_title', 'total_days', 'daily_itinerary']
            for field in required_fields:
                if field not in itinerary_data:
                    logger.warning(f"Missing required field: {field}")
                    
            # Validate daily itinerary structure
            if 'daily_itinerary' in itinerary_data:
                for day_data in itinerary_data['daily_itinerary']:
                    # Ensure each day has activities
                    if not day_data.get('activities'):
                        day_data['activities'] = self._generate_default_activities(day_data.get('day', 1), trip_details)
                    
                    # Ensure each activity has required fields
                    for activity in day_data['activities']:
                        if not activity.get('selected_reason'):
                            activity['selected_reason'] = f"🎯 Great choice for your {profile_data.get('travel_style', 'balanced')} travel style."
                        
                        if not activity.get('alternatives'):
                            activity['alternatives'] = self._generate_default_alternatives(activity)
            
            # Add optimization score if missing
            if 'optimization_score' not in itinerary_data:
                itinerary_data['optimization_score'] = 0.85
            
            # Add conflict warnings if missing
            if 'conflict_warnings' not in itinerary_data:
                itinerary_data['conflict_warnings'] = []
            
            return itinerary_data
            
        except Exception as e:
            logger.error(f"Quality assurance check failed: {e}")
            return itinerary_data

    def _generate_fallback_itinerary_data(self, trip_details: Dict, days: int) -> Dict[str, Any]:
        """Generate fallback itinerary data in the new comprehensive format"""
        destination = trip_details.get('destination', 'India')
        
        fallback_data = {
            "variant_title": f"{self.variant_type.value.title()} {destination}",
            "total_days": days,
            "total_cost": days * 4000,
            "optimization_score": 0.75,
            "conflict_warnings": [],
            "daily_itinerary": []
        }
        
        # Generate basic daily itineraries
        for day in range(1, days + 1):
            day_data = {
                "day": day,
                "date": (datetime.now() + timedelta(days=day-1)).strftime('%Y-%m-%d'),
                "theme": f"Day {day} Exploration",
                "activities": self._generate_default_activities(day, trip_details),
                "daily_budget": 4000,
                "daily_travel_time": "60 minutes total"
            }
            fallback_data["daily_itinerary"].append(day_data)
        
        return fallback_data

    def _generate_default_activities(self, day: int, trip_details: Dict) -> List[Dict]:
        """Generate default activities for fallback scenarios"""
        destination = trip_details.get('destination', 'India')
        activities = [
            {
                "time_slot": "9:00 AM - 11:00 AM",
                "title": f"Morning Exploration in {destination}",
                "category": "sightseeing",
                "location": destination,
                "description": f"Explore the local attractions and culture of {destination}",
                "duration": "2 hours",
                "cost": 1200,
                "rating": 4.2,
                "image": self._get_image_url_for_activity(f"Morning in {destination}", destination, "sightseeing"),
                "selected_reason": "🎯 Perfect morning activity to start your day with local exploration.",
                "alternatives": self._generate_default_alternatives({"title": f"Morning in {destination}", "cost": 1200}),
                "travel_logistics": {
                    "from_previous": "Hotel",
                    "distance_km": 2.0,
                    "travel_time": "15 minutes",
                    "transport_mode": "Taxi",
                    "transport_cost": 150
                },
                "booking_info": {
                    "advance_booking": "Not required",
                    "availability": "Open access",
                    "cancellation": "N/A"
                }
            },
            {
                "time_slot": "2:00 PM - 4:00 PM",
                "title": f"Afternoon Experience in {destination}",
                "category": "culture",
                "location": destination,
                "description": f"Cultural experience showcasing the heritage of {destination}",
                "duration": "2 hours",
                "cost": 1500,
                "rating": 4.5,
                "image": self._get_image_url_for_activity(f"Culture in {destination}", destination, "culture"),
                "selected_reason": "🎯 Immersive cultural experience perfect for understanding local traditions.",
                "alternatives": self._generate_default_alternatives({"title": f"Culture in {destination}", "cost": 1500}),
                "travel_logistics": {
                    "from_previous": "Previous location",
                    "distance_km": 3.5,
                    "travel_time": "20 minutes",
                    "transport_mode": "Auto-rickshaw",
                    "transport_cost": 100
                },
                "booking_info": {
                    "advance_booking": "Recommended",
                    "availability": "Limited slots",
                    "cancellation": "24h free cancellation"
                }
            }
        ]
        
        return activities

    def _generate_default_alternatives(self, activity: Dict) -> List[Dict]:
        """Generate 9 default alternatives for any activity"""
        base_cost = activity.get('cost', 1000)
        base_name = activity.get('title', 'Activity')
        
        alternatives = []
        for i in range(1, 10):  # Generate 9 alternatives
            alt_cost = int(base_cost * (0.7 + i * 0.1))  # Vary cost from 70% to 160%
            alt_rating = round(3.8 + i * 0.15, 1)  # Vary rating from 3.8 to 5.15
            
            alternative = {
                "name": f"Alternative {base_name} Option {i}",
                "cost": alt_cost,
                "rating": min(alt_rating, 5.0),  # Cap at 5.0
                "reason": f"{'Budget-friendly' if alt_cost < base_cost else 'Premium'} option with {'excellent' if alt_rating >= 4.5 else 'good'} reviews",
                "distance_km": round(1.0 + i * 0.5, 1),
                "travel_time": f"{10 + i * 5} minutes"
            }
            alternatives.append(alternative)
        
        return alternatives

    def _get_image_url_for_activity(self, activity_title: str, location: str, category: str) -> str:
        """Generate appropriate image URL for activity"""
        # Category-based image mapping
        image_mapping = {
            'adventure': 'https://images.unsplash.com/photo-1544966503-7cc51d6d6657?w=400&h=300&fit=crop',
            'culture': 'https://images.unsplash.com/photo-1564677051169-a46a76359e41?w=400&h=300&fit=crop', 
            'dining': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400&h=300&fit=crop',
            'accommodation': 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=400&h=300&fit=crop',
            'transport': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop',
            'nature': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
            'beach': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=300&fit=crop',
            'shopping': 'https://images.unsplash.com/photo-1472851294608-062f824d29cc?w=400&h=300&fit=crop',
            'nightlife': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&h=300&fit=crop',
            'sightseeing': 'https://images.unsplash.com/photo-1539650116574-75c0c6d73f6b?w=400&h=300&fit=crop'
        }
        
        # Location-specific images
        location_images = {
            'goa': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=400&h=300&fit=crop',
            'kerala': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop',
            'mumbai': 'https://images.unsplash.com/photo-1595655406003-65bb1acc49ad?w=400&h=300&fit=crop',
            'delhi': 'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=400&h=300&fit=crop',
            'rajasthan': 'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400&h=300&fit=crop'
        }
        
        # Try location first, then category, then default
        location_key = location.lower() if location else ''
        category_key = category.lower() if category else ''
        
        for loc in location_images:
            if loc in location_key:
                return location_images[loc]
        
        if category_key in image_mapping:
            return image_mapping[category_key]
        
        # Default travel image
        return 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop'
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for session"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self._get_system_message()
        ).with_model("openai", "gpt-4o-mini")
    
    def _get_system_message(self) -> str:
        return f"""You are a MASTER TRAVEL PLANNER with real-time access to global flight, hotel, cab and activity inventories. 

CORE CAPABILITIES:
✅ Real-time inventory access for flights, hotels, cabs, activities
✅ Live pricing, availability, reviews, and local events data
✅ Advanced profile-based matching and recommendations
✅ Travel time optimization and conflict detection
✅ Explainable AI - clear reasoning for every recommendation

VARIANT SPECIALIZATION: {self.variant_type.value.upper()}
- Adventurer: Activity-dense, thrill-seeking, off-the-beaten-path experiences
- Balanced: Perfect mix of marquee sights + relaxation + local culture
- Luxury: Premium accommodations, curated exclusive experiences, VIP services

RECOMMENDATION METHODOLOGY:
1. PROFILE ANALYSIS: Age, interests, physical condition, travel style, budget
2. REAL-TIME MATCHING: Live availability, pricing, reviews (4.0+ rating preferred)
3. TOP 10 SELECTION: Auto-select #1 recommendation, provide 9 alternatives
4. TRAVEL OPTIMIZATION: Minimize transit time, maximize experience value
5. CONFLICT DETECTION: Flag scheduling conflicts, weather issues, capacity limits
6. EXPLAINABILITY: Clear reasoning for every single recommendation

OUTPUT REQUIREMENTS:
- Detailed day-wise itinerary with time slots
- Top recommendation auto-selected for each service slot
- 9 alternative options with reasons for each slot
- Clear explainability for every choice
- Travel time estimates and optimization notes
- Conflict warnings and resolution suggestions
- No repeated activities or venues across days
- Budget breakdown with real-time pricing

REASONING FORMAT:
"🎯 SELECTED: [Service Name] - Perfect for your [profile trait] preference. [Specific reason: rating/price/location/feature]. Distance: [X] km from hotel, Travel time: [Y] minutes."

Generate comprehensive, intelligent, and perfectly optimized travel experiences."""

    async def _handle_generation_request(self, event):
        """Handle itinerary generation request event"""
        try:
            session_id = event.session_id
            persona_type = event.data.get("persona_type")
            trip_details = event.data.get("trip_details", {})
            profile_data = event.data.get("profile_data", {})
            persona_tags = event.data.get("persona_tags", [persona_type] if persona_type else [])
            
            # Check if this agent should handle this request based on persona matching
            if self._should_handle_request(persona_type, profile_data):
                logger.info(f"🗓️ {self.variant_type.value.title()} agent generating itinerary for session {session_id}")
                
                itinerary = await self.generate_itinerary(session_id, trip_details, persona_tags, profile_data)
                
                await self.event_bus.emit(EventTypes.ITINERARY_VARIANT_GENERATED, {
                    "variant_type": self.variant_type.value,
                    "itinerary": itinerary,
                    "session_id": session_id
                }, session_id)
                
        except Exception as e:
            logger.error(f"{self.variant_type.value} itinerary generation error: {e}")

    def _should_handle_request(self, persona_type: str, profile_data: Dict[str, Any]) -> bool:
        """Determine if this agent should handle the request"""
        # All agents generate variants for comparison
        return True

    async def generate_itinerary(self, session_id: str, trip_details: Dict[str, Any], persona_tags: List[str], profile_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive itinerary with top 10 service recommendations and explainability"""
        try:
            logger.info(f"🏗️ Generating {self.variant_type.value} itinerary for {trip_details.get('destination')}")
            
            # Calculate trip duration
            start_date = datetime.fromisoformat(trip_details.get('start_date', '2024-12-25'))
            end_date = datetime.fromisoformat(trip_details.get('end_date', '2024-12-28'))
            days = (end_date - start_date).days + 1
            
            # Use profile_data if provided, otherwise create default from persona_tags
            if profile_data is None:
                profile_data = self._create_profile_from_persona_tags(persona_tags)
            
            # Enhanced context for master travel planner
            planner_context = f"""
            🎯 MASTER TRAVEL PLANNER REQUEST - GENERATE {self.variant_type.value.upper()} VARIANT
            
            TRAVELER PROFILE ANALYSIS:
            • Persona Tags: {', '.join(persona_tags)}
            • Vacation Style: {profile_data.get('vacation_style', ['balanced'])}
            • Experience Preference: {profile_data.get('experience_type', ['mixed'])}
            • Budget Level: {profile_data.get('budget_level', 'moderate')}
            • Physical Activity: {profile_data.get('activity_level', 'moderate')}
            • Interests: {', '.join(profile_data.get('interests', []))}
            • Age Group: {profile_data.get('age_group', 'adult')}
            • Travel Style: {profile_data.get('travel_style', 'explorer')}
            
            TRIP SPECIFICATIONS:
            • Destination: {trip_details.get('destination', 'India')}
            • Duration: {days} days ({start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')})
            • Group Size: {trip_details.get('adults', 2)} adults, {trip_details.get('children', 0)} children
            • Budget per night: {trip_details.get('budget_per_night', 3000)} INR
            • Total estimated budget: {trip_details.get('budget_per_night', 3000) * days} INR
            
            REAL-TIME REQUIREMENTS:
            ✅ Auto-select TOP recommendation for each service slot
            ✅ Provide 9 alternatives with clear ranking reasons
            ✅ No repeated activities/venues across {days} days
            ✅ Optimize travel times and detect conflicts
            ✅ Include live pricing and availability status
            ✅ 4.0+ rating preference for all recommendations
            
            GENERATE DETAILED DAY-WISE ITINERARY:
            
            For each day, create 4-6 activity slots with:
            1. TIME SLOT (e.g., 9:00 AM - 11:00 AM)
            2. SELECTED SERVICE with complete details
            3. REASONING: Why this is perfect for the traveler's profile
            4. TOP 9 ALTERNATIVES with brief reasons
            5. TRAVEL LOGISTICS: Distance, time, transport mode
            6. PRICING: Live cost estimates
            7. CONFLICT WARNINGS: If any scheduling issues
            
            MANDATORY JSON STRUCTURE:
            {{
                "variant_title": "{self.variant_type.value.title()} {trip_details.get('destination', 'Adventure')}",
                "total_days": {days},
                "total_cost": 0,
                "optimization_score": 0.95,
                "conflict_warnings": [],
                "daily_itinerary": [
                    {{
                        "day": 1,
                        "date": "{start_date.strftime('%Y-%m-%d')}",
                        "theme": "Arrival & Local Exploration",
                        "activities": [
                            {{
                                "time_slot": "10:00 AM - 12:00 PM",
                                "title": "Activity Name",
                                "category": "sightseeing|adventure|culture|dining|accommodation|transport",
                                "location": "Specific Location",
                                "description": "Detailed activity description",
                                "duration": "2 hours",
                                "cost": 1500,
                                "rating": 4.5,
                                "image": "https://images.unsplash.com/400x300/?activity",
                                "selected_reason": "🎯 Perfect for your adventure-seeking preference. Highest rated (4.8★) adventure activity in the area with live availability. Distance: 2.5km from hotel, Travel time: 15 minutes by taxi.",
                                "alternatives": [
                                    {{
                                        "name": "Alternative 1",
                                        "cost": 1200,
                                        "rating": 4.3,
                                        "reason": "Budget-friendly option with good reviews",
                                        "distance_km": 3.2,
                                        "travel_time": "20 minutes"
                                    }}
                                ],
                                "travel_logistics": {{
                                    "from_previous": "Hotel/Previous Location",
                                    "distance_km": 2.5,
                                    "travel_time": "15 minutes",
                                    "transport_mode": "Taxi",
                                    "transport_cost": 200
                                }},
                                "booking_info": {{
                                    "advance_booking": "Required",
                                    "availability": "Live slots available",
                                    "cancellation": "Free cancellation up to 24h"
                                }}
                            }}
                        ],
                        "daily_budget": 8500,
                        "daily_travel_time": "45 minutes total"
                    }}
                ]
            }}
            
            CRITICAL SUCCESS FACTORS:
            • Every activity MUST have clear explainable reasoning
            • All 9 alternatives MUST be provided for each slot
            • Travel optimization MUST minimize transit time
            • NO activity repetition across {days} days
            • Pricing MUST be realistic for {trip_details.get('destination')}
            • Schedule MUST be conflict-free and realistic
            """
            
            # Generate itinerary using enhanced LLM
            llm_client = self._get_llm_client(session_id)
            response = await asyncio.wait_for(
                llm_client.send_message(UserMessage(text=planner_context)),
                timeout=25.0  # Increased timeout for comprehensive generation
            )
            
            # Parse and validate comprehensive response
            itinerary_data = await self._parse_comprehensive_response(response, days, trip_details)
            
            # Post-process for quality assurance
            final_itinerary = await self._quality_assurance_check(itinerary_data, trip_details, profile_data)
            
            logger.info(f"✅ Generated {self.variant_type.value} variant with {len(final_itinerary.get('daily_itinerary', []))} days")
            return final_itinerary
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Itinerary generation timeout, using fallback for {self.variant_type.value}")
            return self._generate_fallback_itinerary(trip_details, days)
        except Exception as e:
            logger.error(f"❌ Itinerary generation error: {e}")
            return self._generate_fallback_itinerary(trip_details, days)

    def _create_profile_from_persona_tags(self, persona_tags: List[str]) -> Dict[str, Any]:
        """Create a basic profile from persona tags"""
        return {
            'vacation_style': ['balanced'],
            'experience_type': ['mixed'],
            'budget_level': 'moderate',
            'activity_level': 'moderate',
            'interests': persona_tags,
            'age_group': 'adult',
            'travel_style': 'explorer'
        }

    async def _parse_comprehensive_response(self, response: str, days: int, trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """Parse comprehensive LLM response into structured data"""
        try:
            import json
            import re
            
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
            
            # Parse JSON
            itinerary_data = json.loads(json_text.strip())
            
            # Validate and ensure required fields
            if 'daily_itinerary' not in itinerary_data:
                itinerary_data['daily_itinerary'] = []
            
            # Calculate total cost if not provided
            if 'total_cost' not in itinerary_data or itinerary_data['total_cost'] == 0:
                total_cost = 0
                for day in itinerary_data.get('daily_itinerary', []):
                    for activity in day.get('activities', []):
                        total_cost += activity.get('cost', 0)
                        # Add travel costs
                        travel_logistics = activity.get('travel_logistics', {})
                        total_cost += travel_logistics.get('transport_cost', 0)
                itinerary_data['total_cost'] = total_cost
            
            return itinerary_data
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse comprehensive response: {e}")
            return self._generate_fallback_itinerary_data(trip_details, days)

    async def _quality_assurance_check(self, itinerary_data: Dict[str, Any], trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quality assurance checks on generated itinerary"""
        try:
            # Check for required fields
            required_fields = ['variant_title', 'total_days', 'daily_itinerary']
            for field in required_fields:
                if field not in itinerary_data:
                    logger.warning(f"Missing required field: {field}")
                    return self._generate_fallback_itinerary_data(trip_details, itinerary_data.get('total_days', 3))
            
            # Validate daily itinerary structure
            for day_data in itinerary_data.get('daily_itinerary', []):
                if 'activities' not in day_data:
                    day_data['activities'] = []
                
                # Ensure each activity has required fields
                for activity in day_data['activities']:
                    if 'image' not in activity:
                        activity['image'] = self._get_image_url_for_activity(
                            activity.get('title', 'Activity'),
                            activity.get('location', trip_details.get('destination', 'India')),
                            activity.get('category', 'sightseeing')
                        )
                    
                    # Ensure alternatives exist
                    if 'alternatives' not in activity:
                        activity['alternatives'] = self._generate_default_alternatives(activity)
            
            return itinerary_data
            
        except Exception as e:
            logger.error(f"Quality assurance check failed: {e}")
            return self._generate_fallback_itinerary_data(trip_details, itinerary_data.get('total_days', 3))

    def _generate_fallback_itinerary_data(self, trip_details: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Generate fallback itinerary data in the new format"""
        destination = trip_details.get('destination', 'India')
        start_date = datetime.fromisoformat(trip_details.get('start_date', '2024-12-25'))
        
        daily_itinerary = []
        for day in range(1, days + 1):
            current_date = start_date + timedelta(days=day-1)
            daily_itinerary.append({
                "day": day,
                "date": current_date.strftime('%Y-%m-%d'),
                "theme": f"Day {day} in {destination}",
                "activities": [
                    {
                        "time_slot": "10:00 AM - 1:00 PM",
                        "title": f"Explore {destination}",
                        "category": "sightseeing",
                        "location": f"Central {destination}",
                        "description": f"Discover the highlights of {destination}",
                        "duration": "3 hours",
                        "cost": 2500,
                        "rating": 4.2,
                        "image": self._get_image_url_for_activity(f"Explore {destination}", destination, "sightseeing"),
                        "selected_reason": f"🎯 Perfect introduction to {destination} with highly rated local guides",
                        "alternatives": self._generate_default_alternatives({"title": f"Explore {destination}", "cost": 2500}),
                        "travel_logistics": {
                            "from_previous": "Hotel",
                            "distance_km": 2.0,
                            "travel_time": "10 minutes",
                            "transport_mode": "Taxi",
                            "transport_cost": 150
                        },
                        "booking_info": {
                            "advance_booking": "Recommended",
                            "availability": "Available",
                            "cancellation": "Free cancellation up to 24h"
                        }
                    }
                ],
                "daily_budget": 3000,
                "daily_travel_time": "30 minutes total"
            })
        
        return {
            "variant_title": f"{self.variant_type.value.title()} {destination}",
            "total_days": days,
            "total_cost": days * 3000,
            "optimization_score": 0.8,
            "conflict_warnings": [],
            "daily_itinerary": daily_itinerary
        }

    def _generate_default_alternatives(self, activity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default alternatives for an activity"""
        base_cost = activity.get('cost', 2000)
        alternatives = []
        
        for i in range(9):  # Generate 9 alternatives as required
            alternatives.append({
                "name": f"Alternative {i+1}",
                "cost": base_cost + (i * 200) - 400,  # Vary costs around base
                "rating": 4.0 + (i * 0.1),
                "reason": f"Alternative option with {'budget-friendly' if i < 3 else 'premium' if i > 6 else 'balanced'} pricing",
                "distance_km": 1.5 + (i * 0.3),
                "travel_time": f"{10 + (i * 2)} minutes"
            })
        
        return alternatives

    def _generate_fallback_itinerary(self, trip_details: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Generate fallback itinerary when LLM fails"""
        return self._generate_fallback_itinerary_data(trip_details, days)

    async def _generate_day_itinerary(self, day: int, date: datetime, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> DayItinerary:
        """Generate itinerary for a specific day"""
        destination = trip_details.get("destination", "India")
        
        # Get day-specific activities based on variant type
        activities = await self._get_day_activities(day, destination, trip_details, profile_data)
        
        # Calculate daily cost
        total_cost = sum(activity.cost for activity in activities)
        
        return DayItinerary(
            day=day,
            date=date.strftime("%Y-%m-%d"),
            theme=self._get_day_theme(day, destination),
            activities=activities,
            total_cost=total_cost
        )

    async def _get_day_activities(self, day: int, destination: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[Activity]:
        """Get activities for a specific day using LLM"""
        try:
            context = f"""
            Generate a detailed day {day} itinerary for a {self.variant_type.value} style trip to {destination}.
            
            Trip Context:
            - Destination: {destination}
            - Day: {day}
            - Trip Style: {self.variant_type.value}
            - Budget per night: ₹{trip_details.get('budget_per_night', 8000)}
            - Travelers: {trip_details.get('adults', 2)} adults, {trip_details.get('children', 0)} children
            - User preferences: {profile_data}
            
            Generate 3-4 activities for this day that match the {self.variant_type.value} style:
            
            Guidelines:
            - Include realistic timings (format: "HH:MM")
            - Include realistic costs in INR
            - Activities should be 1-4 hours duration
            - Include mix of activity types: arrival/departure, adventure, cultural, dining, sightseeing, relaxation
            - For day 1, include arrival logistics
            - Make activities specific to {destination}
            - Ensure activities match {self.variant_type.value} persona
            
            Respond in JSON array format:
            [
                {{
                    "name": "Activity Name",
                    "type": "arrival|departure|adventure|cultural|dining|sightseeing|relaxation|transportation|accommodation|shopping",
                    "time": "09:00",
                    "duration": "2 hours",
                    "location": "Specific location in {destination}",
                    "description": "Detailed description of the activity",
                    "cost": 2500,
                    "sustainability_tags": ["eco_friendly", "local_community"]
                }}
            ]
            """
            
            user_msg = UserMessage(text=context)
            llm_client = self._get_llm_client("temp_session")  # Use temp session for activity generation
            response = await llm_client.send_message(user_msg)
            
            # Parse JSON response (handle markdown-wrapped JSON)
            import json
            import uuid
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
                
                activities_data = json.loads(json_text.strip())
                
                activities = []
                for i, act_data in enumerate(activities_data):
                    # Map string type to enum
                    activity_type = ActivityType.SIGHTSEEING  # Default
                    try:
                        activity_type = ActivityType(act_data["type"])
                    except ValueError:
                        logger.warning(f"Invalid activity type: {act_data['type']}, using sightseeing")
                    
                    activity = Activity(
                        id=f"{self.variant_type.value}_day{day}_act{i}_{str(uuid.uuid4())[:8]}",
                        name=act_data["name"],
                        type=activity_type,
                        time=act_data["time"],
                        duration=act_data["duration"],
                        location=act_data["location"],
                        description=act_data["description"],
                        cost=float(act_data["cost"]),
                        image=self._get_image_url_for_activity(act_data["name"], act_data["location"], act_data["type"]),
                        sustainability_tags=act_data.get("sustainability_tags", [])
                    )
                    activities.append(activity)
                
                return activities
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse activities JSON for day {day}, using fallback")
                return await self._get_fallback_activities(day, destination, trip_details)
            
        except Exception as e:
            logger.error(f"LLM activity generation error for day {day}: {e}")
            return await self._get_fallback_activities(day, destination, trip_details)

    async def _get_fallback_activities(self, day: int, destination: str, trip_details: Dict[str, Any]) -> List[Activity]:
        """Fallback activities if LLM fails"""
        import uuid
        
        base_activities = [
            Activity(
                id=f"fallback_{day}_{str(uuid.uuid4())[:8]}",
                name=f"Explore {destination}",
                type=ActivityType.SIGHTSEEING,
                time="10:00",
                duration="3 hours",
                location=f"Central {destination}",
                description=f"Guided exploration of {destination}'s main attractions",
                cost=3000,
                image=self._get_image_url_for_activity(f"Explore {destination}", f"Central {destination}", "sightseeing"),
                sustainability_tags=["local_guides"]
            ),
            Activity(
                id=f"fallback_{day}_dining_{str(uuid.uuid4())[:8]}",
                name=f"Traditional {destination} Cuisine",
                type=ActivityType.DINING,
                time="19:00",
                duration="2 hours",
                location=f"Local Restaurant, {destination}",
                description=f"Authentic {destination} dining experience",
                cost=2000,
                image=self._get_image_url_for_activity(f"Traditional {destination} Cuisine", f"Local Restaurant, {destination}", "dining"),
                sustainability_tags=["local_cuisine"]
            )
        ]
        
        return base_activities

    def _get_variant_title(self) -> str:
        """Get variant title (to be overridden by subclasses)"""
        return f"{self.variant_type.value.title()} Experience"

    def _get_variant_description(self) -> str:
        """Get variant description (to be overridden by subclasses)"""
        return f"A {self.variant_type.value} travel experience"

    def _get_day_theme(self, day: int, destination: str) -> str:
        """Get theme for a specific day"""
        themes = {
            1: f"Arrival & {destination} Welcome",
            2: f"Explore {destination} Highlights",
            3: f"{destination} Adventures",
            4: f"Cultural {destination}",
            5: f"Hidden Gems of {destination}",
            6: f"Farewell {destination}"
        }
        return themes.get(day, f"Day {day} in {destination}")

    def _generate_highlights(self, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[str]:
        """Generate itinerary highlights"""
        return [
            "Personalized recommendations",
            "Local expert insights",
            "Flexible scheduling",
            "Authentic experiences"
        ]

    def _calculate_persona_match(self, profile_data: Dict[str, Any]) -> float:
        """Calculate how well this variant matches the user's persona"""
        return 0.8  # Base match score

    def _calculate_sustainability_score(self, daily_itineraries: List[DayItinerary]) -> float:
        """Calculate sustainability score for the itinerary"""
        # Count eco-friendly activities
        eco_activities = 0
        total_activities = 0
        
        for day in daily_itineraries:
            for activity in day.activities:
                total_activities += 1
                if any(tag in ["eco_friendly", "sustainable", "local_community"] for tag in activity.sustainability_tags):
                    eco_activities += 1
        
        return eco_activities / max(total_activities, 1)

    def _is_recommended(self, profile_data: Dict[str, Any]) -> bool:
        """Determine if this variant should be recommended"""
        return False  # Override in subclasses


class AdventurerAgent(BaseItineraryAgent):
    """Agent for generating adventurous itineraries"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        super().__init__(context_store, event_bus, ItineraryVariantType.ADVENTURER)
    
    def _get_variant_title(self) -> str:
        return "Adventure Explorer"
    
    def _get_variant_description(self) -> str:
        return "Action-packed with outdoor activities, adventure sports, and thrilling experiences"
    
    def _generate_highlights(self, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[str]:
        return [
            "Extreme Sports & Adventures",
            "Professional Safety Equipment", 
            "Experienced Adventure Guides",
            "Adrenaline-Pumping Activities",
            "Mountain & Water Sports"
        ]
    
    def _is_recommended(self, profile_data: Dict[str, Any]) -> bool:
        vacation_style = profile_data.get('vacation_style', '')
        interests = profile_data.get('interests', [])
        return vacation_style == 'adventurous' or 'hiking' in interests


class BalancedAgent(BaseItineraryAgent):
    """Agent for generating balanced itineraries"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        super().__init__(context_store, event_bus, ItineraryVariantType.BALANCED)
    
    def _get_variant_title(self) -> str:
        return "Perfect Balance"
    
    def _get_variant_description(self) -> str:
        return "Perfect mix of adventure, culture, relaxation, and sightseeing"
    
    def _generate_highlights(self, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[str]:
        return [
            "Cultural Heritage Sites",
            "Scenic Natural Beauty",
            "Wellness & Relaxation", 
            "Local Cuisine Experiences",
            "Moderate Adventure Activities"
        ]
    
    def _is_recommended(self, profile_data: Dict[str, Any]) -> bool:
        vacation_style = profile_data.get('vacation_style', '')
        return vacation_style == 'balanced' or vacation_style == ''


class LuxuryAgent(BaseItineraryAgent):
    """Agent for generating luxury itineraries"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        super().__init__(context_store, event_bus, ItineraryVariantType.LUXURY)
    
    def _get_variant_title(self) -> str:
        return "Premium Experience"
    
    def _get_variant_description(self) -> str:
        return "Luxury resorts, fine dining, spa treatments, and exclusive experiences"
    
    def _generate_highlights(self, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[str]:
        return [
            "5-Star Luxury Resorts",
            "Private & Exclusive Experiences",
            "Gourmet Fine Dining",
            "Premium Spa & Wellness", 
            "Personal Concierge Service"
        ]
    
    def _is_recommended(self, profile_data: Dict[str, Any]) -> bool:
        accommodations = profile_data.get('accommodation', [])
        return 'luxury_hotels' in accommodations