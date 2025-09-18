"""
Itinerary Generation Agents - Separate agents for Adventurer, Balanced, and Luxury variants
Generate top service recommendations for flights, hotels, cabs, and sightseeing
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
    """Base class for itinerary generation agents"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus, variant_type: ItineraryVariantType):
        self.context_store = context_store
        self.event_bus = event_bus
        self.variant_type = variant_type
        
        # Initialize LLM client
        self.llm_client = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            system_message=self._get_system_message()
        ).with_model("openai", "gpt-4o-mini")
        
        # Subscribe to itinerary generation requests
        self.event_bus.subscribe(EventTypes.ITINERARY_GENERATION_REQUESTED, self._handle_generation_request)
    
    def _get_system_message(self) -> str:
        return f"""You are Travello.ai's {self.variant_type.value.title()} Itinerary Generation Agent. 

Your role is to create detailed, personalized itineraries that match the {self.variant_type.value} travel style.

CORE RESPONSIBILITIES:
1. Generate day-by-day itineraries with specific activities, timings, and locations
2. Include transportation, accommodation, dining, and sightseeing recommendations
3. Provide accurate cost estimates for all activities and services
4. Ensure activities match the {self.variant_type.value} persona and preferences
5. Create realistic schedules with appropriate travel times and rest periods
6. Include local insights and unique experiences

ITINERARY STRUCTURE:
- Each day should have 4-6 activities with specific timings
- Include arrival/departure logistics
- Mix of must-see attractions and hidden gems
- Appropriate dining recommendations
- Transportation between activities
- Rest periods and flexibility for spontaneous exploration

PERSONALITY:
- Expert local knowledge and insider tips
- Practical and realistic scheduling
- Enthusiastic about unique experiences
- Detail-oriented with accurate information
- Cost-conscious with transparent pricing

Always create comprehensive, actionable itineraries that travelers can actually follow."""

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

    async def generate_itinerary(self, session_id: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> ItineraryVariant:
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
        """Get activities for a specific day (to be overridden by subclasses)"""
        return []

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
    
    async def _get_day_activities(self, day: int, destination: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[Activity]:
        """Generate adventure-focused activities"""
        activities = []
        
        if day == 1:
            # Arrival day
            activities.extend([
                Activity(
                    id=f"adv_arrival_{day}",
                    name="Airport Transfer & Adventure Briefing",
                    type=ActivityType.ARRIVAL,
                    time="10:00",
                    duration="2 hours",
                    location=f"{destination} Airport to Adventure Base",
                    description="Smooth arrival with adventure gear briefing and safety orientation",
                    cost=2500,
                    image=f"https://images.unsplash.com/800x400/?adventure-briefing-{destination.lower()}",
                    sustainability_tags=["local_transport"]
                ),
                Activity(
                    id=f"adv_activity_{day}_1",
                    name="Rock Climbing & Rappelling",
                    type=ActivityType.ADVENTURE,
                    time="14:00",
                    duration="4 hours",
                    location=f"{destination} Adventure Park",
                    description="Adrenaline-pumping rock climbing with professional instructors and safety gear",
                    cost=4500,
                    image=f"https://images.unsplash.com/800x400/?rock-climbing-{destination.lower()}",
                    sustainability_tags=["outdoor_activity", "eco_friendly"]
                ),
                Activity(
                    id=f"adv_dining_{day}",
                    name="Adventure Camp Dinner",
                    type=ActivityType.DINING,
                    time="19:00",
                    duration="2 hours",
                    location=f"Mountain View Restaurant, {destination}",
                    description="Hearty local cuisine with mountain views and adventure stories",
                    cost=1800,
                    image=f"https://images.unsplash.com/800x400/?mountain-restaurant-{destination.lower()}",
                    sustainability_tags=["local_cuisine"]
                )
            ])
        elif day == 2:
            # Water adventures
            activities.extend([
                Activity(
                    id=f"adv_activity_{day}_1",
                    name="White Water Rafting",
                    type=ActivityType.ADVENTURE,
                    time="08:00",
                    duration="5 hours",
                    location=f"{destination} River",
                    description="Thrilling Grade III-IV rapids with experienced guides and safety equipment",
                    cost=6000,
                    image=f"https://images.unsplash.com/800x400/?rafting-{destination.lower()}",
                    sustainability_tags=["eco_friendly", "local_guides"]
                ),
                Activity(
                    id=f"adv_activity_{day}_2",
                    name="Kayaking & Cliff Jumping",
                    type=ActivityType.ADVENTURE,
                    time="15:00",
                    duration="3 hours",
                    location=f"{destination} Lake",
                    description="Kayaking in pristine waters followed by optional cliff jumping",
                    cost=3500,
                    image=f"https://images.unsplash.com/800x400/?kayaking-{destination.lower()}",
                    sustainability_tags=["water_sports", "natural_environment"]
                )
            ])
        elif day == 3:
            # Mountain adventures
            activities.extend([
                Activity(
                    id=f"adv_activity_{day}_1",
                    name="Paragliding Experience",
                    type=ActivityType.ADVENTURE,
                    time="09:00",
                    duration="4 hours",
                    location=f"{destination} Hills",
                    description="Soar through the skies with certified pilots and breathtaking aerial views",
                    cost=8000,
                    image=f"https://images.unsplash.com/800x400/?paragliding-{destination.lower()}",
                    sustainability_tags=["eco_friendly", "minimal_impact"]
                ),
                Activity(
                    id=f"adv_activity_{day}_2",
                    name="Mountain Biking Trail",
                    type=ActivityType.ADVENTURE,
                    time="14:00",
                    duration="3 hours",
                    location=f"{destination} Forest Trails",
                    description="Challenging mountain bike trails through scenic forest paths",
                    cost=2800,
                    image=f"https://images.unsplash.com/800x400/?mountain-biking-{destination.lower()}",
                    sustainability_tags=["eco_friendly", "forest_trails"]
                )
            ])
        
        return activities
    
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
    
    async def _get_day_activities(self, day: int, destination: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[Activity]:
        """Generate balanced activities"""
        activities = []
        
        if day == 1:
            # Cultural immersion
            activities.extend([
                Activity(
                    id=f"bal_arrival_{day}",
                    name="Heritage Welcome & Check-in",
                    type=ActivityType.ARRIVAL,
                    time="10:00",
                    duration="2 hours",
                    location=f"Heritage Hotel, {destination}",
                    description="Traditional welcome with local cultural orientation",
                    cost=2000,
                    image=f"https://images.unsplash.com/800x400/?heritage-hotel-{destination.lower()}",
                    sustainability_tags=["local_culture", "heritage_preservation"]
                ),
                Activity(
                    id=f"bal_cultural_{day}",
                    name=f"Heritage {destination} Walking Tour",
                    type=ActivityType.CULTURAL,
                    time="14:00",
                    duration="3 hours",
                    location=f"Historic {destination} Center",
                    description="Guided walk through ancient temples, markets, and cultural landmarks",
                    cost=1500,
                    image=f"https://images.unsplash.com/800x400/?heritage-walk-{destination.lower()}",
                    sustainability_tags=["local_guides", "cultural_preservation"]
                ),
                Activity(
                    id=f"bal_dining_{day}",
                    name="Traditional Cooking Class",
                    type=ActivityType.DINING,
                    time="18:00",
                    duration="3 hours",
                    location=f"Local Kitchen, {destination}",
                    description="Learn authentic local cuisine from expert chefs with family recipes",
                    cost=3000,
                    image=f"https://images.unsplash.com/800x400/?cooking-class-{destination.lower()}",
                    sustainability_tags=["local_cuisine", "cultural_exchange"]
                )
            ])
        elif day == 2:
            # Nature and relaxation
            activities.extend([
                Activity(
                    id=f"bal_nature_{day}",
                    name=f"{destination} Scenic Cruise",
                    type=ActivityType.SIGHTSEEING,
                    time="09:00",
                    duration="4 hours",
                    location=f"{destination} Backwaters/Coast",
                    description="Peaceful cruise through pristine natural landscapes",
                    cost=4000,
                    image=f"https://images.unsplash.com/800x400/?scenic-cruise-{destination.lower()}",
                    sustainability_tags=["eco_friendly", "natural_environment"]
                ),
                Activity(
                    id=f"bal_wellness_{day}",
                    name="Ayurvedic Spa Experience",
                    type=ActivityType.RELAXATION,
                    time="15:00",
                    duration="2 hours",
                    location=f"Wellness Center, {destination}",
                    description="Rejuvenating traditional spa treatments with natural oils",
                    cost=3500,
                    image=f"https://images.unsplash.com/800x400/?spa-treatment-{destination.lower()}",
                    sustainability_tags=["wellness", "traditional_practices"]
                )
            ])
        elif day == 3:
            # Adventure and exploration
            activities.extend([
                Activity(
                    id=f"bal_adventure_{day}",
                    name="Moderate Trekking & Nature Walk",
                    type=ActivityType.ADVENTURE,
                    time="08:00",
                    duration="4 hours",
                    location=f"{destination} Hills/Forest",
                    description="Scenic trek suitable for all fitness levels with wildlife spotting",
                    cost=2500,
                    image=f"https://images.unsplash.com/800x400/?nature-trek-{destination.lower()}",
                    sustainability_tags=["eco_friendly", "wildlife_conservation"]
                ),
                Activity(
                    id=f"bal_shopping_{day}",
                    name="Local Markets & Handicrafts",
                    type=ActivityType.SHOPPING,
                    time="14:00",
                    duration="3 hours",
                    location=f"{destination} Traditional Markets",
                    description="Explore vibrant markets with authentic handicrafts and local products",
                    cost=2000,
                    image=f"https://images.unsplash.com/800x400/?local-market-{destination.lower()}",
                    sustainability_tags=["local_artisans", "community_support"]
                )
            ])
        
        return activities
    
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
    
    async def _get_day_activities(self, day: int, destination: str, trip_details: Dict[str, Any], profile_data: Dict[str, Any]) -> List[Activity]:
        """Generate luxury-focused activities"""
        activities = []
        
        if day == 1:
            # Luxury arrival
            activities.extend([
                Activity(
                    id=f"lux_arrival_{day}",
                    name="Premium Transfer & Luxury Check-in",
                    type=ActivityType.ARRIVAL,
                    time="10:00",
                    duration="2 hours",
                    location=f"5-Star Luxury Resort, {destination}",
                    description="Private luxury transfer with champagne welcome and suite upgrade",
                    cost=8000,
                    image=f"https://images.unsplash.com/800x400/?luxury-resort-{destination.lower()}",
                    sustainability_tags=["premium_service"]
                ),
                Activity(
                    id=f"lux_spa_{day}",
                    name="Signature Spa Treatment",
                    type=ActivityType.RELAXATION,
                    time="14:00",
                    duration="3 hours",
                    location=f"Resort Spa, {destination}",
                    description="Exclusive spa treatment with premium oils and expert therapists",
                    cost=12000,
                    image=f"https://images.unsplash.com/800x400/?luxury-spa-{destination.lower()}",
                    sustainability_tags=["wellness", "premium_service"]
                ),
                Activity(
                    id=f"lux_dining_{day}",
                    name="Fine Dining Experience",
                    type=ActivityType.DINING,
                    time="19:30",
                    duration="3 hours",
                    location=f"Michelin-Style Restaurant, {destination}",
                    description="Multi-course gourmet meal with wine pairing and personal chef interaction",
                    cost=15000,
                    image=f"https://images.unsplash.com/800x400/?fine-dining-{destination.lower()}",
                    sustainability_tags=["gourmet_cuisine", "local_ingredients"]
                )
            ])
        elif day == 2:
            # Exclusive experiences
            activities.extend([
                Activity(
                    id=f"lux_private_{day}",
                    name="Private Yacht Charter",
                    type=ActivityType.SIGHTSEEING,
                    time="10:00",
                    duration="6 hours",
                    location=f"{destination} Coast/Lake",
                    description="Exclusive yacht charter with private crew, gourmet lunch, and water activities",
                    cost=25000,
                    image=f"https://images.unsplash.com/800x400/?private-yacht-{destination.lower()}",
                    sustainability_tags=["exclusive_access", "premium_service"]
                ),
                Activity(
                    id=f"lux_helicopter_{day}",
                    name="Helicopter Scenic Tour",
                    type=ActivityType.SIGHTSEEING,
                    time="17:00",
                    duration="1 hour",
                    location=f"{destination} Helipad",
                    description="Private helicopter tour with aerial photography and champagne service",
                    cost=18000,
                    image=f"https://images.unsplash.com/800x400/?helicopter-tour-{destination.lower()}",
                    sustainability_tags=["scenic_views", "exclusive_access"]
                )
            ])
        elif day == 3:
            # Cultural luxury
            activities.extend([
                Activity(
                    id=f"lux_private_tour_{day}",
                    name="Private Heritage Tour with Expert",
                    type=ActivityType.CULTURAL,
                    time="09:00",
                    duration="4 hours",
                    location=f"Premium {destination} Attractions",
                    description="Exclusive private tour with renowned local historian and VIP access",
                    cost=8000,
                    image=f"https://images.unsplash.com/800x400/?private-tour-{destination.lower()}",
                    sustainability_tags=["cultural_preservation", "expert_guides"]
                ),
                Activity(
                    id=f"lux_shopping_{day}",
                    name="Personal Shopping Experience",
                    type=ActivityType.SHOPPING,
                    time="14:00",
                    duration="3 hours",
                    location=f"Luxury Boutiques, {destination}",
                    description="Personal shopper service at premium boutiques and designer stores",
                    cost=5000,
                    image=f"https://images.unsplash.com/800x400/?luxury-shopping-{destination.lower()}",
                    sustainability_tags=["premium_service", "local_artisans"]
                )
            ])
        
        return activities
    
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