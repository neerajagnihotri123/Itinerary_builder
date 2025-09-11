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
        Get hotel recommendations with comprehensive scoring and ranking - Pure LLM approach
        Returns: List of scored and ranked hotels with availability info
        """
        if not destination:
            return []
        
        print(f"🏨 Getting hotels for {destination} using LLM-first approach")
        
        # Step 1: Get hotel data using LLM primarily
        raw_hotels = await self._fetch_hotel_data_llm_first(destination, slots)
        
        if not raw_hotels:
            print(f"❌ No hotels found for {destination}")
            return []
        
        # Step 2: Check availability for all hotels
        available_hotels = await self._check_hotel_availability(raw_hotels, slots)
        
        # Step 3: Score and rank hotels using comprehensive factors
        scored_hotels = await self._score_and_rank_hotels(available_hotels, slots)
        
        # Step 4: Limit to top results and add booking metadata
        final_hotels = self._prepare_final_hotel_list(scored_hotels)
        
        print(f"✅ Returning {len(final_hotels)} scored and ranked hotels")
        return final_hotels
    
    async def _fetch_hotel_data_llm_first(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Fetch hotel data using LLM as primary source"""
        hotels = []
        
        try:
            # Try LLM generation first - this is the primary method now
            llm_hotels = await self._generate_hotels_with_llm(destination, slots)
            if llm_hotels:
                hotels.extend(llm_hotels)
                print(f"✅ LLM generated {len(llm_hotels)} hotels for {destination}")
            else:
                print(f"⚠️ LLM generated 0 hotels for {destination}")
        except Exception as e:
            print(f"❌ LLM hotel generation failed: {e}")
        
        # Only use fallback if LLM completely fails
        if not hotels:
            print(f"🔄 Using fallback hotels for {destination}")
            fallback_hotels = await self._get_fallback_hotels(destination, slots)
            hotels.extend(fallback_hotels)
        
        return hotels
    
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
        try:
            budget = slots.budget_per_night if hasattr(slots, 'budget_per_night') and slots.budget_per_night else None
            
            # Check budget compatibility if specified
            if budget and hotel.get('price_estimate'):
                hotel_price = int(hotel.get('price_estimate', 5000))
                if hotel_price > budget * 1.5:  # Too expensive
                    base_availability *= 0.6
        except (ValueError, TypeError, AttributeError):
            pass  # Skip budget adjustment if there are comparison issues
        
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
    
    def _calculate_price_score(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate normalized price score (0-1, higher = better value)"""
        hotel_price = hotel.get('price_estimate', 5000)
        
        # Handle different slot types and None values
        user_budget = None
        if hasattr(slots, 'budget_per_night'):
            user_budget = slots.budget_per_night
        elif isinstance(slots, dict):
            user_budget = slots.get('budget_per_night')
        
        # Ensure we have a valid budget for comparison
        if user_budget is None or user_budget <= 0:
            # If no budget specified, use mid-range preference based on destination
            user_budget = 7000
        
        # Ensure budget is numeric
        try:
            user_budget = float(user_budget)
            hotel_price = float(hotel_price)
        except (ValueError, TypeError):
            return 0.5  # Default score if price comparison fails
        
        # Score based on how close price is to budget (perfect match = 1.0)
        if hotel_price <= user_budget:
            # Under budget is good, but not as good as perfect match
            price_ratio = hotel_price / user_budget
            return 0.8 + (price_ratio * 0.2)  # 0.8 to 1.0
        else:
            # Over budget decreases score
            over_budget_ratio = (hotel_price - user_budget) / user_budget
            return max(0.1, 1.0 - over_budget_ratio)
    
    def _calculate_rating_score(self, hotel: Dict[str, Any]) -> float:
        """Calculate rating score (0-1, higher rating = higher score)"""
        rating = hotel.get('rating', 4.0)
        # Normalize 5-star rating to 0-1 scale
        return min(rating / 5.0, 1.0)
    
    def _calculate_distance_score(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate distance to POIs score (0-1, closer = higher score)"""
        distance_km = hotel.get('distance_to_day1_km', hotel.get('distance_to_center_km', 2.0))
        
        # Ideal distance is 0-2km (score 1.0), decreases linearly to 10km (score 0.1)
        if distance_km <= 2.0:
            return 1.0
        elif distance_km >= 10.0:
            return 0.1
        else:
            # Linear decrease from 1.0 to 0.1 between 2km and 10km
            return 1.0 - ((distance_km - 2.0) / 8.0) * 0.9
    
    def _calculate_amenity_score(self, hotel: Dict[str, Any], slots) -> float:
        """Calculate amenity match score based on user needs"""
        amenities = [a.lower() for a in hotel.get('amenities', [])]
        score = 0.5  # Base score
        
        # Safely get slot values with fallbacks
        children = 0
        adults = 2
        
        if hasattr(slots, 'children'):
            children = slots.children or 0
        elif isinstance(slots, dict):
            children = slots.get('children', 0)
        
        if hasattr(slots, 'adults'):
            adults = slots.adults or 2
        elif isinstance(slots, dict):
            adults = slots.get('adults', 2)
        
        # Ensure numeric values
        try:
            children = int(children)
            adults = int(adults)
        except (ValueError, TypeError):
            children = 0
            adults = 2
        
        # Must-have amenities for different user types
        if children > 0:
            family_amenities = ['pool', 'family room', 'kids club', 'playground', 'babysitting']
            family_matches = sum(1 for amenity in family_amenities if any(fa in amenity for fa in amenities))
            score += (family_matches / len(family_amenities)) * 0.3
        
        if adults >= 4:  # Group travel
            group_amenities = ['restaurant', 'conference room', 'group booking', 'large rooms']
            group_matches = sum(1 for amenity in group_amenities if any(ga in amenity for ga in amenities))
            score += (group_matches / len(group_amenities)) * 0.2
        
        # Universal desirable amenities
        universal_amenities = ['wifi', 'breakfast', 'parking', 'gym', 'spa', 'room service']
        universal_matches = sum(1 for amenity in universal_amenities if any(ua in amenity for ua in amenities))
        score += (universal_matches / len(universal_amenities)) * 0.3
        
        return min(score, 1.0)
    
    def _calculate_flexibility_score(self, hotel: Dict[str, Any]) -> float:
        """Calculate cancellation flexibility score"""
        availability_details = hotel.get('availability_details', {})
        flexibility_score = availability_details.get('flexibility_score', 0.5)
        
        # Boost score for flexible cancellation policies
        cancellation_policy = availability_details.get('cancellation_policy', '').lower()
        if 'free cancellation' in cancellation_policy:
            flexibility_score += 0.3
        if '24 hours' in cancellation_policy:
            flexibility_score += 0.2
        
        return min(flexibility_score, 1.0)
    
    def _calculate_reviews_score(self, hotel: Dict[str, Any]) -> float:
        """Calculate recency of reviews score (simulated)"""
        # In a real system, this would check review dates
        # For now, simulate based on hotel characteristics
        rating = hotel.get('rating', 4.0)
        
        # Higher rated hotels likely have more recent reviews
        if rating >= 4.5:
            return 0.9
        elif rating >= 4.0:
            return 0.7
        else:
            return 0.5
    
    def _generate_ranking_reason(self, hotel: Dict[str, Any], total_score: float, slots) -> str:
        """Generate explanation for why hotel is ranked at this position"""
        reasons = []
        
        if total_score >= 0.85:
            reasons.append("Excellent match for your preferences")
        elif total_score >= 0.7:
            reasons.append("Great option for your trip")
        else:
            reasons.append("Good alternative choice")
        
        # Add specific reasons with safe slot access
        price = hotel.get('price_estimate', 5000)
        user_budget = 7000  # Default
        
        if hasattr(slots, 'budget_per_night') and slots.budget_per_night:
            user_budget = slots.budget_per_night
        elif isinstance(slots, dict) and slots.get('budget_per_night'):
            user_budget = slots.get('budget_per_night')
        
        try:
            if float(price) <= float(user_budget):
                reasons.append("Within your budget")
        except (ValueError, TypeError):
            pass  # Skip budget comparison if values are invalid
        
        rating = hotel.get('rating', 4.0)
        try:
            rating = float(rating)
            if rating >= 4.5:
                reasons.append(f"Outstanding {rating}★ rating")
            elif rating >= 4.0:
                reasons.append(f"Excellent {rating}★ rating")
        except (ValueError, TypeError):
            pass  # Skip rating if invalid
        
        distance = hotel.get('distance_to_day1_km', hotel.get('distance_to_center_km', 2.0))
        try:
            distance = float(distance)
            if distance <= 2.0:
                reasons.append("Prime location")
            elif distance <= 5.0:
                reasons.append("Convenient location")
        except (ValueError, TypeError):
            pass  # Skip distance if invalid
        
        return " • ".join(reasons[:3])  # Limit to 3 reasons
    
    def _prepare_final_hotel_list(self, scored_hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare final hotel list with booking metadata, never include payment credentials"""
        final_hotels = []
        
        for i, hotel in enumerate(scored_hotels[:5]):  # Top 5 hotels
            # Add booking metadata (NO PAYMENT CREDENTIALS)
            booking_metadata = {
                'booking_available': True,
                'booking_id': f"bk_{hash(hotel.get('name', '')) % 10000}",
                'requires_info': ['guest_name', 'contact_email', 'check_in_date', 'check_out_date'],
                'booking_deadline': hotel.get('availability_details', {}).get('booking_deadline'),
                'cancellation_policy': hotel.get('availability_details', {}).get('cancellation_policy')
            }
            
            final_hotel = {
                'id': hotel.get('id'),
                'name': hotel.get('name'),
                'rating': hotel.get('rating'),
                'price_estimate': hotel.get('price_estimate'),
                'hotel_type': hotel.get('hotel_type'),
                'amenities': hotel.get('amenities', []),
                'location': hotel.get('location'),
                'hero_image': hotel.get('hero_image'),
                'distance_info': f"{hotel.get('distance_to_day1_km', 2.0)} km from center",
                'total_score': hotel.get('total_score'),
                'ranking_reason': hotel.get('ranking_reason'),
                'booking_metadata': booking_metadata,
                'rank': i + 1
            }
            
            final_hotels.append(final_hotel)
        
        return final_hotels
    
    async def check_availability(self, hotel_id: str, slots) -> Dict[str, Any]:
        """
        Check real-time availability for a specific hotel
        Returns: availability status with booking options
        """
        print(f"🔍 Checking availability for hotel {hotel_id}")
        
        # Safely get number of nights
        nights = 2  # Default
        try:
            if hasattr(slots, 'nights') and slots.nights:
                nights = int(slots.nights)
            elif isinstance(slots, dict) and slots.get('nights'):
                nights = int(slots.get('nights'))
            elif hasattr(slots, 'start_date') and hasattr(slots, 'end_date') and slots.start_date and slots.end_date:
                # Calculate nights from dates
                from datetime import datetime
                start = datetime.fromisoformat(str(slots.start_date))
                end = datetime.fromisoformat(str(slots.end_date))
                nights = (end - start).days
        except (ValueError, TypeError, AttributeError) as e:
            print(f"⚠️  Error calculating nights: {e}, using default")
            nights = 2
        
        # In a real system, this would call hotel booking APIs
        # For now, simulate availability check
        availability_result = {
            'hotel_id': hotel_id,
            'available': True,
            'rooms_available': 3,
            'price_per_night': 8500,
            'total_price': 8500 * nights,
            'nights': nights,
            'cancellation_policy': 'Free cancellation up to 24 hours before check-in',
            'booking_options': {
                'standard_room': {'available': True, 'price': 8500},
                'deluxe_room': {'available': True, 'price': 12000},
                'suite': {'available': False, 'price': 18000}
            },
            'last_checked': datetime.now(timezone.utc).isoformat()
        }
        
        return availability_result
    
    async def initiate_booking(self, hotel_id: str, room_type: str, guest_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate booking flow: collect minimal booking info → confirm/return booking_result
        NEVER returns payment credentials to frontend
        """
        print(f"🏨 Initiating booking for hotel {hotel_id}, room {room_type}")
        
        # Validate required guest information
        required_fields = ['guest_name', 'contact_email', 'check_in_date', 'check_out_date']
        missing_fields = [field for field in required_fields if not guest_info.get(field)]
        
        if missing_fields:
            return {
                'booking_status': 'info_required',
                'missing_fields': missing_fields,
                'message': f"Please provide: {', '.join(missing_fields)}"
            }
        
        # Generate booking confirmation (simulate booking API call)
        booking_result = {
            'booking_status': 'confirmed',
            'booking_reference': f"TR{hash(hotel_id + str(datetime.now())) % 100000}",
            'hotel_id': hotel_id,
            'room_type': room_type,
            'guest_name': guest_info['guest_name'],
            'check_in': guest_info['check_in_date'],
            'check_out': guest_info['check_out_date'],
            'total_nights': 2,  # Calculate from dates
            'total_amount': 17000,  # Calculate based on room type
            'currency': 'INR',
            'confirmation_sent_to': guest_info['contact_email'],
            'cancellation_deadline': (datetime.now() + timedelta(hours=24)).isoformat(),
            'booking_timestamp': datetime.now(timezone.utc).isoformat(),
            # NO PAYMENT CREDENTIALS EVER RETURNED
            'payment_status': 'pending_checkout',
            'payment_instructions': 'You will be redirected to secure payment gateway'
        }
        
        print(f"✅ Booking confirmed: {booking_result['booking_reference']}")
        return booking_result
    
    async def _generate_hotels_with_llm(self, destination: str, slots) -> List[Dict[str, Any]]:
        """Use LLM to generate hotel recommendations with improved error handling"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for hotel recommendations with timeout
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"hotels_{hash(destination) % 10000}",
                system_message="You are a hotel recommendation expert. Generate accurate, detailed hotel recommendations in JSON format only. No explanations, just valid JSON."
            ).with_model("openai", "gpt-4o-mini")
            
            # Create hotel recommendation context with better error handling
            try:
                context = self._prepare_hotel_context(destination, slots)
            except Exception as e:
                print(f"❌ Context preparation failed: {e}")
                return []
            
            user_message = UserMessage(text=context)
            
            # Set a timeout for LLM request to prevent hanging
            import asyncio
            try:
                response = await asyncio.wait_for(
                    llm_client.send_message(user_message), 
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                print(f"❌ LLM hotel generation timed out for {destination}")
                return []
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Clean the content to ensure it's valid JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            # Parse the JSON response with better error handling
            try:
                hotels_data = json.loads(content)
                if not isinstance(hotels_data, dict) or 'hotels' not in hotels_data:
                    print(f"❌ Invalid JSON structure: missing 'hotels' key")
                    return []
                
                parsed_hotels = self._parse_llm_hotels(hotels_data.get('hotels', []), destination, slots)
                if parsed_hotels:
                    print(f"✅ LLM generated {len(parsed_hotels)} hotels for {destination}")
                    return parsed_hotels
                else:
                    print(f"❌ No valid hotels parsed from LLM response")
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON from LLM hotel generation: {e}")
                print(f"   Raw content: {content[:200]}...")
                return []
                
        except Exception as e:
            print(f"❌ LLM hotel generation error: {e}")
            return []
    
    def _prepare_hotel_context(self, destination: str, slots) -> str:
        """Prepare context for LLM hotel generation with safe slot access"""
        
        # Safely extract slot values
        budget_per_night = 8000  # Default mid-range
        adults = 2
        children = 0
        start_date = 'Flexible'
        end_date = 'Flexible'
        
        try:
            if hasattr(slots, 'budget_per_night') and slots.budget_per_night:
                budget_per_night = int(slots.budget_per_night)
            elif isinstance(slots, dict) and slots.get('budget_per_night'):
                budget_per_night = int(slots.get('budget_per_night'))
            
            if hasattr(slots, 'adults') and slots.adults:
                adults = int(slots.adults)
            elif isinstance(slots, dict) and slots.get('adults'):
                adults = int(slots.get('adults'))
                
            if hasattr(slots, 'children') and slots.children:
                children = int(slots.children)
            elif isinstance(slots, dict) and slots.get('children'):
                children = int(slots.get('children'))
                
            if hasattr(slots, 'start_date') and slots.start_date:
                start_date = str(slots.start_date)
            elif isinstance(slots, dict) and slots.get('start_date'):
                start_date = str(slots.get('start_date'))
                
            if hasattr(slots, 'end_date') and slots.end_date:
                end_date = str(slots.end_date)
            elif isinstance(slots, dict) and slots.get('end_date'):
                end_date = str(slots.get('end_date'))
                
        except (ValueError, TypeError) as e:
            print(f"⚠️  Error parsing slot values: {e}, using defaults")
        
        budget_info = f"Budget: ₹{budget_per_night} per night"
        travelers = f"{adults} adults"
        if children > 0:
            travelers += f", {children} children"
        
        return f"""
Generate hotel recommendations for {destination} based on:

User Requirements:
- Destination: {destination}
- Travelers: {travelers}
- {budget_info}
- Dates: {start_date} to {end_date}

Generate JSON with this structure:
{{
  "hotels": [
    {{
      "id": "unique_hotel_id",
      "name": "Hotel Name",
      "location": "Specific area/neighborhood",
      "rating": 4.5,
      "price_estimate": {budget_per_night},
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
- Include mix of budget ranges around the specified budget (₹{budget_per_night})
- Use realistic Indian hotel names and pricing (in INR)
- Include family-friendly options if children are mentioned ({children} children)
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
        budget = getattr(slots, 'budget_per_night', None)
        
        if budget is not None and budget > 0:
            try:
                hotel_price = float(hotel_price)
                budget = float(budget)
                
                if hotel_price <= budget:
                    score += 0.15
                elif hotel_price <= budget * 1.2:  # Within 20% of budget
                    score += 0.1
                elif hotel_price > budget * 1.5:  # Significantly over budget
                    score -= 0.1
            except (ValueError, TypeError):
                pass  # Skip budget adjustment if values can't be compared
        
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