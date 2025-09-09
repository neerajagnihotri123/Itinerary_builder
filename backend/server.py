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

# Mock Travel Data
MOCK_DESTINATIONS = [
    {
        "id": "paris_france",
        "name": "Paris",
        "country": "France",
        "coordinates": {"lat": 48.8566, "lng": 2.3522},
        "hero_image": "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=800&h=400&fit=crop",
        "category": ["Culture & History", "Urban", "Romance"],
        "weather": {"temp": "18°C", "condition": "Partly Cloudy"},
        "description": "The City of Light captivates with its iconic landmarks, world-class museums, and charming boulevards.",
        "highlights": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Seine River Cruises"],
        "why_match": "Perfect for culture lovers seeking romance and history"
    },
    {
        "id": "tokyo_japan",
        "name": "Tokyo",
        "country": "Japan",
        "coordinates": {"lat": 35.6762, "lng": 139.6503},
        "hero_image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&h=400&fit=crop",
        "category": ["Urban", "Culture & History", "Adventure"],
        "weather": {"temp": "22°C", "condition": "Clear"},
        "description": "A fascinating blend of ultra-modern technology and traditional culture in Japan's vibrant capital.",
        "highlights": ["Shibuya Crossing", "Tokyo Skytree", "Senso-ji Temple", "Tsukiji Fish Market"],
        "why_match": "Ideal for urban explorers and culture enthusiasts"
    },
    {
        "id": "bali_indonesia",
        "name": "Bali",
        "country": "Indonesia",
        "coordinates": {"lat": -8.3405, "lng": 115.0920},
        "hero_image": "https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?w=800&h=400&fit=crop",
        "category": ["Beach", "Nature", "Adventure"],
        "weather": {"temp": "28°C", "condition": "Sunny"},
        "description": "Tropical paradise with stunning beaches, lush rice terraces, and rich cultural heritage.",
        "highlights": ["Ubud Rice Terraces", "Seminyak Beach", "Mount Batur", "Tanah Lot Temple"],
        "why_match": "Perfect for beach lovers and nature enthusiasts"
    },
    {
        "id": "new_york_usa",
        "name": "New York",
        "country": "USA",
        "coordinates": {"lat": 40.7128, "lng": -74.0060},
        "hero_image": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800&h=400&fit=crop",
        "category": ["Urban", "Culture & History", "Adventure"],
        "weather": {"temp": "15°C", "condition": "Cloudy"},
        "description": "The city that never sleeps offers endless possibilities with world-class attractions and dining.",
        "highlights": ["Times Square", "Central Park", "Statue of Liberty", "Broadway Shows"],
        "why_match": "Great for urban adventures and cultural experiences"
    },
    {
        "id": "santorini_greece",
        "name": "Santorini",
        "country": "Greece",
        "coordinates": {"lat": 36.3932, "lng": 25.4615},
        "hero_image": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800&h=400&fit=crop",
        "category": ["Beach", "Romance", "Culture & History"],
        "weather": {"temp": "24°C", "condition": "Sunny"},
        "description": "Iconic Greek island famous for its white-washed buildings, blue domes, and stunning sunsets.",
        "highlights": ["Oia Sunset", "Red Beach", "Akrotiri Archaeological Site", "Wine Tasting"],
        "why_match": "Perfect for romantic getaways and beach relaxation"
    },
    {
        "id": "goa_india",
        "name": "Goa",
        "country": "India",
        "coordinates": {"lat": 15.2993, "lng": 74.1240},
        "hero_image": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&h=400&fit=crop",
        "category": ["Beach", "Culture & History", "Relaxation"],
        "weather": {"temp": "32°C", "condition": "Sunny"},
        "description": "India's beach paradise with golden sands, Portuguese heritage, and vibrant nightlife.",
        "highlights": ["Baga Beach", "Old Goa Churches", "Spice Plantations", "Dudhsagar Falls"],
        "why_match": "Perfect for beach lovers seeking culture and relaxation"
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
        
        # Get LLM response
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
        
        # Generate followup questions
        followup_questions = []
        if not user_profile.get("travel_dates"):
            followup_questions.append("When are you planning to travel?")
        if not user_profile.get("budget"):
            followup_questions.append("Do you have a budget range in mind?")
        
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