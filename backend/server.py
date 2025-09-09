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
system_message = """You are Travello.ai, an expert Indian adventure travel planner and conversational assistant. You specialize in creating personalized travel experiences across India's most exciting destinations.

PERSONALITY & STYLE:
- Enthusiastic, knowledgeable, and genuinely helpful
- Use adventure travel expertise with local insights
- Be conversational but professional
- Ask clarifying questions to understand user preferences
- Reference specific locations, activities, and experiences

SPECIALIZATION AREAS:
- Adventure activities: Trekking, river rafting, paragliding, scuba diving, bungee jumping
- Indian destinations: Manali, Rishikesh, Andaman, Kerala, Rajasthan, Pondicherry
- Cultural experiences: Local festivals, heritage sites, authentic cuisine
- Accommodation: From luxury resorts to adventure camps and heritage properties

RESPONSE GUIDELINES:
1. Always personalize based on user's trip details (destination, budget, travelers, dates)
2. Provide specific, actionable recommendations with prices in INR
3. Include local tips, best times to visit, and insider knowledge
4. Suggest complementary activities and experiences
5. Be aware of seasonal considerations and weather
6. Reference real tour operators and specific activity providers when possible

CONVERSATION FLOW:
- Start by understanding travel preferences and constraints
- Suggest specific destinations based on interests
- Provide detailed itineraries with day-by-day activities
- Recommend accommodations matching budget and style
- Offer activity bookings with actual pricing
- Share local tips and cultural insights

Remember: You're helping plan real trips to real places with real activities and accommodations. Be specific, helpful, and enthusiastic about India's adventure tourism possibilities."""

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
        # Simple keyword matching for destinations
        recommendations = []
        for dest in MOCK_DESTINATIONS:
            if (any(keyword in dest["name"].lower() or keyword in dest["country"].lower() 
                   for keyword in query_lower.split()) or
                any(keyword in category.lower() for category in dest["category"] 
                   for keyword in query_lower.split())):
                recommendations.append(dest)
        return recommendations[:3]  # Return top 3
    
    elif query_type == "hotel":
        # Return hotels for mentioned destinations
        recommendations = []
        for hotel in MOCK_HOTELS:
            dest = next((d for d in MOCK_DESTINATIONS if d["id"] == hotel["destination_id"]), None)
            if dest and any(keyword in dest["name"].lower() or keyword in dest["country"].lower() 
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
        
        # Check message type and provide tailored responses
        message_lower = request.message.lower()
        
        # Check if destination is mentioned in the message
        destination_mentioned = None
        for dest in MOCK_DESTINATIONS:
            if dest["name"].lower() in message_lower or dest["state"].lower() in message_lower:
                destination_mentioned = dest
                break
        
        # Generate personalized response based on query type
        if any(word in message_lower for word in ["itinerary", "plan", "schedule", "day by day", "detailed plan"]):
            # Create personalized itinerary
            destination = destination_mentioned or (MOCK_DESTINATIONS[0] if hasattr(request, 'trip_details') and request.trip_details.get('destination') else None)
            
            if destination:
                llm_response = await generate_personalized_itinerary(destination, request, user_profile)
            else:
                # Use AI to generate itinerary
                enhanced_message = f"Create a detailed itinerary. Context: {request.message}"
                if trip_context:
                    enhanced_message += f"\n\nTrip Context: {trip_context}"
                
                user_message_enhanced = UserMessage(text=enhanced_message)
                llm_response_obj = await chat.send_message(user_message_enhanced)
                llm_response = llm_response_obj.content if hasattr(llm_response_obj, 'content') else str(llm_response_obj)

        elif any(word in message_lower for word in ["hotel", "accommodation", "stay", "where to stay"]):
            # Create personalized hotel recommendations
            destination = destination_mentioned or (MOCK_DESTINATIONS[0] if hasattr(request, 'trip_details') and request.trip_details.get('destination') else None)
            
            if destination:
                llm_response = await generate_personalized_hotels(destination, request, user_profile)
            else:
                # Use AI to generate hotel recommendations
                enhanced_message = f"Recommend accommodations. Context: {request.message}"
                if trip_context:
                    enhanced_message += f"\n\nTrip Context: {trip_context}"
                
                user_message_enhanced = UserMessage(text=enhanced_message)
                llm_response_obj = await chat.send_message(user_message_enhanced)
                llm_response = llm_response_obj.content if hasattr(llm_response_obj, 'content') else str(llm_response_obj)

        else:
            # Regular AI response with enhanced context
            enhanced_message = f"""User message: {request.message}
            
            Context from conversation: {trip_context if trip_context else 'No trip details selected yet'}
            
            Please provide a helpful, personalized response that guides the user in their travel planning journey."""
            
            user_message_enhanced = UserMessage(text=enhanced_message)
            llm_response_obj = await chat.send_message(user_message_enhanced)
            llm_response = llm_response_obj.content if hasattr(llm_response_obj, 'content') else str(llm_response_obj)
        
        # Generate UI actions based on message content
        ui_actions = []
        message_lower = request.message.lower()
        
        # Check for destination requests
        if any(word in message_lower for word in ["visit", "go to", "travel to", "destination", "plan", "explore", "want to explore", "want to visit", "tell me about"]):
            destinations = get_recommendations_for_query(request.message, "destination")
            for dest in destinations:
                ui_actions.append(create_destination_card(dest))
        
        # Check for hotel requests
        if any(word in message_lower for word in ["hotel", "stay", "accommodation", "sleep"]):
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
        
        # Generate enhanced contextual followup questions
        followup_questions = []
        message_lower = request.message.lower()
        trip_details = getattr(request, 'trip_details', {}) or {}
        
        # Context-aware follow-up questions based on trip planning state and conversation
        if destination_mentioned:
            dest_name = destination_mentioned['name']
            
            if any(word in message_lower for word in ["itinerary", "plan"]):
                followup_questions.extend([
                    f"What specific activities interest you most in {dest_name}?",
                    f"Would you like restaurant recommendations for {dest_name}?",
                    f"Should I include adventure activities in your {dest_name} plan?"
                ])
            elif any(word in message_lower for word in ["hotel", "accommodation"]):
                followup_questions.extend([
                    f"What area of {dest_name} would you prefer to stay in?",
                    f"Do you need family-friendly accommodations in {dest_name}?",
                    f"Would you like hotels near {dest_name}'s main attractions?"
                ])
            else:
                followup_questions.extend([
                    f"Would you like a detailed {dest_name} itinerary?",
                    f"What's your budget range for {dest_name}?",
                    f"How many days are you planning in {dest_name}?"
                ])
        
        # Trip details based questions
        elif not trip_details.get('destination'):
            followup_questions.extend([
                "Which destination interests you most for adventure activities?",
                "Are you looking for mountain adventures or beach experiences?",
                "Would you prefer cultural experiences or outdoor activities?"
            ])
        elif not trip_details.get('budget'):
            followup_questions.extend([
                "What's your preferred budget range for this trip?",
                "Are you looking for luxury, mid-range, or budget travel?",
                "Should I focus on premium experiences or value options?"
            ])
        elif not trip_details.get('travelers'):
            followup_questions.extend([
                "How many people will be traveling?",
                "Is this a solo trip, couple's getaway, or family vacation?",
                "Any special requirements for your travel group?"
            ])
        
        # Activity-based follow-ups
        if any(word in message_lower for word in ["adventure", "activity", "experience"]):
            followup_questions.extend([
                "What level of adventure activities do you prefer?",
                "Are you interested in water sports or mountain activities?",
                "Would you like to include cultural experiences too?"
            ])
        
        # Fallback questions if none added yet
        if not followup_questions:
            if any(word in message_lower for word in ["food", "restaurant", "cuisine"]):
                followup_questions.extend([
                    "Do you have any dietary preferences or restrictions?",
                    "Are you interested in local street food experiences?",
                    "Would you like fine dining or authentic local restaurants?"
                ])
            else:
                followup_questions.extend([
                    "What type of travel experience are you looking for?",
                    "Would you like adventure activities or cultural experiences?",
                    "What's most important to you in this trip?"
                ])
        
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