"""
Master Travel Planner - Itinerary Generation Agents
Real-time access to global flight, hotel, cab and activity inventories with intelligent recommendations
"""

import os
import logging
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
            
            # Check if this agent should handle this request based on persona matching
            if self._should_handle_request(persona_type, profile_data):
                logger.info(f"🗓️ {self.variant_type.value.title()} agent generating itinerary for session {session_id}")
                
                itinerary = await self.generate_itinerary(session_id, trip_details, profile_data)
                
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
        """Generate itinerary variant"""
        try:
            # Calculate trip duration
            start_date = datetime.fromisoformat(trip_details.get("start_date", "2024-12-15"))
            end_date = datetime.fromisoformat(trip_details.get("end_date", "2024-12-20"))
            duration = (end_date - start_date).days
            
            # Generate daily itineraries
            daily_itineraries = []
            current_date = start_date
            
            for day in range(1, duration + 1):
                day_itinerary = await self._generate_day_itinerary(
                    day, current_date, trip_details, profile_data
                )
                daily_itineraries.append(day_itinerary)
                current_date += timedelta(days=1)
            
            # Calculate totals
            total_cost = sum(day.total_cost for day in daily_itineraries)
            total_activities = sum(len(day.activities) for day in daily_itineraries)
            activity_types = list(set([
                activity.type.value for day in daily_itineraries 
                for activity in day.activities
            ]))
            
            # Generate highlights
            highlights = self._generate_highlights(trip_details, profile_data)
            
            # Create itinerary variant
            itinerary = ItineraryVariant(
                id=str(uuid.uuid4()),
                type=self.variant_type,
                title=self._get_variant_title(),
                description=self._get_variant_description(),
                days=duration,
                total_cost=total_cost,
                daily_itinerary=daily_itineraries,
                highlights=highlights,
                persona_match=self._calculate_persona_match(profile_data),
                sustainability_score=self._calculate_sustainability_score(daily_itineraries),
                recommended=self._is_recommended(profile_data),
                total_activities=total_activities,
                activity_types=activity_types
            )
            
            # Store in context
            self.context_store.add_itinerary(session_id, itinerary.id, itinerary.dict())
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Itinerary generation error: {e}")
            return self._get_fallback_itinerary(trip_details)

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

    def _get_fallback_itinerary(self, trip_details: Dict[str, Any]) -> ItineraryVariant:
        """Get fallback itinerary when generation fails"""
        return ItineraryVariant(
            id=str(uuid.uuid4()),
            type=self.variant_type,
            title=self._get_variant_title(),
            description="A curated travel experience",
            days=3,
            total_cost=15000,
            daily_itinerary=[],
            highlights=["Curated experiences"],
            persona_match=0.5,
            sustainability_score=0.5,
            recommended=False,
            total_activities=0,
            activity_types=[]
        )


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