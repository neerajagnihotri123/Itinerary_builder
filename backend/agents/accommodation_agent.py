"""
Accommodation Agent - Scores and ranks hotel recommendations
"""
import math
from typing import List, Dict, Any

class AccommodationAgent:
    """Handles hotel scoring and ranking based on user preferences"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Mock hotel data for Indian destinations
        self.mock_hotels = [
            # Andaman Islands Hotels
            {
                "id": "hotel_andaman_1",
                "destination_id": "andaman_islands",
                "name": "Barefoot at Havelock",
                "hero_image": "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=400&fit=crop",
                "rating": 4.8,
                "price_estimate": 7000,
                "hotel_type": "Eco Resort",
                "amenities": ["Beach Access", "Spa", "Restaurant", "Diving Center"],
                "location": "Havelock Island",
                "distance_to_day1_km": 0.5
            },
            {
                "id": "hotel_andaman_2", 
                "destination_id": "andaman_islands",
                "name": "Taj Exotica Resort & Spa",
                "hero_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&h=400&fit=crop",
                "rating": 4.9,
                "price_estimate": 20000,
                "hotel_type": "Luxury Resort",
                "amenities": ["Private Beach", "Spa", "Fine Dining", "Water Sports"],
                "location": "Radhanagar Beach, Havelock",
                "distance_to_day1_km": 1.2
            },
            # Manali Hotels
            {
                "id": "hotel_manali_1",
                "destination_id": "manali_himachal",
                "name": "The Himalayan",
                "hero_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop",
                "rating": 4.7,
                "price_estimate": 11500,
                "hotel_type": "Mountain Resort",
                "amenities": ["Mountain Views", "Spa", "Adventure Sports", "Fireplace"],
                "location": "Hadimba Road, Manali",
                "distance_to_day1_km": 2.0
            },
            {
                "id": "hotel_manali_2",
                "destination_id": "manali_himachal", 
                "name": "Hotel Snow Valley Resorts",
                "hero_image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&h=400&fit=crop",
                "rating": 4.4,
                "price_estimate": 4500,
                "hotel_type": "Mid-Range",
                "amenities": ["Valley Views", "Restaurant", "Room Service", "Travel Desk"],
                "location": "Mall Road, Manali",
                "distance_to_day1_km": 1.5
            },
            # Rishikesh Hotels
            {
                "id": "hotel_rishikesh_1",
                "destination_id": "rishikesh_uttarakhand",
                "name": "Ananda in the Himalayas",
                "hero_image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=600&h=400&fit=crop",
                "rating": 4.9,
                "price_estimate": 27500,
                "hotel_type": "Luxury Spa Resort",
                "amenities": ["Spa", "Yoga", "Meditation", "Gourmet Dining"],
                "location": "Narendra Nagar, Rishikesh",
                "distance_to_day1_km": 8.0
            },
            {
                "id": "hotel_rishikesh_2",
                "destination_id": "rishikesh_uttarakhand",
                "name": "Camp 5 Elements",
                "hero_image": "https://images.unsplash.com/photo-1504197885-8d8c99d1b3b3?w=600&h=400&fit=crop", 
                "rating": 4.5,
                "price_estimate": 3500,
                "hotel_type": "Adventure Camp",
                "amenities": ["Riverside Location", "Adventure Activities", "Bonfire", "Organic Food"],
                "location": "Shivpuri, Rishikesh",
                "distance_to_day1_km": 15.0
            },
            # Kerala Hotels
            {
                "id": "hotel_kerala_1",
                "destination_id": "kerala_backwaters",
                "name": "Kumarakom Lake Resort",
                "hero_image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=600&h=400&fit=crop",
                "rating": 4.8,
                "price_estimate": 15000,
                "hotel_type": "Heritage Resort",
                "amenities": ["Backwater Views", "Ayurvedic Spa", "Traditional Architecture", "Houseboat"],
                "location": "Kumarakom, Kerala",
                "distance_to_day1_km": 5.0
            },
            # Goa Hotels
            {
                "id": "hotel_goa_1",
                "destination_id": "goa_india",
                "name": "Taj Exotica Goa",
                "hero_image": "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=400&fit=crop",
                "rating": 4.8,
                "price_estimate": 12000,
                "hotel_type": "Beach Resort",
                "amenities": ["Beach Access", "Spa", "Multiple Restaurants", "Water Sports"],
                "location": "Benaulim Beach, South Goa",
                "distance_to_day1_km": 2.0
            },
            {
                "id": "hotel_goa_2",
                "destination_id": "goa_india",
                "name": "The Leela Goa",
                "hero_image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=600&h=400&fit=crop",
                "rating": 4.9,
                "price_estimate": 18000,
                "hotel_type": "Luxury Resort",
                "amenities": ["Private Beach", "Golf Course", "Spa", "Fine Dining"],
                "location": "Cavelossim Beach, South Goa",
                "distance_to_day1_km": 1.0
            }
        ]
    
    async def rank_hotels(self, hotels: List[Dict[str, Any]], slots) -> List[Dict[str, Any]]:
        """
        Score and rank hotels based on user preferences
        Returns: Top 3 ranked hotels with scores and reasons
        """
        if not hotels:
            return []
        
        # Score each hotel
        scored_hotels = []
        for hotel in hotels:
            score = self._calculate_hotel_score(hotel, slots)
            reason = self._generate_reason(hotel, slots, score)
            
            scored_hotel = {
                "id": hotel.get('id', ''),
                "name": hotel.get('name', ''),
                "price_estimate": hotel.get('price_estimate', 5000),
                "score": score,
                "reason": reason,
                "distance_to_day1_km": hotel.get('distance_to_day1_km', 2.0),  # Mock distance
                "amenities": hotel.get('amenities', []),
                "booking_link_estimate": True,
                "rating": hotel.get('rating', 4.0),
                "estimated": True  # Mark as estimated since we're using mock data
            }
            scored_hotels.append(scored_hotel)
        
        # Sort by score and return top 3
        scored_hotels.sort(key=lambda x: x['score'], reverse=True)
        return scored_hotels[:3]
    
    def _calculate_hotel_score(self, hotel: Dict[str, Any], slots) -> float:
        """
        Calculate hotel score based on: preference_match (40%), rating (25%), proximity (20%), price (15%)
        """
        score = 0.0
        
        # Preference match (40%)
        preference_score = self._calculate_preference_match(hotel, slots)
        score += preference_score * 0.4
        
        # Rating (25%)
        rating = hotel.get('rating', 4.0)
        rating_score = min(rating / 5.0, 1.0)  # Normalize to 0-1
        score += rating_score * 0.25
        
        # Proximity (20%) - closer to city center/attractions is better
        distance = hotel.get('distance_to_day1_km', 2.0)
        proximity_score = max(0, 1.0 - (distance / 10.0))  # Assume 10km is max reasonable distance
        score += proximity_score * 0.20
        
        # Price match (15%)
        price_score = self._calculate_price_match(hotel, slots)
        score += price_score * 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_preference_match(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate how well hotel matches user preferences"""
        score = 0.5  # Base score
        
        hotel_type = hotel.get('hotel_type', '').lower()
        amenities = [a.lower() for a in hotel.get('amenities', [])]
        
        # Family preferences
        if slots.children > 0:
            if any(amenity in amenities for amenity in ['family room', 'kids club', 'playground', 'family activities']):
                score += 0.3
            if 'pool' in amenities or 'swimming' in ' '.join(amenities):
                score += 0.2
        
        # Business/luxury preferences based on budget
        if slots.budget_per_night and slots.budget_per_night > 8000:  # High budget in INR
            if 'luxury' in hotel_type or 'resort' in hotel_type:
                score += 0.3
            if any(amenity in amenities for amenity in ['spa', 'concierge', 'business center', 'fine dining']):
                score += 0.2
        
        # Budget preferences
        elif slots.budget_per_night and slots.budget_per_night < 3000:  # Budget in INR
            if 'budget' in hotel_type or 'hostel' in hotel_type:
                score += 0.2
            if 'free wifi' in amenities or 'free breakfast' in amenities:
                score += 0.3
        
        # Adventure travelers
        if any(word in (slots.destination or '').lower() for word in ['rishikesh', 'manali', 'ladakh']):
            if any(amenity in amenities for amenity in ['adventure sports', 'trekking', 'outdoor activities']):
                score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_price_match(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate price compatibility score"""
        hotel_price = hotel.get('price_estimate', 5000)
        
        if not slots.budget_per_night:
            return 0.7  # Neutral score if no budget specified
        
        budget = slots.budget_per_night
        
        # Perfect match at exact budget
        if hotel_price <= budget:
            return 1.0
        
        # Gradual decrease for over-budget hotels
        over_budget_ratio = (hotel_price - budget) / budget
        if over_budget_ratio <= 0.2:  # Within 20% of budget
            return 0.8
        elif over_budget_ratio <= 0.5:  # Within 50% of budget
            return 0.5
        else:
            return 0.2  # Significantly over budget
    
    def _generate_reason(self, hotel: Dict[str, Any], slots, score: float) -> str:
        """Generate explanation for why this hotel was recommended"""
        reasons = []
        
        # Rating reason
        rating = hotel.get('rating', 4.0)
        if rating >= 4.5:
            reasons.append(f"Excellent {rating}★ rating")
        elif rating >= 4.0:
            reasons.append(f"Great {rating}★ rating")
        
        # Price reason
        if slots.budget_per_night:
            hotel_price = hotel.get('price_estimate', 5000)
            if hotel_price <= slots.budget_per_night:
                reasons.append("Within your budget")
            elif hotel_price <= slots.budget_per_night * 1.2:
                reasons.append("Close to your budget range")
        
        # Amenities reason
        amenities = hotel.get('amenities', [])
        if slots.children > 0 and any('family' in a.lower() or 'kids' in a.lower() for a in amenities):
            reasons.append("Family-friendly amenities")
        
        if any('spa' in a.lower() or 'wellness' in a.lower() for a in amenities):
            reasons.append("Spa and wellness facilities")
        
        if any('free' in a.lower() for a in amenities):
            reasons.append("Great value with free amenities")
        
        # Location reason
        distance = hotel.get('distance_to_day1_km', 2.0)
        if distance <= 1.0:
            reasons.append("Prime location")
        elif distance <= 3.0:
            reasons.append("Convenient location")
        
        # Score-based reason
        if score >= 0.9:
            reasons.append("Perfect match for your needs")
        elif score >= 0.8: 
            reasons.append("Excellent choice for your trip")
        elif score >= 0.7:
            reasons.append("Good option for your preferences")
        
        # Combine reasons
        if reasons:
            return ". ".join(reasons[:3])  # Limit to 3 reasons
        else:
            return f"Quality {hotel.get('hotel_type', 'accommodation')} option"