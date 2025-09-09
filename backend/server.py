from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
emergent_key = os.environ.get('EMERGENT_LLM_KEY')
system_message = """You are Travello.ai, an expert Indian adventure travel assistant. You create amazing travel experiences with a natural, conversational approach.

PERSONALITY:
- Friendly, enthusiastic, and genuinely helpful
- Natural conversationalist who builds on what users say
- Provides immediate value and specific suggestions
- Avoids repetitive questions - be progressive in conversation

EXPERTISE:
- Indian adventure tourism specialist
- Real pricing in Indian Rupees with current market rates
- Specific destinations: Manali, Rishikesh, Andaman, Kerala, Rajasthan, Pondicherry
- Activities: Trekking, rafting, paragliding, scuba diving, cultural experiences

CONVERSATION STYLE:
1. Listen to what users say and build on it naturally
2. Provide immediate, actionable suggestions with real pricing
3. Offer specific examples they can choose from
4. Be helpful without being pushy or repetitive
5. Make planning feel easy and exciting

RESPONSE APPROACH:
- When users say general things like "plan a trip" → Give specific destination options with pricing
- When they mention a destination → Provide trip options and experiences for that place  
- When they ask for itineraries → Create detailed day-by-day plans
- When they ask about hotels → Give categorized options by budget

NEVER:
- Ask the same questions repeatedly
- Give generic templated responses
- Overwhelm with too many questions at once
- Ignore what the user has already told you

Be the travel buddy they wish they had - knowledgeable, helpful, and naturally conversational."""

# Real Thrillophilia Travel Data - Updated with actual packages
MOCK_DESTINATIONS = [
    {
        "id": "manali_himachal",
        "name": "Manali",
        "country": "India", 
        "state": "Himachal Pradesh",
        "coordinates": {"lat": 32.2396, "lng": 77.1887},
        "hero_image": "https://images.unsplash.com/photo-1464822759844-d150baec0494?w=800&h=400&fit=crop",
        "category": ["Adventure", "Mountains", "Paragliding", "River Rafting"],
        "weather": {"temp": "18°C", "condition": "Pleasant"},  
        "description": "Adventure hub of Himachal Pradesh offering paragliding, river rafting, trekking, and stunning Himalayan views.",
        "highlights": ["Solang Valley Paragliding", "Beas River Rafting", "Rohtang Pass", "Snow Activities"],
        "why_match": "Perfect for adventure sports enthusiasts",
        "activities": [
            {"name": "River Rafting + Paragliding Combo", "price": "₹2,199", "duration": "Full Day"},
            {"name": "Paragliding Flight", "price": "₹3,000", "duration": "15 mins"},
            {"name": "River Rafting", "price": "₹1,500", "duration": "2 hours"}
        ]
    },
    {
        "id": "rishikesh_uttarakhand",
        "name": "Rishikesh",
        "country": "India",
        "state": "Uttarakhand", 
        "coordinates": {"lat": 30.0869, "lng": 78.2676},
        "hero_image": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&h=400&fit=crop",
        "category": ["Adventure", "Spiritual", "River Rafting", "Bungee Jumping"],
        "weather": {"temp": "25°C", "condition": "Sunny"},
        "description": "Yoga capital and adventure hub offering world-class river rafting, bungee jumping, and spiritual experiences.",
        "highlights": ["White Water Rafting", "Bungee Jumping", "Lakshman Jhula", "Yoga Ashrams"],
        "why_match": "Ultimate destination for adventure and spirituality",
        "activities": [
            {"name": "16km White Water Rafting", "price": "₹3,000", "duration": "4 hours"},
            {"name": "Adventure Camp Package", "price": "₹4,500", "duration": "2 days"},
            {"name": "Bungee Jumping", "price": "₹3,500", "duration": "1 hour"}
        ]
    },
    {
        "id": "andaman_islands",
        "name": "Andaman Islands", 
        "country": "India",
        "state": "Andaman & Nicobar",
        "coordinates": {"lat": 11.7401, "lng": 92.6586},
        "hero_image": "https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=800&h=400&fit=crop",
        "category": ["Beach", "Scuba Diving", "Marine Life", "Water Sports"],
        "weather": {"temp": "30°C", "condition": "Tropical"},
        "description": "Pristine tropical islands with crystal clear waters, coral reefs, and world-class scuba diving.",
        "highlights": ["Scuba Diving", "Snorkeling", "Radhanagar Beach", "Neil Island"],
        "why_match": "Paradise for marine life and beach lovers",
        "activities": [
            {"name": "Scuba Diving Session", "price": "₹3,500", "duration": "30 mins"},
            {"name": "Snorkeling Experience", "price": "₹2,000", "duration": "1 hour"},
            {"name": "Island Hopping Tour", "price": "₹5,500", "duration": "Full Day"}
        ]
    },
    {
        "id": "pondicherry_tamil_nadu",
        "name": "Pondicherry",
        "country": "India",
        "state": "Tamil Nadu",
        "coordinates": {"lat": 11.9416, "lng": 79.8083},
        "hero_image": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800&h=400&fit=crop",
        "category": ["Beach", "Scuba Diving", "French Culture", "Water Sports"],
        "weather": {"temp": "29°C", "condition": "Sunny"},
        "description": "French colonial charm meets adventure with scuba diving, surfing, and cultural experiences.",
        "highlights": ["Scuba Diving", "French Quarter", "Auroville", "Paradise Beach"],
        "why_match": "Unique blend of culture and water sports",
        "activities": [
            {"name": "Scuba Diving with Videography", "price": "₹6,499", "duration": "2 hours"},
            {"name": "Surfing Lessons", "price": "₹2,500", "duration": "1 hour"},
            {"name": "Heritage Walk", "price": "₹1,500", "duration": "3 hours"}
        ]
    },
    {
        "id": "kerala_backwaters",
        "name": "Kerala",
        "country": "India",
        "state": "Kerala",
        "coordinates": {"lat": 10.8505, "lng": 76.2711},
        "hero_image": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=400&fit=crop",
        "category": ["Backwaters", "Houseboat", "Nature", "Cultural"],
        "weather": {"temp": "28°C", "condition": "Humid"},
        "description": "God's own country with serene backwaters, houseboat cruises, spice plantations, and Ayurvedic treatments.",
        "highlights": ["Alleppey Houseboat", "Munnar Tea Gardens", "Thekkady Wildlife", "Kochi Heritage"],
        "why_match": "Perfect for nature lovers and cultural enthusiasts",
        "activities": [
            {"name": "8-Day Kerala Expedition", "price": "₹25,999", "duration": "8 days"},
            {"name": "Houseboat Stay Package", "price": "₹8,500", "duration": "2 days"},
            {"name": "Spice Plantation Tour", "price": "₹2,000", "duration": "Half Day"}
        ]
    },
    {
        "id": "rajasthan_desert",
        "name": "Rajasthan",
        "country": "India",
        "state": "Rajasthan", 
        "coordinates": {"lat": 27.0238, "lng": 74.2179},
        "hero_image": "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=800&h=400&fit=crop",
        "category": ["Desert Safari", "Heritage", "Culture", "Palaces"],
        "weather": {"temp": "32°C", "condition": "Sunny"},
        "description": "Land of maharajas with majestic palaces, desert safaris, camel rides, and royal heritage.",
        "highlights": ["Jaisalmer Desert Safari", "Udaipur Palaces", "Jaipur Pink City", "Camel Safari"],
        "why_match": "Ultimate destination for heritage and desert adventure",
        "activities": [
            {"name": "Desert Safari Package", "price": "₹4,500", "duration": "2 days"},
            {"name": "Heritage Palace Tour", "price": "₹15,999", "duration": "7 days"},
            {"name": "Camel Safari", "price": "₹2,500", "duration": "1 day"}
        ]
    }
]

# Real Thrillophilia Tours Data
THRILLOPHILIA_TOURS = [
    {
        "id": "manali_adventure_combo",
        "name": "River Rafting + Paragliding Combo",
        "location": "Manali, Himachal Pradesh",
        "price": "₹2,199",
        "original_price": "₹3,500",
        "duration": "Full Day",
        "image": "https://images.unsplash.com/photo-1464822759844-d150baec0494?w=400&h=300&fit=crop",
        "rating": 4.8,
        "reviews": 1250,
        "highlights": ["9km Beas River Rafting", "12-min Paragliding from 7000ft", "Grade II & III Rapids"],
        "category": "Adventure Combo"
    },
    {
        "id": "rishikesh_rafting_camp",
        "name": "16km White Water Rafting + Adventure Camp",
        "location": "Rishikesh, Uttarakhand", 
        "price": "₹3,000",
        "original_price": "₹4,000",
        "duration": "2 Days",
        "image": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400&h=300&fit=crop",
        "rating": 4.9,
        "reviews": 2100,
        "highlights": ["Grade III & IV Rapids", "Rock Climbing", "Rappelling", "Riverside Camping"],
        "category": "Adventure Package"
    },
    {
        "id": "kerala_enchanting_expedition",
        "name": "8-Day Enchanting Expedition of Kerala",
        "location": "Kerala (Kochi to Trivandrum)",
        "price": "₹25,999", 
        "original_price": "₹32,000",
        "duration": "8 Days",
        "image": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=400&h=300&fit=crop",
        "rating": 4.7,
        "reviews": 890,
        "highlights": ["Munnar Tea Gardens", "Alleppey Houseboat", "Thekkady Wildlife", "Kovalam Beach"],
        "category": "Cultural Tour"
    },
    {
        "id": "rajasthan_heritage_tour",
        "name": "Rajasthan Heritage & Desert Safari",
        "location": "Rajasthan (Jaipur to Jaisalmer)",
        "price": "₹15,999",
        "original_price": "₹20,000", 
        "duration": "7 Days",
        "image": "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=400&h=300&fit=crop",
        "rating": 4.6,
        "reviews": 750,
        "highlights": ["Amber Fort", "Desert Safari", "Camel Ride", "Palace Hotels"],
        "category": "Heritage Tour"
    }
]

# Real Thrillophilia Activities Data  
THRILLOPHILIA_ACTIVITIES = [
    {
        "id": "manali_paragliding",
        "name": "Paragliding in Manali",
        "location": "Solang Valley, Manali",
        "price": "₹3,000",
        "original_price": "₹3,500",
        "duration": "15 minutes",
        "image": "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=400&h=300&fit=crop",
        "rating": 4.8,
        "reviews": 1845,
        "highlights": ["300m Launch Height", "Himalayan Views", "Certified Instructors"],
        "category": "Adventure"
    },
    {
        "id": "pondicherry_scuba_diving",
        "name": "Scuba Diving with Free Videography",
        "location": "Pondicherry", 
        "price": "₹6,499",
        "original_price": "₹7,500",
        "duration": "2 Hours",
        "image": "https://images.unsplash.com/photo-1544551763-77ef2d0cfc6c?w=400&h=300&fit=crop",
        "rating": 4.9,
        "reviews": 920,
        "highlights": ["Bay of Bengal Diving", "Professional Video", "Beginner Friendly"],
        "category": "Water Sports"
    },
    {
        "id": "andaman_scuba_diving",
        "name": "Scuba Diving in Andaman",
        "location": "Havelock Island, Andaman",
        "price": "₹3,500", 
        "original_price": "₹4,200",
        "duration": "30 minutes",
        "image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400&h=300&fit=crop",
        "rating": 4.9,
        "reviews": 1150,
        "highlights": ["Coral Reef Diving", "Tropical Fish", "Crystal Clear Waters"],
        "category": "Marine Adventure"
    },
    {
        "id": "rishikesh_bungee_jumping",
        "name": "Bungee Jumping in Rishikesh",
        "location": "Jumpin Heights, Rishikesh",
        "price": "₹3,500",
        "original_price": "₹4,000", 
        "duration": "1 Hour",
        "image": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=300&fit=crop",
        "rating": 4.7,
        "reviews": 2200,
        "highlights": ["83m Jump Height", "Fixed Platform", "Safety Certified"],
        "category": "Extreme Adventure"
    }
]

MOCK_HOTELS = [
    {
        "id": "hotel_paris_1",
        "destination_id": "paris_france",
        "name": "Le Marais Grand Hotel",
        "hero_image": "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&h=400&fit=crop",
        "rating": 4.5,
        "price_range": {"min": 120, "max": 180, "currency": "USD"},
        "category": "Boutique",
        "amenities": ["WiFi", "Restaurant", "Spa", "Concierge"],
        "location": "Le Marais District",
        "pitch": "Charming boutique hotel in historic Le Marais",
        "why_match": "Perfect location for exploring Paris on foot",
        "cancellation_policy": "Free cancellation until 24 hours before check-in"
    },
    {
        "id": "hotel_tokyo_1",
        "destination_id": "tokyo_japan",
        "name": "Tokyo Central Tower",
        "hero_image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&h=400&fit=crop",
        "rating": 4.8,
        "price_range": {"min": 200, "max": 300, "currency": "USD"},
        "category": "Luxury",
        "amenities": ["WiFi", "Restaurant", "Gym", "City Views"],
        "location": "Shibuya",
        "pitch": "Modern luxury hotel with stunning city views",
        "why_match": "Central location near major attractions",
        "cancellation_policy": "Free cancellation until 48 hours before check-in"
    },
    {
        "id": "hotel_bali_1",
        "destination_id": "bali_indonesia",
        "name": "Ubud Jungle Resort",
        "hero_image": "https://images.unsplash.com/photo-1540541338287-41700207dee6?w=600&h=400&fit=crop",
        "rating": 4.6,
        "price_range": {"min": 80, "max": 150, "currency": "USD"},
        "category": "Resort",
        "amenities": ["Pool", "Spa", "Restaurant", "Nature Views"],
        "location": "Ubud",
        "pitch": "Peaceful resort surrounded by lush jungle",
        "why_match": "Perfect for nature lovers and relaxation",
        "cancellation_policy": "Free cancellation until 72 hours before check-in"
    }
]

# Memory storage for conversation context
conversation_memory = {}

def update_conversation_memory(session_id: str, message: str, response: str, trip_details: dict):
    """Update conversation memory with key information"""
    if session_id not in conversation_memory:
        conversation_memory[session_id] = {
            "conversation_history": [],
            "mentioned_destinations": set(),
            "user_preferences": {},
            "trip_context": {}
        }
    
    memory = conversation_memory[session_id]
    
    # Add to conversation history (keep last 10 exchanges)
    memory["conversation_history"].append({
        "user": message,
        "assistant": response[:200] + "..." if len(response) > 200 else response,
        "timestamp": datetime.now().isoformat()
    })
    if len(memory["conversation_history"]) > 10:
        memory["conversation_history"] = memory["conversation_history"][-10:]
    
    # Track mentioned destinations
    for dest in MOCK_DESTINATIONS:
        if dest["name"].lower() in message.lower():
            memory["mentioned_destinations"].add(dest["name"])
    
    # Update trip context
    if trip_details:
        memory["trip_context"].update(trip_details)
    
    # Extract user preferences from messages
    message_lower = message.lower()
    if any(word in message_lower for word in ["budget", "cheap", "expensive", "luxury"]):
        if "budget" in message_lower or "cheap" in message_lower:
            memory["user_preferences"]["budget_preference"] = "budget"
        elif "luxury" in message_lower or "expensive" in message_lower:
            memory["user_preferences"]["budget_preference"] = "luxury"
    
    if any(word in message_lower for word in ["adventure", "thrill", "exciting"]):
        memory["user_preferences"]["activity_preference"] = "adventure"
    elif any(word in message_lower for word in ["relaxing", "peaceful", "calm"]):
        memory["user_preferences"]["activity_preference"] = "relaxation"

def get_conversation_context(session_id: str) -> str:
    """Get formatted conversation context for AI"""
    if session_id not in conversation_memory:
        return ""
    
    memory = conversation_memory[session_id]
    context_parts = []
    
    if memory["mentioned_destinations"]:
        context_parts.append(f"Previously discussed destinations: {', '.join(memory['mentioned_destinations'])}")
    
    if memory["user_preferences"]:
        prefs = []
        for key, value in memory["user_preferences"].items():
            prefs.append(f"{key}: {value}")
        context_parts.append(f"User preferences: {'; '.join(prefs)}")
    
    if memory["trip_context"]:
        trip_info = []
        for key, value in memory["trip_context"].items():
            if value and value != "Not selected" and value != "Not specified":
                trip_info.append(f"{key}: {value}")
        if trip_info:
            context_parts.append(f"Current trip planning: {'; '.join(trip_info)}")
    
    if memory["conversation_history"]:
        last_exchange = memory["conversation_history"][-1]
        context_parts.append(f"Last discussed: {last_exchange['assistant']}")
    
    return "\n".join(context_parts) if context_parts else ""

# Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ui_actions: Optional[List[Dict[str, Any]]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    trip_details: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_text: str
    ui_actions: List[Dict[str, Any]] = []
    followup_questions: List[str] = []
    updated_profile: Dict[str, Any] = {}
    analytics_tags: List[str] = []

class RecommendationRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class BookingRequest(BaseModel):
    hotel_id: str
    check_in: str
    check_out: str
    guests: int

# Helper Functions
def get_recommendations_for_query(query: str, query_type: str = "destination"):
    """Get mock recommendations based on query"""
    query_lower = query.lower()
    
    if query_type == "destination":
        recommendations = []
        
        # First try exact matches for destinations and categories
        for dest in MOCK_DESTINATIONS:
            # Check if destination name or state is mentioned
            if (dest["name"].lower() in query_lower or 
                dest["state"].lower() in query_lower or
                any(keyword in dest["name"].lower() or keyword in dest["state"].lower() 
                   for keyword in query_lower.split())):
                recommendations.append(dest)
            # Check if any category matches
            elif any(keyword in category.lower() for category in dest["category"] 
                    for keyword in query_lower.split()):
                recommendations.append(dest)
        
        # If we have specific matches, return them
        if recommendations:
            return recommendations[:3]
        
        # For general queries like "plan a trip", return popular adventure destinations
        if any(word in query_lower for word in ["plan", "trip", "travel", "adventure", "explore", "visit"]):
            # Return top adventure destinations
            adventure_destinations = [
                dest for dest in MOCK_DESTINATIONS 
                if any(category in ["Adventure", "Mountains", "River Rafting", "Paragliding", "Scuba Diving"] 
                      for category in dest["category"])
            ]
            return adventure_destinations[:3] if adventure_destinations else MOCK_DESTINATIONS[:3]
        
        return []
    
    elif query_type == "hotel":
        # Return hotels for mentioned destinations
        recommendations = []
        for hotel in MOCK_HOTELS:
            dest = next((d for d in MOCK_DESTINATIONS if d["id"] == hotel["destination_id"]), None)
            if dest and any(keyword in dest["name"].lower() or keyword in dest["state"].lower() 
                          for keyword in query_lower.split()):
                recommendations.append(hotel)
        return recommendations[:2]  # Return top 2
    
    return []

def create_destination_card(destination):
    """Create a destination card UI action"""
    return {
        "type": "card_add",
        "payload": {
            "id": destination["id"],
            "category": "destination",
            "title": f"{destination['name']}, {destination['country']}",
            "hero_image": destination["hero_image"],
            "pitch": destination["description"][:100] + "...",
            "why_match": destination["why_match"],
            "weather": destination["weather"],
            "highlights": destination["highlights"],
            "coordinates": destination["coordinates"],
            "cta_primary": {"label": "Explore", "action": "explore"},
            "cta_secondary": {"label": "View on map", "action": "map"},
            "motion": {"enter_ms": 260, "stagger_ms": 80}
        }
    }

def create_hotel_card(hotel):
    """Create a hotel card UI action"""
    return {
        "type": "card_add",
        "payload": {
            "id": hotel["id"],
            "category": "hotel",
            "title": hotel["name"],
            "hero_image": hotel["hero_image"],
            "pitch": hotel["pitch"],
            "why_match": hotel["why_match"],
            "rating": hotel["rating"],
            "price_estimate": hotel["price_range"],
            "amenities": hotel["amenities"],
            "location": hotel["location"],
            "cta_primary": {"label": "View rooms", "action": "book"},
            "cta_secondary": {"label": "View details", "action": "details"},
            "motion": {"enter_ms": 260, "stagger_ms": 80}
        }
    }

def generate_contextual_chips(message: str, profile: Dict[str, Any]):
    """Generate contextual chips based on conversation"""
    message_lower = message.lower()
    chips = []
    
    # Travel vibe chips
    if not profile.get("travel_vibe") and any(word in message_lower for word in ["plan", "trip", "travel", "vacation"]):
        chips.extend([
            {"label": "🏃 Adventurous", "value": "adventure"},
            {"label": "🏖 Relaxing", "value": "relax"},
            {"label": "🏛 Cultural", "value": "culture"}
        ])
    
    # Budget chips
    if not profile.get("budget") and any(word in message_lower for word in ["hotel", "stay", "accommodation"]):
        chips.extend([
            {"label": "Budget ($50-100)", "value": "budget"},
            {"label": "Mid-range ($100-200)", "value": "mid_range"},
            {"label": "Luxury ($200+)", "value": "luxury"}
        ])
    
    # Duration chips
    if not profile.get("duration") and any(word in message_lower for word in ["days", "weeks", "trip"]):
        chips.extend([
            {"label": "Weekend (2-3 days)", "value": "weekend"},
            {"label": "Week (5-7 days)", "value": "week"},
            {"label": "Extended (10+ days)", "value": "extended"}
        ])
    
    return chips[:3]  # Return max 3 chips

async def generate_personalized_itinerary(destination, request, user_profile):
    """Generate personalized itinerary based on destination and user context"""
    trip_details = getattr(request, 'trip_details', {}) or {}
    duration = trip_details.get('duration', '7 days')
    budget = trip_details.get('budget', 'mid-range')
    travelers = trip_details.get('travelers', '2 people')
    
    base_response = f"""🗓️ **Perfect! Here's your personalized {destination['name']} adventure itinerary:**

## {destination['name']}, {destination['state']} - {duration} Travel Plan 🌟

### Day 1 – 🛬 Arrival & {destination['name']} Welcome
**Morning:** Arrival and check-in
- **Weather:** {destination['weather']['temp']}, {destination['weather']['condition']}
- **Activity:** {destination['name']} orientation and local setup

**Afternoon:** Explore {destination['highlights'][0] if destination['highlights'] else 'main attractions'}
- **Experience:** {destination['description'][:100]}...
- **Duration:** 3-4 hours

**Evening:** Welcome dinner with local specialties
- **Recommendation:** Try regional cuisine unique to {destination['state']}

### Day 2-3 – 🎯 {destination['category'][0] if destination['category'] else 'Adventure'} Experiences
**Featured Activities:**"""

    # Add specific activities for this destination
    if destination.get('activities'):
        for activity in destination['activities'][:3]:
            base_response += f"\n- **{activity['name']}** - {activity['price']} ({activity['duration']})"
    
    base_response += f"""

### Remaining Days – Customized for Your Group of {travelers}
**Budget Level:** {budget.title()} experience
**Activities tailored to:** {', '.join(destination['category'][:3]) if destination['category'] else 'Adventure and culture'}

**🏨 Accommodation in {destination['name']}:**
- **Luxury:** ₹8,000-15,000/night - Premium properties
- **Mid-Range:** ₹3,000-6,000/night - Comfortable hotels  
- **Budget:** ₹1,000-2,500/night - Clean, safe options

**💰 Estimated Budget for {travelers}:**
- **Premium:** ₹{25000 * (2 if '2' in str(travelers) else 1):,}-{40000 * (2 if '2' in str(travelers) else 1):,}
- **Standard:** ₹{15000 * (2 if '2' in str(travelers) else 1):,}-{25000 * (2 if '2' in str(travelers) else 1):,}
- **Budget:** ₹{8000 * (2 if '2' in str(travelers) else 1):,}-{15000 * (2 if '2' in str(travelers) else 1):,}

*Estimates include accommodation, meals, activities, and local transport for {duration}*"""
    
    return base_response

async def generate_personalized_hotels(destination, request, user_profile):
    """Generate personalized hotel recommendations based on destination and user context"""
    trip_details = getattr(request, 'trip_details', {}) or {}
    budget = trip_details.get('budget', 'mid-range')
    travelers = trip_details.get('travelers', '2 people')
    
    return f"""🏨 **Perfect accommodation recommendations for {destination['name']}, {destination['state']}:**

## Premium Hotels in {destination['name']} 🌟🌟🌟🌟🌟

### Luxury Category (₹10,000-20,000/night)
**The Oberoi {destination['name']}** ⭐⭐⭐⭐⭐
- **Location:** Prime area near {destination['highlights'][0] if destination['highlights'] else 'main attractions'}
- **Best for:** {budget.title()} travelers, perfect for {travelers}
- **Amenities:** Spa, dining, concierge, airport transfer
- **Weather comfort:** Ideal for {destination['weather']['condition'].lower()} conditions

**Heritage Palace Hotel** ⭐⭐⭐⭐⭐  
- **Features:** Traditional {destination['state']} architecture
- **Special:** Cultural immersion in {destination['name']}
- **Activities nearby:** {', '.join(destination['highlights'][:2]) if destination['highlights'] else 'Local attractions'}

## Mid-Range Options (₹4,000-8,000/night) 

### Perfect for {travelers}
**Lemon Tree Premier {destination['name']}** ⭐⭐⭐⭐
- **Location:** Central {destination['name']}, walking distance to attractions
- **Best for:** Families and groups exploring {destination['category'][0] if destination['category'] else 'adventure'}
- **Value:** Great base for {destination['name']} activities

## Budget-Friendly (₹1,500-3,500/night)

### Clean & Comfortable in {destination['name']}
**Local Heritage Guesthouses** ⭐⭐⭐
- **Experience:** Authentic {destination['state']} hospitality
- **Perfect for:** Budget-conscious travelers wanting local culture
- **Bonus:** Insider tips for {destination['name']} exploration

## 🎯 **Recommendations Based on Your {destination['name']} Trip:**

**For {destination['category'][0] if destination['category'] else 'Adventure'} Enthusiasts:** Stay near activity centers
**Weather Consideration:** {destination['weather']['condition']} weather, choose AC/heating accordingly
**Group of {travelers}:** Family rooms and connecting rooms available

**📍 {destination['name']} Location Tips:**
- **Near {destination['highlights'][0] if destination['highlights'] else 'Main Area'}:** Best for sightseeing
- **{destination['state']} Heritage Quarter:** Authentic cultural experience
- **Modern {destination['name']}:** Shopping and dining options

**💡 {destination['name']} Booking Tips:**
- Book 2-3 weeks ahead for {destination['weather']['condition'].lower()} season
- Many hotels offer pickup from nearest airport/station
- Ask about {destination['category'][0] if destination['category'] else 'activity'} packages"""

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Travello.ai API"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Get or create user profile
        user_profile = request.user_profile or {}
        
        # Extract trip context from the request
        trip_context = ""
        if hasattr(request, 'trip_details') and request.trip_details:
            trip_details = request.trip_details
            trip_context = f"""
CURRENT TRIP PLANNING CONTEXT:
- Destination: {trip_details.get('destination', 'Not selected')}
- Travel Dates: {trip_details.get('dates', 'Not selected')}
- Number of Travelers: {trip_details.get('travelers', 'Not specified')}
- Budget Range: {trip_details.get('budget', 'Not specified')}
- Trip Duration: {trip_details.get('duration', 'Not specified')}
"""
        
        # Get conversation context
        conversation_context = get_conversation_context(request.session_id or "default")
        
        # Enhanced system message with context and conversation memory
        contextual_system_message = system_message
        if trip_context:
            contextual_system_message += trip_context + "\nUse this trip information to personalize your recommendations."
        if conversation_context:
            contextual_system_message += f"\n\nCONVERSATION CONTEXT:\n{conversation_context}\n\nReference previous discussions and build upon established preferences."
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=emergent_key,
            session_id=request.session_id or str(uuid.uuid4()),
            system_message=contextual_system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Get conversation context and make responses more natural and progressive
        conversation_context = get_conversation_context(request.session_id or "default")
        message_lower = request.message.lower()
        
        # Check if destination is mentioned in the message
        destination_mentioned = None
        for dest in MOCK_DESTINATIONS:
            if dest["name"].lower() in message_lower or dest["state"].lower() in message_lower:
                destination_mentioned = dest
                break
        
        # Check if this is a booking/planning request - gather essential info first
        if any(phrase in message_lower for phrase in ["book it", "book", "plan it", "let's plan", "create itinerary"]):
            # Extract any destination mentioned
            destination_name = None
            if destination_mentioned:
                destination_name = destination_mentioned['name']
            else:
                # Try to extract destination from message
                for dest in MOCK_DESTINATIONS:
                    if dest["name"].lower() in message_lower:
                        destination_name = dest["name"]
                        destination_mentioned = dest
                        break
            
            # Check what information we already have from trip details
            trip_details = getattr(request, 'trip_details', {}) or {}
            missing_info = []
            
            if not trip_details.get('destination') and not destination_name:
                missing_info.append("destination")
            if not trip_details.get('dates'):
                missing_info.append("travel dates")
            if not trip_details.get('travelers'):
                missing_info.append("number of travelers")
            if not trip_details.get('budget'):
                missing_info.append("budget range")
            if not trip_details.get('duration'):
                missing_info.append("trip duration")
            
            # If we're missing essential information, ask for it
            if missing_info:
                if destination_name:
                    llm_response = f"""Perfect! {destination_name} is an amazing choice! 🎯

To create the perfect itinerary for you, I need a few quick details:

📅 **When are you planning to travel?** (dates or month)
👥 **How many people?** (solo, couple, family, group size)
💰 **What's your budget range?** 
   • Budget-friendly: ₹8K-15K per person
   • Mid-range: ₹15K-25K per person  
   • Premium: ₹25K+ per person
⏰ **How many days?** (weekend, week, extended trip)

Once I have these details, I'll create a personalized {destination_name} adventure just for you! 🚀

You can also use the trip planning bar above to set these details quickly! ⬆️"""
                else:
                    llm_response = f"""I'd love to help you plan something amazing! 🌟

To get started, I need to know:

🗺️ **Where would you like to go?** 
   • Manali (mountains, adventure sports)
   • Rishikesh (river rafting, spirituality)
   • Andaman (scuba diving, beaches)
   • Kerala (backwaters, culture)
   • Rajasthan (desert, heritage)

📅 **When are you traveling?**
👥 **How many people?**
💰 **Budget range?** (₹8K-15K, ₹15K-25K, or ₹25K+ per person)
⏰ **How many days?**

You can tell me like: "5-day Manali trip for 2 people in December, budget ₹20K each" and I'll create the perfect plan! 🎯"""
            
            else:
                # We have all the info, now generate personalized itinerary
                if destination_mentioned or destination_name:
                    dest = destination_mentioned or next((dest for dest in MOCK_DESTINATIONS if dest["name"].lower() == destination_name.lower()), None)
                    if dest:
                        llm_response = await generate_personalized_itinerary(dest, request, user_profile)
                    else:
                        llm_response = "I couldn't find that destination. Could you specify which destination you'd like to book?"
                else:
                    llm_response = "I'd be happy to create your itinerary! Which destination interests you most?"

        # Check if this is a simple/general request that should get direct help
        elif any(phrase in message_lower for phrase in ["plan a trip", "help me plan", "trip planning", "travel plan", "plan my trip"]):
            # Instead of asking questions again, provide immediate help with suggestions
            if destination_mentioned:
                dest = destination_mentioned
                llm_response = f"""Perfect! Let me help you plan an amazing trip to **{dest['name']}**! 🎯

Based on what I know about {dest['name']}, here's what I can suggest:

🗓️ **Quick Trip Planning Options:**
• **Weekend Getaway (2-3 days)** - ₹8,000-15,000 per person
• **Week-long Adventure (5-7 days)** - ₹20,000-35,000 per person  
• **Extended Exploration (10+ days)** - ₹40,000+ per person

🏔️ **Top Experiences in {dest['name']}:**
{' • '.join([f"**{highlight}**" for highlight in dest['highlights'][:3]])}

💡 **To create your perfect itinerary, just tell me:**
- When are you traveling? (dates/month)
- How many people? (solo, couple, family, group)
- Budget preference? (₹8K-15K, ₹15K-25K, ₹25K+)
- How many days?

**Example:** "5-day {dest['name']} trip for 2 people in January, budget ₹20K each" 🚀"""

            else:
                # No specific destination mentioned, suggest popular ones
                llm_response = f"""Absolutely! Let's plan something amazing! 🌟

Since you're open to suggestions, here are **India's hottest adventure destinations** right now:

🏔️ **Mountain Adventures:**
• **Manali** - Perfect for paragliding, river rafting, snow activities (₹15K-25K for 5 days)
• **Rishikesh** - Ultimate for white water rafting, bungee jumping, yoga retreats (₹12K-20K)

🏖️ **Beach & Marine:**
• **Andaman Islands** - World-class scuba diving, pristine beaches (₹25K-40K for 7 days)
• **Pondicherry** - French culture + water sports combo (₹10K-18K for 4 days)

🏜️ **Cultural Adventures:**
• **Rajasthan** - Desert safaris, palace stays, camel rides (₹20K-35K for 7 days)
• **Kerala** - Backwater cruises, spice plantations, houseboat stays (₹18K-30K for 6 days)

💡 **To get your perfect itinerary, just say something like:**
"5-day Manali trip for 2 people in December, budget ₹20K each" 🎯"""

        elif any(phrase in message_lower for phrase in ["itinerary", "detailed plan", "day by day", "schedule"]):
            # User wants detailed planning - provide it immediately
            if destination_mentioned:
                llm_response = await generate_personalized_itinerary(destination_mentioned, request, user_profile)
            else:
                llm_response = f"""I'd love to create a detailed itinerary for you! 📅

**Quick question to get this perfect:** Where are you thinking of going? 

Here are some **instant itinerary options** I can create right now:

🎯 **Popular Choices:**
• **"5-day Manali adventure"** - Paragliding, rafting, snow activities
• **"7-day Kerala backwaters"** - Houseboats, spice tours, cultural immersion  
• **"4-day Rishikesh spiritual adventure"** - Rafting, yoga, Ganga aarti
• **"6-day Andaman marine experience"** - Scuba diving, island hopping, beaches

**Just say something like "7-day Kerala itinerary"** and I'll have it ready in seconds! 🚀"""

        elif any(phrase in message_lower for phrase in ["hotel", "accommodation", "where to stay", "lodging"]):
            # User wants accommodation help
            if destination_mentioned:
                llm_response = await generate_personalized_hotels(destination_mentioned, request, user_profile)
            else:
                llm_response = f"""I'll help you find perfect accommodations! 🏨

**What's your style?**

💎 **Luxury Seeker?**
• Heritage palaces in Rajasthan (₹12K-25K/night)
• Beach resorts in Andaman (₹8K-18K/night)
• Mountain luxury in Manali (₹6K-15K/night)

🎯 **Adventure Focused?**  
• Riverside camps in Rishikesh (₹3K-8K/night)
• Trekking base camps in Himachal (₹2K-6K/night)
• Beach shacks in Goa (₹2K-5K/night)

💰 **Budget Conscious?**
• Clean hostels and guesthouses (₹800-2.5K/night)
• Homestays with local families (₹1K-3K/night)

**Just tell me the destination and your budget** - like "hotels in Manali under ₹5K" and I'll show you the best options! 🎯"""

        else:
            # Regular conversation - make it more natural and helpful
            enhanced_message = f"""User: {request.message}

Context: {conversation_context if conversation_context else 'New conversation'}

Be helpful, natural, and conversational. Provide specific suggestions and actionable advice. Don't ask repetitive questions. Build on the conversation naturally."""
            
            user_message_enhanced = UserMessage(text=enhanced_message)
            llm_response_obj = await chat.send_message(user_message_enhanced)
            llm_response = llm_response_obj.content if hasattr(llm_response_obj, 'content') else str(llm_response_obj)
        
        # Generate UI actions based on message content - make it more inclusive
        ui_actions = []
        message_lower = request.message.lower()
        
        # Check for destination requests - be more inclusive
        if any(word in message_lower for word in [
            "visit", "go to", "travel to", "destination", "plan", "explore", "trip", 
            "adventure", "want to explore", "want to visit", "tell me about", 
            "suggestions", "recommend", "best places", "where to go", "travel"
        ]):
            destinations = get_recommendations_for_query(request.message, "destination")
            
            # If no specific destinations found, show popular adventure destinations
            if not destinations:
                # Show popular Indian adventure destinations for general queries
                popular_destinations = [
                    dest for dest in MOCK_DESTINATIONS 
                    if any(category in ["Adventure", "Mountains", "Beach", "Desert Safari"] 
                          for category in dest["category"])
                ][:3]
                destinations = popular_destinations
            
            for dest in destinations:
                ui_actions.append(create_destination_card(dest))
        
        # Check for hotel requests
        if any(word in message_lower for word in ["hotel", "stay", "accommodation", "sleep", "lodge"]):
            hotels = get_recommendations_for_query(request.message, "hotel")
            for hotel in hotels:
                ui_actions.append(create_hotel_card(hotel))
        
        # Generate contextual chips
        chips = generate_contextual_chips(request.message, user_profile)
        if chips:
            ui_actions.append({
                "type": "prompt",
                "payload": {
                    "text": "Quick choices to help me tailor suggestions:",
                    "chips": chips,
                    "modal": False
                }
            })
        
        # Generate smarter, contextual followup questions that guide information gathering
        followup_questions = []
        
        # If user wants to book/plan but we're missing info, guide them to provide it
        if any(phrase in message_lower for phrase in ["book it", "book", "plan it", "let's plan"]):
            if destination_mentioned:
                dest_name = destination_mentioned['name']
                followup_questions.extend([
                    f"5-day {dest_name} trip for 2 people, budget ₹20K",
                    f"Weekend {dest_name} getaway for couple",
                    f"Family trip to {dest_name} in December"
                ])
            else:
                followup_questions.extend([
                    "5-day Manali trip for 2 people, budget ₹20K",
                    "Weekend Rishikesh adventure for couple",
                    "7-day Kerala backwaters family trip"
                ])
        
        # If asking for general planning help, provide structured examples
        elif any(phrase in message_lower for phrase in ["plan a trip", "help me plan", "recommend"]):
            followup_questions.extend([
                "5-day mountain adventure in Manali",
                "Beach vacation in Andaman Islands",
                "Cultural tour of Rajasthan"
            ])
        
        # If they mention a destination but no details, guide them to be specific
        elif destination_mentioned and not any(word in message_lower for word in ["day", "budget", "people", "travelers"]):
            dest_name = destination_mentioned['name']
            followup_questions.extend([
                f"5-day {dest_name} adventure for ₹20K",
                f"Weekend {dest_name} trip for couple",
                f"Best time to visit {dest_name}?"
            ])
        
        # For other queries, provide helpful examples
        else:
            followup_questions.extend([
                "Plan a 5-day adventure trip",
                "Best destinations for couples",
                "Budget-friendly weekend getaways"
            ])
        
        # Keep it actionable - max 3 questions
        followup_questions = followup_questions[:3]
        
        # Store chat message in database
        chat_message = ChatMessage(
            role="user",
            content=request.message,
            ui_actions=ui_actions
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        assistant_message = ChatMessage(
            role="assistant",
            content=llm_response,
            ui_actions=ui_actions
        )
        await db.chat_messages.insert_one(assistant_message.dict())
        
        # Update conversation memory
        update_conversation_memory(
            session_id=request.session_id or "default",
            message=request.message,
            response=llm_response,
            trip_details=trip_details if hasattr(request, 'trip_details') and request.trip_details else {}
        )
        
        return ChatResponse(
            chat_text=llm_response,
            ui_actions=ui_actions,
            followup_questions=followup_questions[:2],  # Max 2 questions
            updated_profile=user_profile,
            analytics_tags=["chat_response_generated"]
        )
        
    except Exception as e:
        logging.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@api_router.get("/destinations")
async def get_destinations():
    return {"destinations": MOCK_DESTINATIONS}

@api_router.get("/destinations/{destination_id}")
async def get_destination(destination_id: str):
    destination = next((d for d in MOCK_DESTINATIONS if d["id"] == destination_id), None)
    if not destination:
        raise HTTPException(status_code=404, detail="Destination not found")
    return destination

@api_router.get("/hotels")
async def get_hotels(destination_id: Optional[str] = None):
    hotels = MOCK_HOTELS
    if destination_id:
        hotels = [h for h in hotels if h["destination_id"] == destination_id]
    return {"hotels": hotels}

@api_router.get("/hotels/{hotel_id}")
async def get_hotel(hotel_id: str):
    hotel = next((h for h in MOCK_HOTELS if h["id"] == hotel_id), None)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel

@api_router.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    destinations = get_recommendations_for_query(request.query, "destination")
    hotels = get_recommendations_for_query(request.query, "hotel")
    
    return {
        "destinations": destinations,
        "hotels": hotels,
        "query": request.query
    }

@api_router.post("/booking")
async def create_booking(request: BookingRequest):
    hotel = next((h for h in MOCK_HOTELS if h["id"] == request.hotel_id), None)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Mock booking creation
    booking_id = str(uuid.uuid4())
    total_price = hotel["price_range"]["min"] * request.guests
    
    booking_payload = {
        "booking_id": booking_id,
        "hotel": hotel,
        "check_in": request.check_in,
        "check_out": request.check_out,
        "guests": request.guests,
        "total_price": total_price,
        "currency": hotel["price_range"]["currency"],
        "status": "confirmed",
        "cancellation_policy": hotel["cancellation_policy"]
    }
    
    # Store booking in database
    await db.bookings.insert_one(booking_payload)
    
    return {
        "type": "booking_payload",
        "payload": {
            "provider": "Travello.ai",
            "price": {"currency": hotel["price_range"]["currency"], "total": total_price},
            "rooms": [{"type": "Standard", "occupancy": request.guests}],
            "cancellation_policy": hotel["cancellation_policy"],
            "booking_id": booking_id,
            "deep_link": f"https://travello.ai/booking/{booking_id}"
        }
    }

@api_router.get("/chat-history/{session_id}")
async def get_chat_history(session_id: str):
    messages = await db.chat_messages.find({"session_id": session_id}).to_list(100)
    return {"messages": messages}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()