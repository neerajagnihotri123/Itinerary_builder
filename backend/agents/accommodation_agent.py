"""
Accommodation Agent - Hotel scoring, ranking, availability checks, and booking flow
"""
import math
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class AccommodationAgent:
    """
    Handles hotel scoring, ranking, availability checks, and booking flow.
    Scoring factors: normalized price, rating, distance to POIs, amenity match, 
    cancellation flexibility, recency of reviews.
    Never returns payment credentials to frontend.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        # Scoring weights
        self.scoring_weights = {
            'price': 0.25,      # 25% - normalized price match
            'rating': 0.20,     # 20% - hotel rating
            'distance': 0.15,   # 15% - distance to POIs
            'amenities': 0.20,  # 20% - amenity match
            'flexibility': 0.10, # 10% - cancellation flexibility 
            'reviews': 0.10     # 10% - recency of reviews
        }
    
    async def get_hotels_for_destination(self, destination: str, slots) -> List[Dict[str, Any]]:
        """
        Get hotel recommendations with comprehensive scoring and ranking
        Returns: List of scored and ranked hotels with availability info
        """
        if not destination:
            return []
        
        print(f"🏨 Getting hotels for {destination}")
        
        # Step 1: Get raw hotel data (LLM + fallback)
        raw_hotels = await self._fetch_hotel_data(destination, slots)
        
        if not raw_hotels:
            return []
        
        # Step 2: Check availability for all hotels
        available_hotels = await self._check_hotel_availability(raw_hotels, slots)
        
        # Step 3: Score and rank hotels using comprehensive factors
        scored_hotels = await self._score_and_rank_hotels(available_hotels, slots)
        
        # Step 4: Limit to top results and add booking metadata
        final_hotels = self._prepare_final_hotel_list(scored_hotels)
        
        print(f"✅ Returning {len(final_hotels)} scored and ranked hotels")
        return final_hotels
    
    async def _fetch_hotel_data(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Fetch hotel data from LLM and fallback sources"""
        hotels = []
        
        try:
            # Try LLM generation first
            llm_hotels = await self._generate_hotels_with_llm(destination, slots)
            if llm_hotels:
                hotels.extend(llm_hotels)
        except Exception as e:
            print(f"❌ LLM hotel generation failed: {e}")
        
        # Always add fallback hotels for diversity
        fallback_hotels = await self._get_fallback_hotels(destination, slots)
        hotels.extend(fallback_hotels)
        
        # Remove duplicates by name
        unique_hotels = {}
        for hotel in hotels:
            hotel_key = hotel.get('name', '').lower().replace(' ', '')
            if hotel_key not in unique_hotels:
                unique_hotels[hotel_key] = hotel
        
        return list(unique_hotels.values())
    
    async def _check_hotel_availability(self, hotels: List[Dict[str, Any]], slots) -> List[Dict[str, Any]]:
        """
        Check availability for hotels based on dates and travelers
        Returns hotels with availability status
        """
        available_hotels = []
        
        for hotel in hotels:
            # Simulate availability check (in real system, this would call hotel APIs)
            availability_result = self._simulate_availability_check(hotel, slots)
            
            hotel_with_availability = {
                **hotel,
                'availability': availability_result['available'],
                'availability_details': availability_result,
                'last_availability_check': datetime.now(timezone.utc).isoformat()
            }
            
            # Only include available hotels
            if availability_result['available']:
                available_hotels.append(hotel_with_availability)
            else:
                print(f"   🚫 {hotel.get('name', 'Hotel')} not available")
        
        print(f"   📅 {len(available_hotels)}/{len(hotels)} hotels available")
        return available_hotels
    
    def _simulate_availability_check(self, hotel: Dict[str, Any], slots) -> Dict[str, Any]:
        """Simulate availability check (replace with real API calls)"""
        
        # Simulate availability based on hotel characteristics
        base_availability = 0.85  # 85% base availability
        
        # Reduce availability for luxury hotels (more exclusive)
        if 'luxury' in hotel.get('hotel_type', '').lower():
            base_availability *= 0.7
        
        # Reduce availability for high-rated hotels
        rating = hotel.get('rating', 4.0)
        if rating > 4.5:
            base_availability *= 0.8
        
        # Check if dates affect availability
        is_available = hash(hotel.get('name', '')) % 100 < (base_availability * 100)
        
        return {
            'available': is_available,
            'rooms_available': 3 if is_available else 0,
            'cancellation_policy': 'Free cancellation up to 24 hours before check-in' if is_available else None,
            'flexibility_score': 0.8 if is_available else 0,
            'booking_deadline': (datetime.now() + timedelta(hours=6)).isoformat() if is_available else None
        }
    
    async def _score_and_rank_hotels(self, hotels: List[Dict[str, Any]], slots) -> List[Dict[str, Any]]:
        """
        Score and rank hotels using comprehensive factors:
        - Normalized price (25%), Rating (20%), Distance to POIs (15%)
        - Amenity match (20%), Cancellation flexibility (10%), Review recency (10%)
        """
        scored_hotels = []
        
        for hotel in hotels:
            # Calculate individual scores
            price_score = self._calculate_price_score(hotel, slots)
            rating_score = self._calculate_rating_score(hotel)
            distance_score = self._calculate_distance_score(hotel, slots)
            amenity_score = self._calculate_amenity_score(hotel, slots)
            flexibility_score = self._calculate_flexibility_score(hotel)
            reviews_score = self._calculate_reviews_score(hotel)
            
            # Calculate weighted total score
            total_score = (
                price_score * self.scoring_weights['price'] +
                rating_score * self.scoring_weights['rating'] +
                distance_score * self.scoring_weights['distance'] +
                amenity_score * self.scoring_weights['amenities'] +
                flexibility_score * self.scoring_weights['flexibility'] +
                reviews_score * self.scoring_weights['reviews']
            )
            
            # Add scoring details to hotel
            scored_hotel = {
                **hotel,
                'total_score': round(total_score, 3),
                'score_breakdown': {
                    'price_score': round(price_score, 2),
                    'rating_score': round(rating_score, 2),
                    'distance_score': round(distance_score, 2),
                    'amenity_score': round(amenity_score, 2),
                    'flexibility_score': round(flexibility_score, 2),
                    'reviews_score': round(reviews_score, 2)
                },
                'ranking_reason': self._generate_ranking_reason(hotel, total_score, slots)
            }
            
            scored_hotels.append(scored_hotel)
        
        # Sort by total score (descending)
        scored_hotels.sort(key=lambda h: h['total_score'], reverse=True)
        
        print(f"   📊 Hotels scored and ranked by comprehensive factors")
        return scored_hotels
    
    async def _generate_hotels_with_llm(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Use LLM to generate hotel recommendations"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for hotel recommendations
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"hotels_{hash(destination) % 10000}",
                system_message="You are a hotel recommendation expert. Generate accurate, detailed hotel recommendations in JSON format."
            ).with_model("openai", "gpt-4o-mini")
            
            # Create hotel recommendation context
            context = self._prepare_hotel_context(destination, slots)
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse the JSON response
            try:
                hotels_data = json.loads(content)
                parsed_hotels = self._parse_llm_hotels(hotels_data.get('hotels', []), destination, slots)
                print(f"✅ LLM generated {len(parsed_hotels)} hotels for {destination}")
                return parsed_hotels
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from LLM hotel generation")
                return []
                
        except Exception as e:
            print(f"❌ LLM hotel generation error: {e}")
            return []
    
    def _prepare_hotel_context(self, destination: str, slots) -> str:
        """Prepare context for LLM hotel generation"""
        budget_info = f"Budget: ₹{getattr(slots, 'budget_per_night', 8000)} per night" if getattr(slots, 'budget_per_night', None) else "Budget: Mid-range"
        travelers = f"{getattr(slots, 'adults', 2)} adults"
        if getattr(slots, 'children', 0) > 0:
            travelers += f", {getattr(slots, 'children', 0)} children"
        
        return f"""
Generate hotel recommendations for {destination} based on:

User Requirements:
- Destination: {destination}
- Travelers: {travelers}
- {budget_info}
- Dates: {getattr(slots, 'start_date', 'Flexible')} to {getattr(slots, 'end_date', 'Flexible')}

Generate JSON with this structure:
{{
  "hotels": [
    {{
      "id": "unique_hotel_id",
      "name": "Hotel Name",
      "location": "Specific area/neighborhood",
      "rating": 4.5,
      "price_estimate": 8000,
      "hotel_type": "Luxury Resort/Heritage Hotel/Budget Hotel/etc",
      "amenities": ["Free WiFi", "Swimming Pool", "Spa", "Restaurant"],
      "hero_image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop",
      "distance_to_center_km": 2.5,
      "description": "Brief compelling description",
      "booking_available": true,
      "score_reason": "Why this hotel is recommended"
    }}
  ]
}}

Requirements:
- Generate 3-5 hotels that match the user's profile
- Include mix of budget ranges around the specified budget
- Use realistic Indian hotel names and pricing (in INR)
- Include family-friendly options if children are mentioned
- Focus on hotels in {destination} with accurate locations
- Provide high-quality Unsplash image URLs
- Consider proximity to major attractions
- Include compelling reasons for each recommendation

Ensure prices are realistic for {destination} and match the budget tier.
"""
    
    def _parse_llm_hotels(self, hotels_data: List[Dict], destination: str, slots) -> List[Dict[str, Any]]:
        """Parse LLM-generated hotels into standard format"""
        parsed_hotels = []
        
        for hotel in hotels_data:
            # Calculate intelligent score based on LLM data and user preferences
            score = self._calculate_llm_hotel_score(hotel, slots)
            
            parsed_hotel = {
                "id": hotel.get('id', f"hotel_{hash(hotel.get('name', '')) % 10000}"),
                "name": hotel.get('name', ''),
                "price_estimate": hotel.get('price_estimate', 5000),
                "score": score,
                "reason": hotel.get('score_reason', 'Great choice for your trip'),
                "distance_to_day1_km": hotel.get('distance_to_center_km', 2.0),
                "amenities": hotel.get('amenities', []),
                "booking_link_estimate": hotel.get('booking_available', True),
                "rating": hotel.get('rating', 4.0),
                "estimated": False,  # LLM-generated data is considered accurate
                "hero_image": hotel.get('hero_image', ''),
                "location": hotel.get('location', destination),
                "hotel_type": hotel.get('hotel_type', 'Hotel'),
                "description": hotel.get('description', '')
            }
            parsed_hotels.append(parsed_hotel)
        
        # Sort by score and return top 3
        parsed_hotels.sort(key=lambda x: x['score'], reverse=True)
        return parsed_hotels[:3]
    
    def _calculate_llm_hotel_score(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate hotel score for LLM-generated hotels"""
        score = 0.7  # Base score for LLM-generated hotels
        
        # Rating bonus
        rating = hotel.get('rating', 4.0)
        score += (rating - 3.0) / 2.0 * 0.2  # Rating contributes up to 0.2
        
        # Budget match bonus
        hotel_price = hotel.get('price_estimate', 5000)
        if getattr(slots, 'budget_per_night', None):
            budget = slots.budget_per_night
            if hotel_price <= budget:
                score += 0.15
            elif hotel_price <= budget * 1.2:  # Within 20% of budget
                score += 0.1
            elif hotel_price > budget * 1.5:  # Significantly over budget
                score -= 0.1
        
        # Family-friendly bonus
        if getattr(slots, 'children', 0) > 0:
            amenities = [a.lower() for a in hotel.get('amenities', [])]
            if any('family' in a or 'kids' in a or 'pool' in a for a in amenities):
                score += 0.1
        
        # Luxury preference (high budget)
        if getattr(slots, 'budget_per_night', 0) > 10000:
            if any(word in hotel.get('hotel_type', '').lower() for word in ['luxury', 'resort', 'heritage']):
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _get_fallback_hotels(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Enhanced fallback using improved mock data logic"""
        destination_lower = destination.lower()
        
        # Map destination names to destination IDs (keeping existing logic)
        destination_mapping = {
            "andaman": "andaman_islands",
            "andaman islands": "andaman_islands", 
            "havelock": "andaman_islands",
            "manali": "manali_himachal",
            "himachal": "manali_himachal",
            "rishikesh": "rishikesh_uttarakhand",
            "uttarakhand": "rishikesh_uttarakhand",
            "kerala": "kerala_backwaters",
            "goa": "goa_india"
        }
        
        # Find matching destination ID
        destination_id = None
        for dest_name, dest_id in destination_mapping.items():
            if dest_name in destination_lower:
                destination_id = dest_id
                break
        
        if not destination_id:
            print(f"🏨 No fallback hotels found for destination: {destination}")
            return []
        
        # Filter hotels for this destination (using existing mock data)
        destination_hotels = [
            hotel for hotel in self._get_mock_hotels() 
            if hotel.get("destination_id") == destination_id
        ]
        
        if not destination_hotels:
            print(f"🏨 No fallback hotels available for destination_id: {destination_id}")
            return []
        
        print(f"🔄 Using fallback hotels: {len(destination_hotels)} hotels for {destination}")
        
        # Rank the hotels using existing ranking logic
        ranked_hotels = await self.rank_hotels(destination_hotels, slots)
        
        return ranked_hotels
    
    def _get_mock_hotels(self) -> List[Dict[str, Any]]:
        """Get the existing mock hotel data"""
        return [
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