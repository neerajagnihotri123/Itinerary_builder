"""
Travello.ai Backend - Clean Agent-Based Architecture
Multi-agent travel planning system with event-driven pipeline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv
import os
import logging
import time
import uuid
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
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
    allow_origins=["http://localhost:3000", "https://trip-architect-4.preview.emergentagent.com"],
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
from agents.service_selection_agent import ServiceSelectionAgent
from agents.conflict_detection_agent import ConflictDetectionAgent
from agents.dynamic_pricing_agent import DynamicPricingAgent
from utils.context_store import ContextStore
from utils.event_bus import EventBus
from models.schemas import *

# Initialize context store and event bus
context_store = ContextStore()
event_bus = EventBus()

# Initialize all agents with required dependencies
profile_intake = ProfileIntakeAgent(context_store, event_bus)
persona_classifier = PersonaClassificationAgent(context_store, event_bus)
adventurer_agent = AdventurerAgent(context_store, event_bus)
balanced_agent = BalancedAgent(context_store, event_bus)
luxury_agent = LuxuryAgent(context_store, event_bus)
customization_agent = CustomizationAgent(context_store, event_bus)
pricing_agent = PricingAgent(context_store, event_bus)
service_selector = ServiceSelectionAgent()
conflict_detector = ConflictDetectionAgent()
dynamic_pricing_agent = DynamicPricingAgent()

# Initialize placeholder agents (to be implemented later)
class PlaceholderAgent:
    pass

booking_agent = PlaceholderAgent()
sustainability_agent = PlaceholderAgent()

# Register agents with event bus
event_bus.register_agent("profile_intake", profile_intake)
event_bus.register_agent("persona_classifier", persona_classifier)
event_bus.register_agent("adventurer", adventurer_agent)
event_bus.register_agent("balanced", balanced_agent)
event_bus.register_agent("luxury", luxury_agent)
event_bus.register_agent("customization", customization_agent)
event_bus.register_agent("pricing", pricing_agent)
event_bus.register_agent("service_selector", service_selector)
event_bus.register_agent("conflict_detector", conflict_detector)
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
    """Generate enhanced itinerary variants using Master Travel Planner agents"""
    try:
        session_id = request.session_id
        trip_details = request.trip_details
        persona_tags = request.persona_tags
        
        logger.info(f"🗓️ Generating enhanced Master Travel Planner itinerary for session {session_id}")
        logger.info(f"🗓️ Trip details: {trip_details}")
        logger.info(f"🗓️ Persona tags: {persona_tags}")
        
        # Use enhanced agents to generate comprehensive itinerary variants
        import asyncio
        
        try:
            # Generate all variants using enhanced agents with timeout
            adventurer_task = adventurer_agent.generate_itinerary(session_id, trip_details, persona_tags)
            balanced_task = balanced_agent.generate_itinerary(session_id, trip_details, persona_tags)
            luxury_task = luxury_agent.generate_itinerary(session_id, trip_details, persona_tags)
            
            # Wait for all enhanced variants with shorter timeout
            adventurer_result, balanced_result, luxury_result = await asyncio.wait_for(
                asyncio.gather(adventurer_task, balanced_task, luxury_task),
                timeout=20.0  # 20 second timeout for all agents
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Enhanced agents failed or timed out: {e}, using fallback")
            return await generate_simple_itinerary_fallback(request)
        
        # Convert enhanced agent results to frontend-compatible format
        variants = []
        
        for agent_result, variant_type in [
            (adventurer_result, "adventurer"),
            (balanced_result, "balanced"), 
            (luxury_result, "luxury")
        ]:
            if agent_result and "daily_itinerary" in agent_result:
                # Convert enhanced agent format to frontend format
                variant = {
                    "id": f"{variant_type}_{trip_details.get('destination', 'destination').lower().replace(' ', '_')}",
                    "title": agent_result.get("variant_title", f"{variant_type.title()} Experience"),
                    "description": f"Enhanced {variant_type} experience with explainable recommendations",
                    "persona": variant_type,
                    "days": agent_result.get("total_days", 3),
                    "price": agent_result.get("total_cost", 15000),
                    "price_per_day": int(agent_result.get("total_cost", 15000) / agent_result.get("total_days", 3)),
                    "total_activities": sum(len(day.get("activities", [])) for day in agent_result.get("daily_itinerary", [])),
                    "activity_types": [],
                    "highlights": [],
                    "recommended": variant_type == "adventurer",
                    "optimization_score": agent_result.get("optimization_score", 0.85),
                    "conflict_warnings": agent_result.get("conflict_warnings", []),
                    "itinerary": []
                }
                
                # Convert daily itinerary to frontend format
                for day_data in agent_result.get("daily_itinerary", []):
                    day_activities = []
                    
                    for activity in day_data.get("activities", []):
                        # Ensure enhanced fields are present
                        enhanced_activity = {
                            "time": activity.get("time_slot", activity.get("time", "10:00 AM")),
                            "title": activity.get("title", "Activity"),
                            "description": activity.get("description", "Activity description"),
                            "location": activity.get("location", trip_details.get("destination", "Location")),
                            "category": activity.get("category", "sightseeing"),
                            "duration": activity.get("duration", "2 hours"),
                            "cost": activity.get("cost", 2000),
                            "rating": activity.get("rating", 4.2),
                            "image": activity.get("image", "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop"),
                            # Enhanced fields as requested
                            "selected_reason": activity.get("selected_reason", f"🎯 Perfect for your {variant_type} travel style with excellent reviews and optimal location."),
                            "alternatives": activity.get("alternatives", []),
                            "travel_logistics": activity.get("travel_logistics", {
                                "from_previous": "Previous location",
                                "distance_km": 2.5,
                                "travel_time": "15 minutes",
                                "transport_mode": "Taxi",
                                "transport_cost": 200
                            }),
                            "booking_info": activity.get("booking_info", {
                                "advance_booking": "Recommended",
                                "availability": "Available",
                                "cancellation": "Free cancellation up to 24h"
                            })
                        }
                        
                        # Ensure alternatives has exactly 9 options
                        if len(enhanced_activity["alternatives"]) != 9:
                            enhanced_activity["alternatives"] = [
                                {
                                    "name": f"Alternative Option {i+1}",
                                    "cost": enhanced_activity["cost"] + (i * 200) - 400,
                                    "rating": 4.0 + (i * 0.1),
                                    "reason": f"{'Budget-friendly' if i < 3 else 'Premium' if i > 6 else 'Balanced'} option with good reviews",
                                    "distance_km": 1.5 + (i * 0.3),
                                    "travel_time": f"{10 + (i * 2)} minutes"
                                }
                                for i in range(9)
                            ]
                        
                        day_activities.append(enhanced_activity)
                    
                    variant["itinerary"].append({
                        "day": day_data.get("day", 1),
                        "date": day_data.get("date", "2024-12-25"),
                        "title": day_data.get("theme", f"Day {day_data.get('day', 1)} Experience"),
                        "activities": day_activities
                    })
                
                variants.append(variant)
        
        # Return enhanced response
        from fastapi.responses import JSONResponse
        response_data = {
            "variants": variants,
            "session_id": session_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"✅ Generated {len(variants)} enhanced itinerary variants with explainable AI")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Enhanced itinerary generation error: {e}")
        # Fallback to simple generation if enhanced fails
        return await generate_simple_itinerary_fallback(request)

async def generate_simple_itinerary_fallback(request: ItineraryGenerationRequest):
    """Fallback to simple itinerary generation if enhanced agents fail"""
    try:
        session_id = request.session_id
        trip_details = request.trip_details
        persona_tags = request.persona_tags
        
        logger.warning(f"Using fallback itinerary generation for session {session_id}")
        
        destination = trip_details.get("destination", "Unknown")
        start_date = trip_details.get("start_date", "2024-12-25")
        end_date = trip_details.get("end_date", "2024-12-28")
        adults = trip_details.get("adults", 2)
        budget = trip_details.get("budget_per_night", 4000)
        
        # Calculate trip duration
        from datetime import datetime, timedelta
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            days = (end - start).days + 1
        except:
            days = 3
        
        # Generate simple fallback variants with enhanced structure
        variants = []
        
        for variant_type in ['adventurer', 'balanced', 'luxury']:
            variant = {
                "id": f"{variant_type}_{destination.lower().replace(' ', '_')}",
                "title": f"{variant_type.title()} Experience",
                "description": f"Enhanced {variant_type} experience in {destination}",
                "persona": variant_type,
                "days": days,
                "price": budget * days * (1.2 if variant_type == 'adventurer' else 1.0 if variant_type == 'balanced' else 1.8),
                "price_per_day": budget * (1.2 if variant_type == 'adventurer' else 1.0 if variant_type == 'balanced' else 1.8),
                "total_activities": days * 3,
                "activity_types": ["Sightseeing", "Culture", "Adventure"],
                "highlights": ["Local Experiences", "Cultural Sites", "Adventure Activities", "Scenic Views"],
                "recommended": variant_type == 'adventurer',
                "optimization_score": 0.8,
                "conflict_warnings": [],
                "itinerary": []
            }
            
            # Generate days with enhanced structure
            for day_num in range(1, days + 1):
                day_date = (datetime.fromisoformat(start_date) + timedelta(days=day_num-1)).isoformat()[:10]
                
                activities = [
                    {
                        "time": "10:00 AM - 1:00 PM",
                        "title": f"Day {day_num} Morning Experience",
                        "description": f"Explore {destination} with guided morning activities",
                        "location": f"{destination} City Center",
                        "category": "sightseeing",
                        "duration": "3 hours",
                        "cost": 2000,
                        "rating": 4.2,
                        "image": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop",
                        "selected_reason": f"🎯 Perfect morning activity for your {variant_type} travel style with excellent local reviews and optimal timing.",
                        "alternatives": [
                            {
                                "name": f"Alternative Morning Option {i+1}",
                                "cost": 2000 + (i * 200) - 400,
                                "rating": 4.0 + (i * 0.1),
                                "reason": f"{'Budget-friendly' if i < 3 else 'Premium' if i > 6 else 'Balanced'} morning option",
                                "distance_km": 1.5 + (i * 0.3),
                                "travel_time": f"{10 + (i * 2)} minutes"
                            }
                            for i in range(9)
                        ],
                        "travel_logistics": {
                            "from_previous": "Hotel",
                            "distance_km": 2.0,
                            "travel_time": "15 minutes",
                            "transport_mode": "Taxi",
                            "transport_cost": 200
                        },
                        "booking_info": {
                            "advance_booking": "Recommended",
                            "availability": "Available",
                            "cancellation": "Free cancellation up to 24h"
                        }
                    }
                ]
                
                variant["itinerary"].append({
                    "day": day_num,
                    "date": day_date,
                    "title": f"Day {day_num}: {destination} Experience",
                    "activities": activities
                })
            
            variants.append(variant)
        
        from fastapi.responses import JSONResponse
        response_data = {
            "variants": variants,
            "session_id": session_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Fallback itinerary generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== NEW ADVANCED FEATURES ENDPOINTS =====

@app.post("/api/service-recommendations")
async def get_service_recommendations(request: dict):
    """Get top 10 service recommendations for itinerary slots"""
    try:
        session_id = request.get("session_id")
        service_type = request.get("service_type")  # 'accommodation', 'activities', 'transportation'
        location = request.get("location")
        traveler_profile = request.get("traveler_profile", {})
        activity_context = request.get("activity_context", {})
        
        logger.info(f"🔧 Getting {service_type} recommendations for {location}")
        
        services = await service_selector.get_service_recommendations(
            session_id=session_id,
            service_type=service_type,
            location=location,
            traveler_profile=traveler_profile,
            activity_context=activity_context
        )
        
        return {
            "services": services,
            "service_type": service_type,
            "location": location,
            "total_options": len(services),
            "auto_selected": services[0] if services else None,  # Auto-select top-ranked
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Service recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conflict-check")
async def check_itinerary_conflicts(request: dict):
    """Check itinerary for conflicts and unrealistic elements"""
    try:
        session_id = request.get("session_id")
        itinerary = request.get("itinerary", [])
        
        logger.info(f"🚨 Checking conflicts for {len(itinerary)}-day itinerary")
        
        conflict_results = await conflict_detector.check_itinerary_conflicts(
            session_id=session_id,
            itinerary=itinerary
        )
        
        # Get resolution suggestions if conflicts exist
        resolutions = []
        if conflict_results["has_conflicts"]:
            resolutions = await conflict_detector.suggest_conflict_resolutions(
                session_id=session_id,
                conflicts=conflict_results["conflicts"],
                itinerary=itinerary
            )
        
        return {
            **conflict_results,
            "resolutions": resolutions,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Conflict check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/edit-itinerary")
async def edit_itinerary(request: dict):
    """Handle itinerary editing operations"""
    try:
        session_id = request.get("session_id")
        operation = request.get("operation")  # 'reorder_days', 'move_activity', 'add_destination', 'remove_destination', 'lock_service'
        itinerary = request.get("itinerary", [])
        operation_data = request.get("operation_data", {})
        
        logger.info(f"✏️ Editing itinerary: {operation}")
        
        # Handle different edit operations
        if operation == "reorder_days":
            new_order = operation_data.get("new_order", [])
            edited_itinerary = [itinerary[i] for i in new_order if i < len(itinerary)]
            
        elif operation == "move_activity":
            from_day = operation_data.get("from_day")
            to_day = operation_data.get("to_day")
            activity_index = operation_data.get("activity_index")
            
            edited_itinerary = itinerary.copy()
            if from_day < len(edited_itinerary) and to_day < len(edited_itinerary):
                activity = edited_itinerary[from_day]["activities"].pop(activity_index)
                edited_itinerary[to_day]["activities"].append(activity)
                
        elif operation == "add_destination":
            new_destination = operation_data.get("destination")
            day_index = operation_data.get("day_index", len(itinerary))
            
            new_day = {
                "day": day_index + 1,
                "date": operation_data.get("date"),
                "title": f"Day {day_index + 1}: {new_destination} Exploration",
                "activities": []
            }
            
            edited_itinerary = itinerary.copy()
            edited_itinerary.insert(day_index, new_day)
            
        elif operation == "remove_destination":
            day_index = operation_data.get("day_index")
            edited_itinerary = [day for i, day in enumerate(itinerary) if i != day_index]
            
        elif operation == "lock_service":
            service_id = operation_data.get("service_id")
            day_index = operation_data.get("day_index")
            activity_index = operation_data.get("activity_index")
            
            edited_itinerary = itinerary.copy()
            if day_index < len(edited_itinerary) and activity_index < len(edited_itinerary[day_index]["activities"]):
                edited_itinerary[day_index]["activities"][activity_index]["locked"] = True
                edited_itinerary[day_index]["activities"][activity_index]["locked_service_id"] = service_id
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {operation}")
        
        # Check conflicts in edited itinerary
        conflict_check = await conflict_detector.check_itinerary_conflicts(session_id, edited_itinerary)
        
        return {
            "edited_itinerary": edited_itinerary,
            "operation": operation,
            "conflict_check": conflict_check,
            "success": True,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Itinerary edit error: {e}")
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
        
        logger.info(f"🎫 Processing external booking for session {session_id}")
        
        # Mock booking response
        return {
            "booking_id": f"booking_{session_id}_{int(time.time())}",
            "status": "confirmed",
            "booking_details": booking_details,
            "confirmation_code": f"TRV{uuid.uuid4().hex[:8].upper()}",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"External booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image-proxy")
async def image_proxy(url: str):
    """Proxy images to avoid CORS issues"""
    try:
        import httpx
        from fastapi.responses import Response
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'image/jpeg')
                return Response(
                    content=response.content,
                    media_type=content_type,
                    headers={
                        "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                        "Access-Control-Allow-Origin": "*"
                    }
                )
            else:
                # Return a default image if fetch fails
                return Response(
                    content=b"",
                    status_code=404
                )
                
    except Exception as e:
        logger.error(f"Image proxy error: {e}")
        return Response(content=b"", status_code=404)

@app.post("/api/dynamic-pricing")
async def calculate_dynamic_pricing(request: dict):
    """Calculate dynamic pricing with competitor analysis and profile discounts"""
    try:
        session_id = request.get("session_id")
        itinerary = request.get("itinerary", [])
        traveler_profile = request.get("traveler_profile", {})
        travel_dates = request.get("travel_dates", {})
        
        logger.info(f"💰 Calculating dynamic pricing for {len(itinerary)}-day itinerary")
        
        pricing_data = await dynamic_pricing_agent.calculate_dynamic_pricing(
            session_id=session_id,
            itinerary=itinerary,
            traveler_profile=traveler_profile,
            travel_dates=travel_dates
        )
        
        return {**pricing_data, "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Dynamic pricing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-checkout-cart")
async def create_checkout_cart(request: dict):
    """Create checkout cart with bundled services"""
    try:
        session_id = request.get("session_id")
        pricing_data = request.get("pricing_data", {})
        itinerary = request.get("itinerary", [])
        user_details = request.get("user_details", {})
        
        logger.info(f"🛒 Creating checkout cart for session {session_id}")
        
        cart = await dynamic_pricing_agent.create_checkout_cart(
            session_id=session_id,
            pricing_data=pricing_data,
            itinerary=itinerary,
            user_details=user_details
        )
        
        return cart
        
    except Exception as e:
        logger.error(f"Checkout cart creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mock-checkout")
async def mock_checkout_process(request: dict):
    """Mock checkout process for POC"""
    try:
        cart_id = request.get("cart_id")
        payment_method = request.get("payment_method", "card")
        
        logger.info(f"💳 Processing mock checkout for cart {cart_id}")
        
        # Simulate checkout process
        checkout_result = {
            "checkout_id": f"checkout_{cart_id}_{int(time.time())}",
            "cart_id": cart_id,
            "status": "completed",
            "payment_method": payment_method,
            "confirmation_code": f"TRV{uuid.uuid4().hex[:8].upper()}",
            "booking_references": [
                f"HTL{uuid.uuid4().hex[:6].upper()}",  # Hotel booking
                f"ACT{uuid.uuid4().hex[:6].upper()}",  # Activities booking
                f"TRN{uuid.uuid4().hex[:6].upper()}"   # Transport booking
            ],
            "total_paid": request.get("total_amount", 0),
            "payment_status": "confirmed",
            "estimated_processing_time": "2-4 hours",
            "customer_support": "+91-800-123-4567",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
        return checkout_result
        
    except Exception as e:
        logger.error(f"Mock checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"External booking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== PARALLEL PROCESSING HELPER FUNCTIONS =====

async def get_cached_itinerary(cache_key: str):
    """Get cached itinerary result"""
    # Simple in-memory cache for demo - in production use Redis
    if not hasattr(get_cached_itinerary, 'cache'):
        get_cached_itinerary.cache = {}
    return get_cached_itinerary.cache.get(cache_key)

async def cache_itinerary(cache_key: str, result: dict, ttl: int = 3600):
    """Cache itinerary result"""
    if not hasattr(get_cached_itinerary, 'cache'):
        get_cached_itinerary.cache = {}
    get_cached_itinerary.cache[cache_key] = result

async def generate_optimized_variant(agent, session_id: str, trip_details: dict, persona_tags: list, variant_type: str):
    """Generate optimized variant with timeout handling"""
    try:
        result = await asyncio.wait_for(
            agent.generate_itinerary(session_id, trip_details, persona_tags),
            timeout=7.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"⏰ {variant_type} agent timed out")
        return None
    except Exception as e:
        logger.error(f"❌ {variant_type} agent failed: {e}")
        return None

async def process_parallel_results(successful_results: list, trip_details: dict):
    """Process successful parallel results into frontend format"""
    variants = []
    
    for agent_result, variant_type in successful_results:
        if agent_result and "daily_itinerary" in agent_result:
            # Convert enhanced agent format to frontend format
            variant = {
                "id": f"{variant_type}_{trip_details.get('destination', 'destination').lower().replace(' ', '_')}",
                "title": agent_result.get("variant_title", f"{variant_type.title()} Experience"),
                "description": f"Enhanced {variant_type} experience with explainable recommendations",
                "persona": variant_type,
                "days": agent_result.get("total_days", 3),
                "price": agent_result.get("total_cost", 15000),
                "price_per_day": int(agent_result.get("total_cost", 15000) / agent_result.get("total_days", 3)),
                "total_activities": sum(len(day.get("activities", [])) for day in agent_result.get("daily_itinerary", [])),
                "activity_types": [],
                "highlights": [],
                "recommended": variant_type == "adventurer",
                "optimization_score": agent_result.get("optimization_score", 0.85),
                "conflict_warnings": agent_result.get("conflict_warnings", []),
                "itinerary": []
            }
            
            # Convert daily itinerary to frontend format
            for day_data in agent_result.get("daily_itinerary", []):
                day_activities = []
                
                for activity in day_data.get("activities", []):
                    # Ensure enhanced fields are present
                    enhanced_activity = {
                        "time": activity.get("time_slot", activity.get("time", "10:00 AM")),
                        "title": activity.get("title", "Activity"),
                        "description": activity.get("description", "Activity description"),
                        "location": activity.get("location", trip_details.get("destination", "Location")),
                        "category": activity.get("category", "sightseeing"),
                        "duration": activity.get("duration", "2 hours"),
                        "cost": activity.get("cost", 2000),
                        "rating": activity.get("rating", 4.2),
                        "image": activity.get("image", "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&h=300&fit=crop"),
                        # Enhanced fields as requested
                        "selected_reason": activity.get("selected_reason", f"🎯 Perfect for your {variant_type} travel style with excellent reviews and optimal location."),
                        "alternatives": activity.get("alternatives", []),
                        "travel_logistics": activity.get("travel_logistics", {
                            "from_previous": "Previous location",
                            "distance_km": 2.5,
                            "travel_time": "15 minutes",
                            "transport_mode": "Taxi",
                            "transport_cost": 200
                        }),
                        "booking_info": activity.get("booking_info", {
                            "advance_booking": "Recommended",
                            "availability": "Available",
                            "cancellation": "Free cancellation up to 24h"
                        })
                    }
                    
                    # Ensure alternatives has exactly 9 options
                    if len(enhanced_activity["alternatives"]) != 9:
                        enhanced_activity["alternatives"] = [
                            {
                                "name": f"Alternative Option {i+1}",
                                "cost": enhanced_activity["cost"] + (i * 200) - 400,
                                "rating": 4.0 + (i * 0.1),
                                "reason": f"{'Budget-friendly' if i < 3 else 'Premium' if i > 6 else 'Balanced'} option with good reviews",
                                "distance_km": 1.5 + (i * 0.3),
                                "travel_time": f"{10 + (i * 2)} minutes"
                            }
                            for i in range(9)
                        ]
                    
                    day_activities.append(enhanced_activity)
                
                variant["itinerary"].append({
                    "day": day_data.get("day", 1),
                    "date": day_data.get("date", "2024-12-25"),
                    "title": day_data.get("theme", f"Day {day_data.get('day', 1)} Experience"),
                    "activities": day_activities
                })
            
            variants.append(variant)
    
    return variants

async def generate_progressive_fallback(request, start_time: float):
    """Progressive fallback when parallel processing fails"""
    try:
        elapsed = time.time() - start_time
        logger.info(f"🔄 PROGRESSIVE FALLBACK: Starting after {elapsed:.2f}s")
        
        # Try one agent at a time with shorter timeouts
        session_id = request.session_id
        trip_details = request.trip_details
        persona_tags = request.persona_tags
        
        # Try balanced agent first (most reliable)
        try:
            balanced_result = await asyncio.wait_for(
                balanced_agent.generate_itinerary(session_id, trip_details, persona_tags),
                timeout=5.0
            )
            if balanced_result:
                variants = await process_parallel_results([(balanced_result, "balanced")], trip_details)
                logger.info(f"✅ FALLBACK SUCCESS: Generated {len(variants)} variant(s)")
                return {"variants": variants}
        except:
            pass
        
        # If that fails, use simple fallback
        logger.warning("🚨 All agents failed, using simple fallback")
        return await generate_simple_itinerary_fallback(request)
        
    except Exception as e:
        logger.error(f"❌ PROGRESSIVE FALLBACK ERROR: {e}")
        return await generate_simple_itinerary_fallback(request)

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