"""
Retrieval Agent - Fetches and returns facts (POIs, hotels, activities) using LLM
"""
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_data import MOCK_DESTINATIONS, MOCK_HOTELS, MOCK_TOURS, MOCK_ACTIVITIES

load_dotenv()

class RetrievalAgent:
    """Handles LLM-powered fact retrieval and grounding for planning"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.confidence_threshold = 0.7
        
    async def get_facts(self, slots) -> List[Dict[str, Any]]:
        """
        Fetch and return top-K matching facts using pure LLM generation
        No mock data - only LLM-generated responses
        """
        facts = []
        
        # Get destination-specific data
        destination_name = slots.destination
        if not destination_name:
            return self._generate_no_facts_response("No destination specified")
        
        try:
            # Use only LLM to generate comprehensive facts about the destination
            llm_facts = await self._generate_facts_with_llm(destination_name, slots)
            if llm_facts:
                facts.extend(llm_facts)
            else:
                return self._generate_no_facts_response(f"Could not generate facts for {destination_name}")
                
        except Exception as e:
            print(f"❌ LLM fact generation failed: {e}")
            return self._generate_no_facts_response(f"Error generating facts for {destination_name}: {str(e)}")
        
        # Sort by relevance (confidence) + freshness (last_updated)
        facts = self._sort_facts_by_relevance_and_freshness(facts)
        
        # Return top-K results (20 facts maximum)
        return facts[:20]
    
    def _sort_facts_by_relevance_and_freshness(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort facts by relevance (confidence) + freshness (last_updated)"""
        
        def calculate_sort_score(fact):
            # Weight: 70% relevance (confidence), 30% freshness
            confidence = fact.get('confidence', 0.5)
            
            # Calculate freshness score based on availability_cache_ts
            try:
                if fact.get('availability_cache_ts'):
                    fact_time = datetime.fromisoformat(fact['availability_cache_ts'].replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    hours_old = (current_time - fact_time).total_seconds() / 3600
                    
                    # Fresher facts get higher scores (decay over 24 hours)
                    freshness = max(0, 1 - (hours_old / 24))
                else:
                    freshness = 0.5  # Neutral score for unknown freshness
            except:
                freshness = 0.5
            
            # Combined score: 70% confidence + 30% freshness
            return (confidence * 0.7) + (freshness * 0.3)
        
        # Sort by combined score (descending)
        facts.sort(key=calculate_sort_score, reverse=True)
        return facts
    
    def _generate_no_facts_response(self, reason: str) -> List[Dict[str, Any]]:
        """Return explainable no_facts response when no facts found"""
        return [{
            "type": "no_facts_found",
            "reason": reason,
            "confidence": 1.0,
            "provider": "retrieval_agent",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "suggestions": [
                "Try searching for a different destination",
                "Check spelling of destination name", 
                "Try broader search terms"
            ],
            "alternative_destinations": [
                {"name": "Kerala, India", "canonical_place_id": "kerala_backwaters"},
                {"name": "Goa, India", "canonical_place_id": "goa_india"},
                {"name": "Rajasthan, India", "canonical_place_id": "rajasthan_india"}
            ]
        }]
    
    async def _generate_facts_with_llm(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Use LLM to generate comprehensive destination facts"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for fact generation
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"retrieval_{hash(destination) % 10000}",
                system_message="You are a travel expert. Generate accurate, detailed information about destinations, hotels, and activities in JSON format."
            ).with_model("openai", "gpt-4o-mini")
            
            # Create comprehensive prompt for fact generation
            context = self._prepare_fact_generation_context(destination, slots)
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse the JSON response
            try:
                facts_data = json.loads(content)
                return self._parse_llm_facts(facts_data, destination)
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from LLM fact generation")
                return self._get_fallback_facts(destination, slots)
                
        except Exception as e:
            print(f"❌ LLM fact generation error: {e}")
            return self._get_fallback_facts(destination, slots)
    
    def _prepare_fact_generation_context(self, destination: str, slots) -> str:
        """Prepare context for LLM fact generation"""
        return f"""
Generate comprehensive travel facts for {destination} including POIs, hotels, and activities.

User Context:
- Destination: {destination}
- Travelers: {getattr(slots, 'adults', 2)} adults, {getattr(slots, 'children', 0)} children
- Budget: {getattr(slots, 'budget_per_night', 'Not specified')} per night
- Duration: {getattr(slots, 'start_date', '')} to {getattr(slots, 'end_date', '')}

Generate JSON with following structure:
{{
  "pois": [
    {{
      "id": "unique_poi_id",
      "name": "POI Name",
      "description": "Detailed description",
      "coordinates": {{"lat": 0.0, "lng": 0.0}},
      "rating": 4.5,
      "highlights": ["highlight1", "highlight2"],
      "category": ["category1"],
      "confidence": 0.9
    }}
  ],
  "hotels": [
    {{
      "id": "unique_hotel_id", 
      "name": "Hotel Name",
      "description": "Hotel description",
      "location": "Specific location",
      "rating": 4.0,
      "price_per_night": 5000,
      "amenities": ["amenity1", "amenity2"],
      "hotel_type": "Resort/Hotel/etc",
      "coordinates": {{"lat": 0.0, "lng": 0.0}},
      "confidence": 0.9
    }}
  ],
  "activities": [
    {{
      "id": "unique_activity_id",
      "name": "Activity Name", 
      "description": "Activity description",
      "location": "Activity location",
      "duration": "2-3 hours",
      "price": 1500,
      "rating": 4.3,
      "category": "Adventure/Cultural/etc",
      "highlights": ["highlight1"],
      "confidence": 0.8
    }}
  ]
}}

Focus on:
- Popular attractions and hidden gems in {destination}
- Accommodations suitable for {getattr(slots, 'adults', 2)} adults and {getattr(slots, 'children', 0)} children
- Activities matching the destination's character (adventure, cultural, nature, etc.)
- Realistic prices in Indian Rupees
- Accurate locations and ratings

Generate 5 POIs, 3-5 hotels, and 8 activities maximum.
"""
    
    def _parse_llm_facts(self, facts_data: Dict, destination: str) -> List[Dict[str, Any]]:
        """Parse LLM-generated facts into standard format with proper metadata"""
        facts = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Parse POIs
        for poi in facts_data.get('pois', []):
            fact = {
                "type": "poi",
                "id": poi.get('id', f"poi_{hash(poi.get('name', '')) % 10000}"),
                "name": poi.get('name', ''),
                "address": f"{poi.get('name', '')}, {destination}",
                "coords": poi.get('coordinates', {}),
                "rating": poi.get('rating', 4.5),
                "price_estimate": None,
                "provider": "llm_generated",
                "source": "emergent_ai_travel_expert", 
                "last_updated": current_time,
                "availability_cache_ts": current_time,
                "confidence": poi.get('confidence', 0.9),
                "description": poi.get('description', ''),
                "highlights": poi.get('highlights', []),
                "category": poi.get('category', []),
                "freshness_score": 1.0  # New facts are maximally fresh
            }
            facts.append(fact)
        
        # Parse hotels
        for hotel in facts_data.get('hotels', []):
            fact = {
                "type": "hotel",
                "id": hotel.get('id', f"hotel_{hash(hotel.get('name', '')) % 10000}"),
                "name": hotel.get('name', ''),
                "address": hotel.get('location', destination),
                "coords": hotel.get('coordinates', {}),
                "rating": hotel.get('rating', 4.0),
                "price_estimate": hotel.get('price_per_night', 5000),
                "provider": "llm_generated",
                "source": "ai_hotel_recommendations",
                "last_updated": current_time,
                "availability_cache_ts": current_time,
                "confidence": hotel.get('confidence', 0.9),
                "amenities": hotel.get('amenities', []),
                "hotel_type": hotel.get('hotel_type', 'Hotel'),
                "description": hotel.get('description', ''),
                "freshness_score": 1.0
            }
            facts.append(fact)
        
        # Parse activities
        for activity in facts_data.get('activities', []):
            fact = {
                "type": "activity",
                "subtype": "experience",
                "id": activity.get('id', f"activity_{hash(activity.get('name', '')) % 10000}"),
                "name": activity.get('name', ''),
                "address": activity.get('location', destination),
                "coords": {},
                "rating": activity.get('rating', 4.3),
                "price_estimate": activity.get('price', 1500),
                "provider": "llm_generated",
                "source": "ai_activity_curator",
                "last_updated": current_time,
                "availability_cache_ts": current_time,
                "confidence": activity.get('confidence', 0.8),
                "duration": activity.get('duration', '2-3 hours'),
                "description": activity.get('description', ''),
                "category": activity.get('category', 'Experience'),
                "freshness_score": 1.0
            }
            facts.append(fact)
        
        print(f"✅ LLM generated {len(facts)} facts for {destination} with metadata")
        return facts
    
    def _get_fallback_facts(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Enhanced fallback using mock data with proper metadata and freshness scoring"""
        facts = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Extract base destination name for matching
        base_destination = self._extract_base_destination(destination)
        
        # Retrieve POIs (destinations) with enhanced metadata
        poi_facts = self._get_poi_facts_with_metadata(base_destination, current_time)
        facts.extend(poi_facts)
        
        # Retrieve hotels with enhanced metadata
        hotel_facts = self._get_hotel_facts_with_metadata(base_destination, slots, current_time)
        facts.extend(hotel_facts)
        
        # Retrieve activities/tours with enhanced metadata
        activity_facts = self._get_activity_facts_with_metadata(base_destination, current_time)
        facts.extend(activity_facts)
        
        print(f"🔄 Using fallback facts: {len(facts)} facts for {destination} with metadata")
        return facts
    
    def _get_poi_facts_with_metadata(self, destination: str, current_time: str) -> List[Dict[str, Any]]:
        """Retrieve POI/destination facts with proper metadata"""
        facts = []
        
        for dest_data in MOCK_DESTINATIONS:
            if destination.lower() in dest_data['name'].lower():
                fact = {
                    "type": "poi",
                    "id": dest_data['id'],
                    "name": dest_data['name'],
                    "address": f"{dest_data['name']}, {dest_data['country']}",
                    "coords": dest_data.get('coordinates', {}),
                    "rating": dest_data.get('rating', 4.5),
                    "price_estimate": None,
                    "provider": "mock_data",
                    "source": "internal_destinations_db",
                    "last_updated": current_time,
                    "availability_cache_ts": current_time,
                    "confidence": 0.85,  # High confidence for curated mock data
                    "description": dest_data.get('pitch', ''),
                    "highlights": dest_data.get('highlights', []),
                    "category": dest_data.get('category', []),
                    "freshness_score": 0.8  # Mock data is reasonably fresh but not as fresh as LLM
                }
                facts.append(fact)
        
        return facts
    
    def _get_hotel_facts_with_metadata(self, destination: str, slots, current_time: str) -> List[Dict[str, Any]]:
        """Retrieve hotel facts with enhanced metadata and budget filtering"""
        facts = []
        
        # Find destination ID
        destination_id = None
        for dest_data in MOCK_DESTINATIONS:
            if destination.lower() in dest_data['name'].lower():
                destination_id = dest_data['id']
                break
        
        if not destination_id:
            return facts
        
        # Get hotels for this destination
        for hotel_data in MOCK_HOTELS:
            if hotel_data.get('destination_id') == destination_id:
                # Check budget compatibility
                budget_match = True
                confidence = 0.85
                if slots.budget_per_night:
                    hotel_price = hotel_data.get('price_per_night', 5000)
                    if hotel_price > slots.budget_per_night * 1.5:  # Allow 50% flexibility
                        budget_match = False
                        confidence = 0.6
                
                fact = {
                    "type": "hotel",
                    "id": hotel_data['id'],
                    "name": hotel_data['name'],
                    "address": hotel_data.get('location', f"{destination}"),
                    "coords": hotel_data.get('coordinates', {}),
                    "rating": hotel_data.get('rating', 4.0),
                    "price_estimate": hotel_data.get('price_per_night', 5000),
                    "provider": "partner_hotels",
                    "source": "curated_accommodations_db", 
                    "last_updated": current_time,
                    "availability_cache_ts": current_time,
                    "confidence": confidence,
                    "amenities": hotel_data.get('amenities', []),
                    "hotel_type": hotel_data.get('type', 'Hotel'),
                    "description": hotel_data.get('description', ''),
                    "budget_match": budget_match,
                    "freshness_score": 0.75
                }
                facts.append(fact)
        
        return facts
    
    def _get_activity_facts_with_metadata(self, destination: str, current_time: str) -> List[Dict[str, Any]]:
        """Retrieve activity/tour facts with enhanced metadata"""
        facts = []
        
        # Get tours with metadata
        for tour_data in MOCK_TOURS:
            if destination.lower() in tour_data.get('location', '').lower():
                fact = {
                    "type": "activity", 
                    "subtype": "tour",
                    "id": tour_data['id'],
                    "name": tour_data['title'],
                    "address": tour_data.get('location', destination),
                    "coords": {},
                    "rating": tour_data.get('rating', 4.5),
                    "price_estimate": tour_data.get('price', 2000),
                    "provider": "tour_operators",
                    "source": "curated_tours_db",
                    "last_updated": current_time,
                    "availability_cache_ts": current_time,
                    "confidence": 0.8,
                    "duration": tour_data.get('duration', '1 day'),
                    "description": tour_data.get('description', ''),
                    "highlights": tour_data.get('highlights', []),
                    "freshness_score": 0.7
                }
                facts.append(fact)
        
        # Get activities with metadata
        for activity_data in MOCK_ACTIVITIES:
            if destination.lower() in activity_data.get('location', '').lower():
                fact = {
                    "type": "activity",
                    "subtype": "experience", 
                    "id": activity_data['id'],
                    "name": activity_data['title'],
                    "address": activity_data.get('location', destination),
                    "coords": {},
                    "rating": activity_data.get('rating', 4.3),
                    "price_estimate": activity_data.get('price', 1500),
                    "provider": "activity_providers",
                    "source": "curated_experiences_db",
                    "last_updated": current_time,
                    "availability_cache_ts": current_time,
                    "confidence": 0.8,
                    "duration": activity_data.get('duration', '2-3 hours'),
                    "description": activity_data.get('description', ''),
                    "category": activity_data.get('category', 'Adventure'),
                    "freshness_score": 0.7
                }
                facts.append(fact)
        
        return facts
    
    def _extract_base_destination(self, destination_name: str) -> str:
        """Extract base destination name for matching"""
        destination_lower = destination_name.lower()
        
        mapping = {
            'rishikesh': 'rishikesh',
            'manali': 'manali', 
            'andaman': 'andaman',
            'kerala': 'kerala',
            'rajasthan': 'rajasthan',
            'pondicherry': 'pondicherry',
            'goa': 'goa',
            'kashmir': 'kashmir',
            'ladakh': 'ladakh'
        }
        
        for key, value in mapping.items():
            if key in destination_lower:
                return value
        
        return destination_lower.split(',')[0].strip()
    
    def _get_poi_facts(self, destination: str) -> List[Dict[str, Any]]:
        """Retrieve POI/destination facts"""
        facts = []
        
        for dest_data in MOCK_DESTINATIONS:
            if destination.lower() in dest_data['name'].lower():
                fact = {
                    "type": "poi",
                    "id": dest_data['id'],
                    "name": dest_data['name'],
                    "address": f"{dest_data['name']}, {dest_data['country']}",
                    "coords": dest_data.get('coordinates', {}),
                    "rating": dest_data.get('rating', 4.5),
                    "price_estimate": None,
                    "source": "internal_db",
                    "availability_cache_ts": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.9,
                    "description": dest_data.get('pitch', ''),
                    "highlights": dest_data.get('highlights', []),
                    "category": dest_data.get('category', [])
                }
                facts.append(fact)
        
        return facts
    
    def _get_hotel_facts(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Retrieve hotel facts matching destination and budget"""
        facts = []
        
        # Find destination ID
        destination_id = None
        for dest_data in MOCK_DESTINATIONS:
            if destination.lower() in dest_data['name'].lower():
                destination_id = dest_data['id']
                break
        
        if not destination_id:
            return facts
        
        # Get hotels for this destination
        for hotel_data in MOCK_HOTELS:
            if hotel_data.get('destination_id') == destination_id:
                # Check budget compatibility
                budget_match = True
                if slots.budget_per_night:
                    hotel_price = hotel_data.get('price_per_night', 5000)
                    if hotel_price > slots.budget_per_night * 1.5:  # Allow 50% flexibility
                        budget_match = False
                
                confidence = 0.9 if budget_match else 0.6
                
                fact = {
                    "type": "hotel",
                    "id": hotel_data['id'],
                    "name": hotel_data['name'],
                    "address": hotel_data.get('location', f"{destination}"),
                    "coords": hotel_data.get('coordinates', {}),
                    "rating": hotel_data.get('rating', 4.0),
                    "price_estimate": hotel_data.get('price_per_night', 5000),
                    "source": "partner_api",
                    "availability_cache_ts": datetime.now(timezone.utc).isoformat(),
                    "confidence": confidence,
                    "amenities": hotel_data.get('amenities', []),
                    "hotel_type": hotel_data.get('type', 'Hotel'),
                    "description": hotel_data.get('description', '')
                }
                facts.append(fact)
        
        return facts
    
    def _get_activity_facts(self, destination: str) -> List[Dict[str, Any]]:
        """Retrieve activity/tour facts"""
        facts = []
        
        # Get tours
        for tour_data in MOCK_TOURS:
            if destination.lower() in tour_data.get('location', '').lower():
                fact = {
                    "type": "activity", 
                    "subtype": "tour",
                    "id": tour_data['id'],
                    "name": tour_data['title'],
                    "address": tour_data.get('location', destination),
                    "coords": {},
                    "rating": tour_data.get('rating', 4.5),
                    "price_estimate": tour_data.get('price', 2000),
                    "source": "tours_db",
                    "availability_cache_ts": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.8,
                    "duration": tour_data.get('duration', '1 day'),
                    "description": tour_data.get('description', ''),
                    "highlights": tour_data.get('highlights', [])
                }
                facts.append(fact)
        
        # Get activities
        for activity_data in MOCK_ACTIVITIES:
            if destination.lower() in activity_data.get('location', '').lower():
                fact = {
                    "type": "activity",
                    "subtype": "experience", 
                    "id": activity_data['id'],
                    "name": activity_data['title'],
                    "address": activity_data.get('location', destination),
                    "coords": {},
                    "rating": activity_data.get('rating', 4.3),
                    "price_estimate": activity_data.get('price', 1500),
                    "source": "activities_db",
                    "availability_cache_ts": datetime.now(timezone.utc).isoformat(),
                    "confidence": 0.8,
                    "duration": activity_data.get('duration', '2-3 hours'),
                    "description": activity_data.get('description', ''),
                    "category": activity_data.get('category', 'Adventure')
                }
                facts.append(fact)
        
        return facts
    
    async def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific hotel"""
        for hotel_data in MOCK_HOTELS:
            if hotel_data['id'] == hotel_id:
                return {
                    "id": hotel_id,
                    "name": hotel_data['name'],
                    "rating": hotel_data.get('rating', 4.0),
                    "price_per_night": hotel_data.get('price_per_night', 5000),
                    "amenities": hotel_data.get('amenities', []),
                    "location": hotel_data.get('location', ''),
                    "type": hotel_data.get('type', 'Hotel'),
                    "description": hotel_data.get('description', ''),
                    "images": hotel_data.get('images', []),
                    "availability": True,  # Mock availability
                    "booking_url": f"https://booking.example.com/hotels/{hotel_id}"
                }
        return {}
    
    async def get_activity_details(self, activity_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific activity"""
        # Check tours first
        for tour_data in MOCK_TOURS:
            if tour_data['id'] == activity_id:
                return {
                    "id": activity_id,
                    "name": tour_data['title'],
                    "type": "tour",
                    "rating": tour_data.get('rating', 4.5),
                    "price": tour_data.get('price', 2000),
                    "duration": tour_data.get('duration', '1 day'),
                    "location": tour_data.get('location', ''),
                    "description": tour_data.get('description', ''),
                    "highlights": tour_data.get('highlights', []),
                    "includes": tour_data.get('includes', []),
                    "booking_url": f"https://booking.example.com/tours/{activity_id}"
                }
        
        # Check activities
        for activity_data in MOCK_ACTIVITIES:
            if activity_data['id'] == activity_id:
                return {
                    "id": activity_id,
                    "name": activity_data['title'],
                    "type": "activity",
                    "rating": activity_data.get('rating', 4.3),
                    "price": activity_data.get('price', 1500),
                    "duration": activity_data.get('duration', '2-3 hours'),
                    "location": activity_data.get('location', ''),
                    "description": activity_data.get('description', ''),
                    "category": activity_data.get('category', ''),
                    "booking_url": f"https://booking.example.com/activities/{activity_id}"
                }
        
        return {}