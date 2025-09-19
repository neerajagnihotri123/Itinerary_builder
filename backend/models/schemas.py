"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class PersonaType(str, Enum):
    """Traveler persona types"""
    ADVENTURER = "adventurer"
    CULTURAL_EXPLORER = "cultural_explorer"
    LUXURY_CONNOISSEUR = "luxury_connoisseur"
    BUDGET_BACKPACKER = "budget_backpacker"
    ECO_CONSCIOUS = "eco_conscious_traveler"
    FAMILY_ORIENTED = "family_oriented"
    BUSINESS_TRAVELER = "business_traveler"
    BALANCED_TRAVELER = "balanced_traveler"  # Added missing persona type
    GENERAL_TRAVELER = "general_traveler"    # Added fallback persona type

class ItineraryVariantType(str, Enum):
    """Itinerary variant types"""
    ADVENTURER = "adventurer"
    BALANCED = "balanced"
    LUXURY = "luxury"

class ActivityType(str, Enum):
    """Activity types"""
    ARRIVAL = "arrival"
    DEPARTURE = "departure"
    SIGHTSEEING = "sightseeing"
    ADVENTURE = "adventure" 
    CULTURAL = "cultural"
    DINING = "dining"
    SHOPPING = "shopping"
    RELAXATION = "relaxation"
    TRANSPORTATION = "transportation"
    ACCOMMODATION = "accommodation"

# Request Models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProfileIntakeRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    responses: Dict[str, Any] = Field(..., description="Profile responses")

class PersonaClassificationRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    trip_details: Dict[str, Any] = Field(..., description="Trip details")
    profile_data: Dict[str, Any] = Field(..., description="Profile data")

class ItineraryGenerationRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    trip_details: Dict[str, Any] = Field(..., description="Trip details")
    persona_tags: List[str] = Field(..., description="Persona tags")

class CustomizationRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    itinerary_id: str = Field(..., description="Itinerary ID")
    customizations: List[Dict[str, Any]] = Field(..., description="Customizations")

class PricingUpdateRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    itinerary_id: str = Field(..., description="Itinerary ID")

class ExternalBookingRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    booking_details: Dict[str, Any] = Field(..., description="Booking details")

# Response Models
class UIAction(BaseModel):
    type: str = Field(..., description="UI action type")
    payload: Dict[str, Any] = Field(..., description="Action payload")

class Activity(BaseModel):
    id: str = Field(..., description="Activity ID")
    name: str = Field(..., description="Activity name")
    type: ActivityType = Field(..., description="Activity type")
    time: str = Field(..., description="Start time")
    duration: str = Field(..., description="Duration")
    location: str = Field(..., description="Location")
    description: str = Field(..., description="Description")
    cost: float = Field(..., description="Cost in INR")
    image: Optional[str] = Field(None, description="Activity image URL")
    booking_url: Optional[str] = Field(None, description="External booking URL")
    sustainability_tags: List[str] = Field(default_factory=list)

class DayItinerary(BaseModel):
    day: int = Field(..., description="Day number")
    date: str = Field(..., description="Date")
    theme: str = Field(..., description="Day theme")
    activities: List[Activity] = Field(..., description="Activities for the day")
    total_cost: float = Field(..., description="Total cost for the day")

class ItineraryVariant(BaseModel):
    id: str = Field(..., description="Variant ID")
    type: ItineraryVariantType = Field(..., description="Variant type")
    title: str = Field(..., description="Variant title")
    description: str = Field(..., description="Variant description")
    days: int = Field(..., description="Total days")
    total_cost: float = Field(..., description="Total cost")
    daily_itinerary: List[DayItinerary] = Field(..., description="Day-by-day itinerary")
    highlights: List[str] = Field(..., description="Key highlights")
    persona_match: float = Field(..., description="Persona match score")
    sustainability_score: float = Field(..., description="Sustainability score")
    recommended: bool = Field(default=False, description="Is recommended")
    total_activities: int = Field(..., description="Total number of activities")
    activity_types: List[str] = Field(..., description="Types of activities included")

class ChatResponse(BaseModel):
    chat_text: str = Field(..., description="Chat response text")
    ui_actions: List[UIAction] = Field(default_factory=list, description="UI actions")
    updated_profile: Dict[str, Any] = Field(default_factory=dict, description="Updated profile")
    followup_questions: List[str] = Field(default_factory=list, description="Follow-up questions")
    analytics_tags: List[str] = Field(default_factory=list, description="Analytics tags")

class ProfileIntakeResponse(BaseModel):
    profile_complete: bool = Field(..., description="Is profile complete")
    persona_tags: List[str] = Field(..., description="Persona tags")
    next_questions: List[str] = Field(default_factory=list, description="Next questions")
    ui_actions: List[UIAction] = Field(default_factory=list, description="UI actions")

class PersonaClassificationResponse(BaseModel):
    persona_type: PersonaType = Field(..., description="Classified persona")
    persona_tags: List[str] = Field(..., description="Persona tags")
    confidence: float = Field(..., description="Classification confidence")
    ui_actions: List[UIAction] = Field(default_factory=list, description="UI actions")

class ItineraryResponse(BaseModel):
    variants: List[ItineraryVariant] = Field(..., description="Itinerary variants")
    session_id: str = Field(..., description="Session ID")
    generated_at: str = Field(..., description="Generation timestamp")

class CustomizationResponse(BaseModel):
    updated_variant: ItineraryVariant = Field(..., description="Updated variant")
    conflicts: List[str] = Field(default_factory=list, description="Conflicts detected")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions")

class PricingResponse(BaseModel):
    updated_pricing: Dict[str, float] = Field(..., description="Updated pricing")
    price_breakdown: Dict[str, Any] = Field(..., description="Price breakdown")
    discounts_applied: List[str] = Field(default_factory=list, description="Discounts applied")

class ExternalBookingResponse(BaseModel):
    booking_status: str = Field(..., description="Booking status")
    booking_reference: Optional[str] = Field(None, description="Booking reference")
    booking_url: Optional[str] = Field(None, description="Booking URL")
    additional_info: Dict[str, Any] = Field(default_factory=dict)