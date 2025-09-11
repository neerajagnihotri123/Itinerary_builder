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
        Fetch and return top-K matching facts (hotels, POIs, activities)
        Returns: List of facts with metadata
        """
        facts = []
        
        # Get destination-specific data
        destination_name = slots.destination
        if not destination_name:
            return []
        
        # Extract base destination name for matching
        base_destination = self._extract_base_destination(destination_name)
        
        # Retrieve POIs (destinations)
        poi_facts = self._get_poi_facts(base_destination)
        facts.extend(poi_facts)
        
        # Retrieve hotels
        hotel_facts = self._get_hotel_facts(base_destination, slots)
        facts.extend(hotel_facts)
        
        # Retrieve activities/tours
        activity_facts = self._get_activity_facts(base_destination)
        facts.extend(activity_facts)
        
        # Sort by confidence and return top results
        facts.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return facts[:20]  # Return top 20 facts
    
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