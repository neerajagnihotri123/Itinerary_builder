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
system_message = """You are Travello.ai, an expert travel planner and conversational assistant integrated into a modern travel planning application. You help users plan amazing trips worldwide by providing contextually relevant recommendations.

CURRENT APPLICATION CONTEXT:
- Users interact with you through a split-screen interface (chat + visual map/cards)
- When users mention destinations, visual destination cards appear automatically
- A trip planning bar appears when users want to plan trips (destination, dates, travelers, budget)
- After trip details are filled, a personalization questionnaire helps create custom itineraries
- You should acknowledge and refer to the visual elements users can see

YOUR RESPONSE STYLE:
1. Be conversational, enthusiastic, and contextually aware
2. Reference the visual cards/map when destinations are mentioned: "I can see you're looking at the Paris card that just appeared!"
3. Guide users through the trip planning flow naturally
4. When trip planning bar appears, acknowledge it: "Perfect! I can see the trip planning bar is now active above."
5. Be aware of what stage the user is in (browsing, planning, personalizing)
6. Keep responses concise but helpful - the visual elements do the heavy lifting

CONTEXTUAL RESPONSES:
- When showing destination cards: Reference them and encourage exploration
- When trip planning bar appears: Guide users to fill in the details
- When personalization is triggered: Explain what's happening next
- Always be aware of the current conversation flow and UI state"""

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

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Travello.ai API"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Initialize chat session
        session_id = request.session_id or str(uuid.uuid4())
        user_profile = request.user_profile or {}
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Enhanced response generation with structured content
        message_lower = request.message.lower()
        
        # Check if destination is mentioned in the message
        destination_mentioned = None
        for dest in MOCK_DESTINATIONS:
            if dest["name"].lower() in message_lower or dest["state"].lower() in message_lower:
                destination_mentioned = f"{dest['name']}, {dest['state']}"
                break
        
        if any(word in message_lower for word in ["itinerary", "plan", "schedule", "day by day", "detailed plan"]):
            llm_response = f"""🗓️ **Perfect! Let me create a detailed {destination_mentioned if destination_mentioned else '7-day'} adventure itinerary for you:**

## {destination_mentioned if destination_mentioned else 'Adventure'} Complete Travel Plan 🌟

### Day 1 – 🛬 Arrival & Welcome
**Morning:** Check-in at premium accommodation
- **Recommended Hotels:** Taj MG Road or The Oberoi (luxury) | Lemon Tree Premier (mid-range)
- **Activity:** City orientation walk, local SIM card, currency exchange

**Afternoon:** Explore local markets and cultural sites
- **Must-visit:** Main cultural district and heritage walk
- **Local Experience:** Traditional welcome lunch at authentic restaurant

**Evening:** Sunset views and welcome dinner
- **Restaurant:** Local specialty cuisine experience
- **Tip:** Try regional delicacies and interact with locals

### Day 2 – 🏰 Heritage & Culture
**Morning:** Historical landmarks and palaces
- **Activities:** Guided heritage tour, photo opportunities
- **Duration:** 3-4 hours with professional guide

**Afternoon:** Art galleries and cultural centers  
- **Experience:** Traditional craft workshops, local art scene
- **Shopping:** Authentic handicrafts and souvenirs

**Evening:** Cultural performance or cooking class
- **Options:** Classical dance show, food tour, or hands-on cooking

### Day 3 – 🌿 Nature & Adventure
**Full Day Adventure Experience:**
- **Morning:** Nature park or botanical gardens
- **Afternoon:** Adventure activities (based on location)
- **Equipment:** All safety gear provided
- **Meals:** Packed adventure lunch included

### Days 4-7 – Customized Based on Your Interests 🎯

**Would you like me to customize the remaining days based on:**
- Adventure activities (trekking, water sports, wildlife)
- Cultural immersion (festivals, workshops, local life)
- Relaxation (spa, beaches, wellness)
- Food exploration (cooking classes, market tours, fine dining)

**🏨 Accommodation Recommendations:**
- **Luxury:** ₹8,000-15,000/night - Premium hotels with full amenities
- **Mid-Range:** ₹3,000-6,000/night - Comfortable hotels with good service  
- **Budget:** ₹1,000-2,500/night - Clean, safe options with basic amenities

**💰 Estimated Budget (per person):**
- **Premium Experience:** ₹25,000-40,000 for 7 days
- **Standard Experience:** ₹15,000-25,000 for 7 days
- **Budget Experience:** ₹8,000-15,000 for 7 days

*All estimates include accommodation, meals, activities, and local transport*"""

        elif any(word in message_lower for word in ["hotel", "accommodation", "stay", "where to stay"]):
            llm_response = f"""🏨 **Perfect accommodation recommendations for {destination_mentioned if destination_mentioned else 'your destination'}:**

## Premium Hotels & Resorts 🌟🌟🌟🌟🌟

### Luxury Category (₹10,000-20,000/night)
**The Oberoi** ⭐⭐⭐⭐⭐
- **Features:** Spa, rooftop dining, concierge service
- **Best for:** Honeymoon, luxury travel, business
- **Amenities:** Pool, gym, multiple restaurants, airport transfer

**Taj Hotels** ⭐⭐⭐⭐⭐  
- **Features:** Heritage property, premium location
- **Best for:** Cultural enthusiasts, luxury seekers
- **Special:** Traditional architecture with modern amenities

## Mid-Range Options (₹4,000-8,000/night) 

### Boutique Properties
**Lemon Tree Premier** ⭐⭐⭐⭐
- **Features:** Contemporary design, central location
- **Best for:** Families, business travelers
- **Amenities:** Restaurant, fitness center, business center

**Local Heritage Hotels** ⭐⭐⭐⭐
- **Features:** Converted palaces/mansions with character
- **Best for:** Cultural experience, unique stays
- **Special:** Authentic architecture, local hospitality

## Budget-Friendly (₹1,500-3,500/night)

### Clean & Comfortable
**OYO Premium Properties** ⭐⭐⭐
- **Features:** Standardized quality, good locations
- **Best for:** Budget travelers, solo travel
- **Amenities:** AC, WiFi, clean bathrooms

**Local Guesthouses** ⭐⭐⭐
- **Features:** Family-run, authentic experience  
- **Best for:** Cultural immersion, meeting locals
- **Special:** Home-cooked meals, insider tips

## 🎯 **My Top Recommendations Based on Travel Style:**

**For Adventure Travelers:** Mid-range hotels near activity centers
**For Cultural Enthusiasts:** Heritage properties in old city areas
**For Families:** Resort-style hotels with amenities and space
**For Solo Travelers:** Boutique hotels in safe, central locations
**For Budget Travelers:** Clean guesthouses in local neighborhoods

**📍 Location Tips:**
- **City Center:** Best for sightseeing and restaurants
- **Heritage Quarter:** Authentic experience, walking distance to attractions  
- **Modern District:** Shopping, nightlife, business facilities
- **Outskirts:** Peaceful, often better value, may need transport

**💡 Booking Tips:**
- Book 2-3 weeks in advance for better rates
- Check for festival dates (prices increase significantly)
- Many hotels offer airport pickup - ask when booking
- Read recent reviews for current condition updates"""

        else:
            # Regular AI response with enhanced formatting
            llm_response = await chat.send_message(user_message)
        
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
        
        # Generate contextual followup questions based on conversation
        followup_questions = []
        message_lower = request.message.lower()
        
        # Context-aware follow-up questions
        if any(word in message_lower for word in ["destination", "place", "visit", "go to"]):
            if not user_profile.get("travel_dates"):
                followup_questions.append("When are you planning to travel?")
            if not user_profile.get("travel_style"):
                followup_questions.append("Are you looking for adventure or relaxation?")
                
        elif any(word in message_lower for word in ["plan", "trip", "vacation"]):
            if not user_profile.get("duration"):
                followup_questions.append("How many days are you planning to stay?")
            if not user_profile.get("budget"):
                followup_questions.append("What's your budget range?")
                
        elif any(word in message_lower for word in ["hotel", "stay", "accommodation"]):
            followup_questions.append("What type of accommodation do you prefer?")
            followup_questions.append("Any specific amenities you're looking for?")
            
        elif any(word in message_lower for word in ["food", "restaurant", "eat"]):
            followup_questions.append("Do you have any dietary preferences?")
            followup_questions.append("Are you interested in local cuisine or international food?")
            
        elif any(word in message_lower for word in ["activity", "do", "see", "experience"]):
            followup_questions.append("Are you interested in cultural experiences?")
            followup_questions.append("Do you prefer indoor or outdoor activities?")
            
        # Default fallback questions if no specific context
        if not followup_questions:
            if not user_profile.get("travel_dates"):
                followup_questions.append("When are you planning to travel?")
            if not user_profile.get("budget"):
                followup_questions.append("Do you have a budget range in mind?")
            if not user_profile.get("travel_companions"):
                followup_questions.append("Are you traveling solo or with others?")
            if not user_profile.get("interests"):
                followup_questions.append("What interests you most when traveling?")
        
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