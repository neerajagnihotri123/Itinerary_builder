"""
Travello.ai Backend - Clean Agent-Based Architecture
Multi-agent travel planning system with event-driven pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timezone, timedelta
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with CORS
app = FastAPI(title="Travello.ai Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://ai-concierge-6.preview.emergentagent.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import agents
from agents.profile_intake_agent import ProfileIntakeAgent
from agents.persona_classification_agent import PersonaClassificationAgent
from agents.itinerary_generation_agents import AdventurerAgent, BalancedAgent, LuxuryAgent
from agents.customization_agent import CustomizationAgent
from agents.pricing_agent import PricingAgent
from agents.external_booking_agent import ExternalBookingAgent
from agents.sustainability_seasonality_agent import SustainabilitySeasonalityAgent
from utils.context_store import ContextStore
from utils.event_bus import EventBus
from models.schemas import *

# Initialize context store and event bus
context_store = ContextStore()
event_bus = EventBus()

# Initialize agents
profile_intake = ProfileIntakeAgent(context_store, event_bus)
persona_classifier = PersonaClassificationAgent(context_store, event_bus)
adventurer_agent = AdventurerAgent(context_store, event_bus)
balanced_agent = BalancedAgent(context_store, event_bus)
luxury_agent = LuxuryAgent(context_store, event_bus)
customization_agent = CustomizationAgent(context_store, event_bus)
pricing_agent = PricingAgent(context_store, event_bus)
booking_agent = ExternalBookingAgent(context_store, event_bus)
sustainability_agent = SustainabilitySeasonalityAgent(context_store, event_bus)

# Register agents with event bus
event_bus.register_agent("profile_intake", profile_intake)
event_bus.register_agent("persona_classifier", persona_classifier)
event_bus.register_agent("adventurer", adventurer_agent)
event_bus.register_agent("balanced", balanced_agent)
event_bus.register_agent("luxury", luxury_agent)
event_bus.register_agent("customization", customization_agent)
event_bus.register_agent("pricing", pricing_agent)
event_bus.register_agent("booking", booking_agent)
event_bus.register_agent("sustainability", sustainability_agent)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Travello.ai Backend",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint - entry point for user interactions"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        user_message = request.message
        
        logger.info(f"🎯 Chat request from session {session_id}: {user_message}")
        
        # Store user message in context
        context_store.add_message(session_id, "user", user_message)
        
        # Route to Profile Intake Agent first
        response = await profile_intake.process_message(session_id, user_message)
        
        logger.info(f"✉️ Chat response: {response.chat_text[:100]}...")
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return ChatResponse(
            chat_text="I apologize, but I'm experiencing some technical difficulties. Please try again.",
            ui_actions=[],
            updated_profile={},
            followup_questions=[],
            analytics_tags=["error"]
        )

@app.post("/api/profile-intake")
async def profile_intake_endpoint(request: ProfileIntakeRequest):
    """Profile intake endpoint for collecting traveler preferences"""
    try:
        session_id = request.session_id
        responses = request.responses
        
        logger.info(f"🏷️ Profile intake for session {session_id}")
        
        # Process profile responses
        result = await profile_intake.process_profile_responses(session_id, responses)
        
        return result
        
    except Exception as e:
        logger.error(f"Profile intake error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/persona-classification")
async def persona_classification_endpoint(request: PersonaClassificationRequest):
    """Persona classification endpoint with simplified processing"""
    try:
        session_id = request.session_id
        trip_details = request.trip_details
        profile_data = request.profile_data
        
        logger.info(f"🎭 Persona classification for session {session_id}")
        logger.info(f"🎭 Profile data: {profile_data}")
        
        # Simple persona classification based on profile data
        persona_tags = []
        persona_type = "balanced_traveler"
        
        # Analyze vacation style
        vacation_style = profile_data.get("vacation_style", "")
        if "adventurous" in str(vacation_style).lower():
            persona_tags.extend(["adventure_seeker", "outdoor_enthusiast"])
            persona_type = "adventurer"
        elif "relaxing" in str(vacation_style).lower():
            persona_tags.extend(["relaxation_focused", "wellness_oriented"])
            persona_type = "luxury_connoisseur"
        else:
            persona_tags.extend(["balanced_traveler", "flexible"])
            persona_type = "balanced_traveler"
        
        # Analyze experience type
        experience_type = profile_data.get("experience_type", "")
        if "nature" in str(experience_type).lower():
            persona_tags.extend(["nature_lover", "outdoor_activities"])
        elif "culture" in str(experience_type).lower():
            persona_tags.extend(["cultural_explorer", "heritage_interested"])
        
        # Analyze accommodation preferences
        accommodation = profile_data.get("accommodation", [])
        if isinstance(accommodation, list):
            if "luxury_hotels" in accommodation:
                persona_tags.append("luxury_oriented")
                persona_type = "luxury_connoisseur"
            elif "budget_hotels" in accommodation or "hostels" in accommodation:
                persona_tags.append("budget_conscious")
                persona_type = "budget_backpacker"
        
        # Remove duplicates
        persona_tags = list(set(persona_tags))
        
        logger.info(f"✅ Classified as: {persona_type} with tags: {persona_tags}")
        
        return PersonaClassificationResponse(
            persona_type=PersonaType(persona_type),
            persona_tags=persona_tags,
            confidence=0.85,
            ui_actions=[]
        )
        
    except Exception as e:
        logger.error(f"Persona classification error: {e}")
        return PersonaClassificationResponse(
            persona_type=PersonaType.BALANCED_TRAVELER,
            persona_tags=["general_traveler"],
            confidence=0.5,
            ui_actions=[]
        )

@app.post("/api/generate-itinerary")
async def generate_itinerary_endpoint(request: ItineraryGenerationRequest):
    """Generate itinerary variants endpoint with direct JSON response"""
    try:
        session_id = request.session_id
        trip_details = request.trip_details
        persona_tags = request.persona_tags
        
        logger.info(f"🗓️ Generating LLM-powered itinerary variants for session {session_id}")
        logger.info(f"🗓️ Trip details: {trip_details}")
        logger.info(f"🗓️ Persona tags: {persona_tags}")
        
        # Use profile intake agent to generate itinerary content via LLM
        destination = trip_details.get("destination", "Unknown")
        start_date = trip_details.get("start_date", "2024-12-15")
        end_date = trip_details.get("end_date", "2024-12-20") 
        adults = trip_details.get("adults", 2)
        budget = trip_details.get("budget_per_night", 8000)
        
        # Calculate trip duration
        from datetime import datetime, timedelta
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days = (end - start).days
        except:
            days = 5
        
        # Generate comprehensive itinerary using LLM with multiple activities per day
        itinerary_prompt = f"""
        Generate 3 detailed travel itinerary variants for {destination} ({days} days, {adults} travelers, ₹{budget} budget):

        1. ADVENTURER: Focus on outdoor activities and adventure sports
        2. BALANCED: Mix of sightseeing, culture, and activities  
        3. LUXURY: Premium experiences and fine dining

        For each variant, provide:
        - Title and description
        - 4 key highlights
        - Daily cost estimate

        IMPORTANT: Each day should have 3-4 activities at different times (morning, afternoon, evening) to create a full-day experience.

        Keep response concise and in JSON format:
        {{
          "adventurer": {{
            "title": "Adventure Explorer", 
            "description": "...", 
            "price": {budget * days},
            "highlights": ["Activity1", "Activity2", "Activity3", "Activity4"]
          }},
          "balanced": {{
            "title": "Balanced Explorer", 
            "description": "...", 
            "price": {int(budget * days * 0.8)},
            "highlights": ["Activity1", "Activity2", "Activity3", "Activity4"]
          }},
          "luxury": {{
            "title": "Luxury Experience", 
            "description": "...", 
            "price": {int(budget * days * 1.5)},
            "highlights": ["Activity1", "Activity2", "Activity3", "Activity4"]
          }}
        }}
        """
        
        # Get LLM response with timeout
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import asyncio
        
        try:
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=session_id,
                system_message="You are a travel expert. Generate concise itinerary variants in valid JSON format."
            ).with_model("openai", "gpt-4o-mini")
            
            user_msg = UserMessage(text=itinerary_prompt)
            
            # Add timeout to LLM call
            llm_response = await asyncio.wait_for(
                llm_client.send_message(user_msg), 
                timeout=15.0  # 15 second timeout
            )
            
            # Parse LLM response quickly
            import json
            import re
            
            json_text = llm_response
            if '```json' in json_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            elif '```' in json_text:
                json_match = re.search(r'```\s*(.*?)\s*```', json_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
            
            llm_data = json.loads(json_text.strip())
            logger.info(f"✅ LLM generated itinerary data successfully")
            
            # Build structured variants from LLM data (frontend compatible format)
            variants = []
            for variant_key, variant_data in llm_data.items():
                if variant_key in ['adventurer', 'balanced', 'luxury']:
                    # Create detailed itinerary structure for frontend
                    detailed_itinerary = []
                    for day_num in range(1, days + 1):
                        day_date = (datetime.fromisoformat(start_date) + timedelta(days=day_num-1)).isoformat()[:10]
                        detailed_itinerary.append({
                            "day": day_num,
                            "date": day_date,
                            "title": f"Day {day_num}: {variant_data.get('highlights', ['Experience'])[min(day_num-1, len(variant_data.get('highlights', []))-1)]}",
                            "activities": [
                                {
                                    "time": "10:00 AM",
                                    "title": f"{variant_data.get('highlights', ['Activity'])[0]} Experience" if day_num == 1 else f"Day {day_num} Adventure",
                                    "description": f"Enjoy {variant_data.get('highlights', ['activities'])[min(day_num-1, len(variant_data.get('highlights', []))-1)].lower()} in {destination}",
                                    "location": destination,
                                    "category": "adventure" if variant_key == 'adventurer' else "sightseeing",
                                    "duration": "4 hours"
                                }
                            ]
                        })
                    
                    variants.append({
                        "id": f"{variant_key}_{destination.lower().replace(' ', '_')}",
                        "title": variant_data.get("title", f"{variant_key.title()} Experience"),
                        "description": variant_data.get("description", f"Great {variant_key} experience in {destination}"),
                        "persona": variant_key,  # Frontend expects 'persona' not 'type'
                        "days": days,
                        "price": variant_data.get("price", 20000),  # Frontend expects 'price' not 'total_cost'
                        "total_activities": days * 2,
                        "activity_types": variant_data.get("highlights", ["Sightseeing", "Culture"]),
                        "highlights": variant_data.get("highlights", ["Experience 1", "Experience 2", "Experience 3", "Experience 4"]),
                        "recommended": variant_key == 'adventurer',  # Default to adventurer as recommended
                        "itinerary": detailed_itinerary  # Frontend expects 'itinerary' not 'daily_itinerary'
                    })
            
            logger.info(f"✅ Built {len(variants)} complete itinerary variants from LLM data")
            
        except asyncio.TimeoutError:
            logger.warning("LLM call timed out, using fallback variants")
            variants = None
        except Exception as e:
            logger.error(f"LLM processing error: {e}, using fallback")
            variants = None
        
        # Use fallback variants if LLM failed (frontend compatible format)
        if variants is None:
            fallback_variants = [
                {
                    "id": f"adventurer_{destination.lower()}",
                    "title": "Adventure Explorer",
                    "description": f"Thrilling outdoor experiences and adventure sports in {destination}",
                    "persona": "adventurer",
                    "days": days,
                    "price": 25000,
                    "total_activities": 12,
                    "activity_types": ["Adventure Sports", "Water Sports", "Trekking", "Local Culture"],
                    "highlights": ["Paragliding", "Scuba Diving", "Beach Trek", "Local Markets"],
                    "recommended": True,
                    "itinerary": [
                        {
                            "day": 1,
                            "date": start_date,
                            "title": f"Arrival & {destination} Adventure",
                            "activities": [
                                {
                                    "time": "10:00 AM",
                                    "title": "Airport Transfer",
                                    "description": "Comfortable transfer to adventure resort",
                                    "location": destination,
                                    "category": "transportation",
                                    "duration": "1 hour"
                                },
                                {
                                    "time": "2:00 PM",
                                    "title": "Adventure Sports Introduction",
                                    "description": "Orientation and first adventure activity",
                                    "location": f"{destination} Adventure Zone",
                                    "category": "adventure",
                                    "duration": "3 hours"
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": f"balanced_{destination.lower()}",
                    "title": "Balanced Explorer",
                    "description": f"Perfect mix of adventure, culture, and relaxation in {destination}",
                    "persona": "balanced",
                    "days": days,
                    "price": 20000,
                    "total_activities": 10,
                    "activity_types": ["Sightseeing", "Culture", "Adventure", "Relaxation"],
                    "highlights": ["City Tour", "Cultural Sites", "Beach Time", "Local Cuisine"],
                    "recommended": False,
                    "itinerary": [
                        {
                            "day": 1,
                            "date": start_date,
                            "title": f"Welcome to {destination}",
                            "activities": [
                                {
                                    "time": "11:00 AM",
                                    "title": "Hotel Check-in",
                                    "description": "Comfortable accommodation setup",
                                    "location": destination,
                                    "category": "accommodation",
                                    "duration": "1 hour"
                                },
                                {
                                    "time": "3:00 PM",
                                    "title": "Heritage Walk",
                                    "description": "Guided tour of historical landmarks",
                                    "location": "Old Town",
                                    "category": "culture",
                                    "duration": "2.5 hours"
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": f"luxury_{destination.lower()}",
                    "title": "Luxury Experience",
                    "description": f"Premium accommodations and exclusive experiences in {destination}",
                    "persona": "luxury",
                    "days": days,
                    "price": 45000,
                    "total_activities": 8,
                    "activity_types": ["Fine Dining", "Spa", "Private Tours", "Luxury Transport"],
                    "highlights": ["5-Star Resort", "Private Tours", "Spa Treatments", "Gourmet Dining"],
                    "recommended": False,
                    "itinerary": [
                        {
                            "day": 1,
                            "date": start_date,
                            "title": f"Luxury Arrival in {destination}",
                            "activities": [
                                {
                                    "time": "10:00 AM",
                                    "title": "Private Airport Transfer",
                                    "description": "Luxury vehicle with personal chauffeur",
                                    "location": "Airport",
                                    "category": "transportation",
                                    "duration": "1 hour"
                                },
                                {
                                    "time": "4:00 PM",
                                    "title": "Premium Spa Experience",
                                    "description": "Rejuvenating treatments at 5-star spa",
                                    "location": "Resort Spa",
                                    "category": "wellness",
                                    "duration": "3 hours"
                                }
                            ]
                        }
                    ]
                }
            ]
        else:
            # Use LLM-generated variants
            fallback_variants = variants
            
        # Return raw JSON response (bypass Pydantic validation)
        from fastapi.responses import JSONResponse
        response_data = {
            "variants": fallback_variants,
            "session_id": session_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ Returning {len(fallback_variants)} itinerary variants")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Itinerary generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customize-itinerary")
async def customize_itinerary_endpoint(request: CustomizationRequest):
    """Customize itinerary endpoint"""
    try:
        session_id = request.session_id
        itinerary_id = request.itinerary_id
        customizations = request.customizations
        
        logger.info(f"✏️ Customizing itinerary {itinerary_id} for session {session_id}")
        
        result = await customization_agent.apply_customizations(session_id, itinerary_id, customizations)
        
        return result
        
    except Exception as e:
        logger.error(f"Customization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-pricing")
async def update_pricing_endpoint(request: PricingUpdateRequest):
    """Update pricing endpoint"""
    try:
        session_id = request.session_id
        itinerary_id = request.itinerary_id
        
        logger.info(f"💰 Updating pricing for itinerary {itinerary_id}")
        
        result = await pricing_agent.update_pricing(session_id, itinerary_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Pricing update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/external-booking")
async def external_booking_endpoint(request: ExternalBookingRequest):
    """External booking endpoint"""
    try:
        session_id = request.session_id
        booking_details = request.booking_details
        
        logger.info(f"🔗 External booking for session {session_id}")
        
        result = await booking_agent.handle_booking(session_id, booking_details)
        
        return result
        
    except Exception as e:
        logger.error(f"External booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_all_variants(session_id: str, trip_details: Dict, persona_tags: List[str]):
    """Generate all itinerary variants in parallel"""
    import asyncio
    
    # Run agents in parallel
    adventurer_task = adventurer_agent.generate_itinerary(session_id, trip_details, persona_tags)
    balanced_task = balanced_agent.generate_itinerary(session_id, trip_details, persona_tags)
    luxury_task = luxury_agent.generate_itinerary(session_id, trip_details, persona_tags)
    
    # Wait for all results
    adventurer_result, balanced_result, luxury_result = await asyncio.gather(
        adventurer_task, balanced_task, luxury_task
    )
    
    return [adventurer_result, balanced_result, luxury_result]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )