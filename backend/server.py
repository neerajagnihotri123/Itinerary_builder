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
from agents.conversation_manager import ConversationManager

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
    # Andaman Islands Hotels
    {
        "id": "hotel_andaman_1",
        "destination_id": "andaman_islands",
        "name": "Barefoot at Havelock",
        "hero_image": "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=400&fit=crop",
        "rating": 4.8,
        "price_range": {"min": 6000, "max": 8000, "currency": "INR"},
        "category": "Eco Resort",
        "amenities": ["Beach Access", "Spa", "Restaurant", "Diving Center"],
        "location": "Havelock Island",
        "pitch": "Eco-friendly beachfront resort with pristine beaches",
        "why_match": "Perfect for scuba diving and marine adventures",
        "cancellation_policy": "Free cancellation until 48 hours before check-in"
    },
    {
        "id": "hotel_andaman_2", 
        "destination_id": "andaman_islands",
        "name": "Taj Exotica Resort & Spa",
        "hero_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&h=400&fit=crop",
        "rating": 4.9,
        "price_range": {"min": 15000, "max": 25000, "currency": "INR"},
        "category": "Luxury Resort",
        "amenities": ["Private Beach", "Spa", "Fine Dining", "Water Sports"],
        "location": "Radhanagar Beach, Havelock",
        "pitch": "Luxury beachfront resort with world-class amenities",
        "why_match": "Ultimate luxury for romantic getaways and relaxation",
        "cancellation_policy": "Free cancellation until 72 hours before check-in"
    },
    # Manali Hotels
    {
        "id": "hotel_manali_1",
        "destination_id": "manali_himachal",
        "name": "The Himalayan",
        "hero_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop",
        "rating": 4.7,
        "price_range": {"min": 8000, "max": 15000, "currency": "INR"},
        "category": "Mountain Resort",
        "amenities": ["Mountain Views", "Spa", "Adventure Sports", "Fireplace"],
        "location": "Hadimba Road, Manali",
        "pitch": "Luxury mountain resort with stunning Himalayan views",
        "why_match": "Perfect base for adventure activities and mountain exploration",
        "cancellation_policy": "Free cancellation until 24 hours before check-in"
    },
    {
        "id": "hotel_manali_2",
        "destination_id": "manali_himachal", 
        "name": "Hotel Snow Valley Resorts",
        "hero_image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&h=400&fit=crop",
        "rating": 4.4,
        "price_range": {"min": 3000, "max": 6000, "currency": "INR"},
        "category": "Mid-Range",
        "amenities": ["Valley Views", "Restaurant", "Room Service", "Travel Desk"],
        "location": "Mall Road, Manali",
        "pitch": "Comfortable stay with easy access to main attractions",
        "why_match": "Great value for money with convenient location",
        "cancellation_policy": "Free cancellation until 24 hours before check-in"
    },
    # Rishikesh Hotels
    {
        "id": "hotel_rishikesh_1",
        "destination_id": "rishikesh_uttarakhand",
        "name": "Ananda in the Himalayas",
        "hero_image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=600&h=400&fit=crop",
        "rating": 4.9,
        "price_range": {"min": 20000, "max": 35000, "currency": "INR"},
        "category": "Luxury Spa Resort",
        "amenities": ["Spa", "Yoga", "Meditation", "Gourmet Dining"],
        "location": "Narendra Nagar, Rishikesh",
        "pitch": "World-renowned wellness retreat in the Himalayas",
        "why_match": "Perfect for spiritual and wellness experiences",
        "cancellation_policy": "Free cancellation until 72 hours before check-in"
    },
    {
        "id": "hotel_rishikesh_2",
        "destination_id": "rishikesh_uttarakhand",
        "name": "Camp 5 Elements",
        "hero_image": "https://images.unsplash.com/photo-1504197885-8d8c99d1b3b3?w=600&h=400&fit=crop", 
        "rating": 4.5,
        "price_range": {"min": 2500, "max": 4500, "currency": "INR"},
        "category": "Adventure Camp",
        "amenities": ["Riverside Location", "Adventure Activities", "Bonfire", "Organic Food"],
        "location": "Shivpuri, Rishikesh",
        "pitch": "Riverside adventure camp perfect for rafting enthusiasts",
        "why_match": "Ideal base for white water rafting and adventure sports",
        "cancellation_policy": "Free cancellation until 24 hours before check-in"
    },
    # Kerala Hotels
    {
        "id": "hotel_kerala_1",
        "destination_id": "kerala_backwaters",
        "name": "Kumarakom Lake Resort",
        "hero_image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&h=400&fit=crop",
        "rating": 4.8,
        "price_range": {"min": 12000, "max": 18000, "currency": "INR"},
        "category": "Heritage Resort",
        "amenities": ["Backwater Views", "Ayurvedic Spa", "Traditional Architecture", "Houseboat"],
        "location": "Kumarakom, Kerala",
        "pitch": "Heritage resort on the backwaters with traditional Kerala architecture",
        "why_match": "Perfect for experiencing Kerala's backwater culture",
        "cancellation_policy": "Free cancellation until 48 hours before check-in"
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
        # Initialize the Conversation Manager
        chat_client = LlmChat(
            api_key=emergent_key,
            session_id=request.session_id or str(uuid.uuid4())
        ).with_model("openai", "gpt-4o-mini")
        
        conversation_manager = ConversationManager(chat_client)
        
        # Extract current slots from request
        current_slots = {}
        if request.trip_details:
            current_slots = {
                "destination": request.trip_details.get('destination'),
                "start_date": request.trip_details.get('dates', {}).get('start_date') if isinstance(request.trip_details.get('dates'), dict) else None,
                "end_date": request.trip_details.get('dates', {}).get('end_date') if isinstance(request.trip_details.get('dates'), dict) else None,
                "adults": request.trip_details.get('travelers', {}).get('adults', 2) if isinstance(request.trip_details.get('travelers'), dict) else 2,
                "children": request.trip_details.get('travelers', {}).get('children', 0) if isinstance(request.trip_details.get('travelers'), dict) else 0,
                "budget_per_night": request.trip_details.get('budget', {}).get('per_night') if isinstance(request.trip_details.get('budget'), dict) else None,
                "currency": "INR"
            }
        
        # Process message through conversation manager
        result = await conversation_manager.process_message(
            message=request.message,
            session_id=request.session_id or str(uuid.uuid4()),
            current_slots=current_slots
        )
        
        # Convert to ChatResponse format
        rr_payload = result.get("rr_payload", {})
        
        # Extract UI actions from rr_payload
        ui_actions = rr_payload.get("ui_actions", [])
        
        # Add backward compatibility UI actions based on rr_payload content
        if rr_payload.get("itinerary"):
            # Add destination and hotel cards as UI actions for backward compatibility
            for hotel in rr_payload.get("hotels", []):
                ui_actions.append({
                    "type": "card_add",
                    "payload": {
                        "id": hotel.get("id"),
                        "title": hotel.get("name"),
                        "category": "hotel",
                        "rating": hotel.get("rating"),
                        "price_estimate": {"min": hotel.get("price_estimate", 0), "max": hotel.get("price_estimate", 0)},
                        "pitch": hotel.get("reason", ""),
                        "cta_primary": {"label": "Book Now", "action": "book"},
                        "cta_secondary": {"label": "Details", "action": "details"}
                    }
                })
        
        # Generate contextual questions as UI actions
        contextual_questions = await generate_contextual_questions(request.message, current_slots)
        for question in contextual_questions:
            ui_actions.append({
                "type": "question_chip",
                "payload": {
                    "id": f"q_{len(ui_actions)}",
                    "question": question,
                    "category": "suggestion"
                }
            })
        
        return ChatResponse(
            chat_text=result.get("human_text", "I'd be happy to help you plan your trip!"),
            ui_actions=ui_actions,
            updated_profile=request.user_profile or {},
            followup_questions=[],
            analytics_tags=["multi_agent_response"]
        )
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return ChatResponse(
            chat_text="I apologize, but I encountered an issue. Could you please try rephrasing your request?",
            ui_actions=[],
            updated_profile=request.user_profile or {},
            followup_questions=[],
            analytics_tags=["error"]
        )

async def generate_contextual_questions(message: str, slots: Dict[str, Any]) -> List[str]:
    """Generate contextual questions based on the current conversation state"""
    message_lower = message.lower()
    questions = []
    
    # Questions based on message content
    if any(word in message_lower for word in ["accommodation", "hotel", "stay"]):
        if slots.get("destination"):
            dest_name = slots["destination"]
            questions = [
                f"Best restaurants in {dest_name}",
                f"Top activities in {dest_name}",
                f"Transportation to {dest_name}",
                f"Best time to visit {dest_name}"
            ]
        else:
            questions = [
                "Budget vs luxury hotels",
                "Hotel booking tips",
                "Best areas to stay",
                "Family-friendly accommodations"
            ]
    
    elif slots.get("destination"):
        dest_name = slots["destination"]
        questions = [
            f"Hotels in {dest_name}",
            f"Best activities in {dest_name}",
            f"Food recommendations in {dest_name}",
            f"Transportation options to {dest_name}"
        ]
    
    elif any(word in message_lower for word in ["plan", "trip", "travel"]):
        questions = [
            "Best adventure destinations",
            "Budget travel tips",
            "Solo vs group travel",
            "Best travel season in India"
        ]
    
    else:
        questions = [
            "Plan a weekend getaway",
            "Adventure vs relaxation trips",
            "Popular destinations right now",
            "Budget-friendly destinations"
        ]
    
    return questions[:4]  # Return max 4 questions

# Other API endpoints
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
        
        # Generate UI actions based on message content - make it more comprehensive
        ui_actions = []
        message_lower = request.message.lower()
        
        # Check for accommodation/hotel requests - priority handling
        accommodation_requested = any(word in message_lower for word in ["accommodation", "hotel", "stay", "sleep", "lodge", "resort"])
        
        if accommodation_requested:
            # ONLY show hotel cards when accommodation is explicitly requested
            hotels = []
            if destination_mentioned:
                # Get hotels specifically for the mentioned destination
                for hotel in MOCK_HOTELS:
                    if hotel["destination_id"] == destination_mentioned["id"]:
                        hotels.append(hotel)
            else:
                # Get hotels from context or popular destinations
                hotels = MOCK_HOTELS[:3]  # Show top 3 hotels
            
            for hotel in hotels:
                ui_actions.append(create_hotel_card(hotel))
            
            print(f"🏨 Generated {len(hotels)} hotel cards for accommodation request")
        
        # Check for destination requests - ONLY if accommodation was NOT requested
        elif not accommodation_requested and any(word in message_lower for word in [
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
            
            print(f"🗺️ Generated {len(destinations)} destination cards for destination request")
        
        # Add contextual "You might want to ask" question cards based on conversation context
        contextual_questions = []
        
        # Get conversation history to make questions more dynamic
        memory = conversation_memory.get(request.session_id or "default", {})
        mentioned_destinations = memory.get("mentioned_destinations", set())
        user_preferences = memory.get("user_preferences", {})
        
        # More sophisticated contextual question generation
        if any(word in message_lower for word in ["accommodation", "hotel", "stay"]):
            if destination_mentioned:
                dest_name = destination_mentioned['name']
                # Dynamic questions based on what hasn't been asked yet
                base_questions = [
                    f"Best restaurants in {dest_name}",
                    f"Top activities in {dest_name}",
                    f"Best time to visit {dest_name}",
                    f"Transportation to {dest_name}",
                    f"Plan a 5-day {dest_name} itinerary"
                ]
                contextual_questions = base_questions
            else:
                contextual_questions = [
                    "Compare luxury vs budget hotels",
                    "Best hotel booking platforms",
                    "Hotel amenities that matter most",
                    "Safe accommodation tips for solo travelers"
                ]
        
        elif destination_mentioned:
            dest_name = destination_mentioned['name']
            # Vary questions based on what's been discussed before
            potential_questions = [
                f"Hotels and stays in {dest_name}",
                f"Must-try food in {dest_name}",
                f"Best activities in {dest_name}",
                f"How to reach {dest_name}",
                f"Plan a trip to {dest_name}",
                f"Best season for {dest_name}",
                f"Budget for {dest_name} vacation",
                f"Local culture in {dest_name}"
            ]
            # Select questions that haven't been covered
            contextual_questions = potential_questions[:4]
        
        elif any(word in message_lower for word in ["plan", "trip", "travel", "itinerary"]):
            # Questions for trip planning context
            if mentioned_destinations:
                recent_dest = list(mentioned_destinations)[-1] if mentioned_destinations else None
                if recent_dest:
                    contextual_questions = [
                        f"Best hotels in {recent_dest}",
                        f"Create {recent_dest} itinerary",
                        f"Things to pack for {recent_dest}",
                        f"Local transportation in {recent_dest}"
                    ]
                else:
                    contextual_questions = [
                        "Best adventure destinations in India",
                        "Budget-friendly destinations",
                        "Solo vs group travel destinations",
                        "Romantic getaway destinations"
                    ]
            else:
                contextual_questions = [
                    "Popular destinations for first-time travelers",
                    "Adventure vs cultural destinations",
                    "Weekend vs extended trip planning",
                    "Solo travel safety tips"
                ]
        
        elif any(word in message_lower for word in ["food", "restaurant", "eat", "cuisine"]):
            if destination_mentioned:
                dest_name = destination_mentioned['name']
                contextual_questions = [
                    f"Best street food in {dest_name}",
                    f"Fine dining options in {dest_name}",
                    f"Local specialties of {dest_name}",
                    f"Food safety tips for {dest_name}"
                ]
            else:
                contextual_questions = [
                    "Best food destinations in India",
                    "Street food safety tips",
                    "Vegetarian travel options",
                    "Regional Indian cuisines to try"
                ]
        
        elif any(word in message_lower for word in ["activity", "adventure", "things to do"]):
            if destination_mentioned:
                dest_name = destination_mentioned['name']
                contextual_questions = [
                    f"Adventure sports in {dest_name}",
                    f"Cultural experiences in {dest_name}",
                    f"Family activities in {dest_name}",
                    f"Best photo spots in {dest_name}"
                ]
            else:
                contextual_questions = [
                    "Adventure destinations in India",
                    "Cultural heritage sites",
                    "Family-friendly activities",
                    "Photography hotspots"
                ]
        
        else:
            # Default contextual questions when no specific topic detected
            if mentioned_destinations:
                recent_dest = list(mentioned_destinations)[-1] if mentioned_destinations else None
                if recent_dest:
                    contextual_questions = [
                        f"Plan a detailed {recent_dest} trip",
                        f"Hotels in {recent_dest}",
                        f"Best activities in {recent_dest}",
                        "Compare with other destinations"
                    ]
            else:
                contextual_questions = [
                    "Plan a weekend getaway",
                    "Best destinations for your budget",
                    "Adventure vs relaxation trips",
                    "Popular destinations right now"
                ]
        
        # Add contextual questions as UI actions
        for question in contextual_questions[:5]:  # Limit to 5 questions
            ui_actions.append({
                "type": "question_chip",
                "payload": {
                    "id": f"q_{hash(question)}",
                    "question": question,
                    "category": "suggestion"
                }
            })
        
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