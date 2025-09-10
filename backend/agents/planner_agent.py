"""
Planner Agent - Generates day-by-day itineraries using retrieved facts
"""
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from emergentintegrations.llm.chat import UserMessage

class PlannerAgent:
    """Generates detailed itineraries using grounding facts"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def generate_itinerary(self, slots, retrieval_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate day-by-day itinerary using retrieved facts
        Returns: {"itinerary": [...], "hotel_recommendations": [...], "followups": [...]}
        """
        try:
            # Calculate trip duration
            if slots.start_date and slots.end_date:
                start = datetime.fromisoformat(slots.start_date)
                end = datetime.fromisoformat(slots.end_date)
                days = (end - start).days + 1
            else:
                days = 5  # Default trip length
            
            # Prepare context for LLM
            context = self._prepare_planning_context(slots, retrieval_candidates, days)
            
            # Generate itinerary using LLM
            itinerary_response = await self._generate_with_llm(context)
            
            # Parse and validate response
            result = json.loads(itinerary_response)
            
            # Ensure required structure
            if "itinerary" not in result:
                result["itinerary"] = []
            if "hotel_recommendations" not in result:
                result["hotel_recommendations"] = self._extract_hotels(retrieval_candidates)[:3]
            if "followups" not in result:
                result["followups"] = []
            
            return result
            
        except Exception as e:
            print(f"Planning error: {e}")
            return await self._fallback_itinerary(slots, retrieval_candidates)
    
    def _prepare_planning_context(self, slots, candidates: List[Dict[str, Any]], days: int) -> str:
        """Prepare context for LLM planning"""
        
        # Extract different types of candidates
        pois = [c for c in candidates if c.get('type') == 'poi']
        hotels = [c for c in candidates if c.get('type') == 'hotel']
        activities = [c for c in candidates if c.get('type') == 'activity']
        
        context = f"""
System: You are a planner. Create a {days}-day itinerary for {slots.destination}.

Input:
- Destination: {slots.destination}
- Dates: {slots.start_date} to {slots.end_date}
- Travelers: {slots.adults} adults, {slots.children} children
- Budget: {slots.budget_per_night} {slots.currency} per night (if specified)

Available POIs:
{json.dumps(pois[:5], indent=2)}

Available Hotels:
{json.dumps(hotels[:5], indent=2)}

Available Activities:
{json.dumps(activities[:8], indent=2)}

Output JSON only:
{{
  "itinerary": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD", 
      "activities": [
        {{
          "time": "09:00",
          "type": "poi|activity|meal|transit",
          "id": "poi_1",
          "title": "Activity Name",
          "notes": "Brief description"
        }}
      ]
    }}
  ],
  "hotel_recommendations": [
    {{
      "id": "hotel_123",
      "name": "Hotel Name",
      "price_estimate": 5000,
      "reason": "Why this hotel fits"
    }}
  ],
  "followups": [
    {{
      "type": "clarify",
      "slot": "preferences", 
      "question": "Would you prefer cultural or adventure activities?"
    }}
  ]
}}

Rules:
- Use ONLY retrieved candidates with their exact IDs
- Keep each day to 2-4 activities including meals
- Include realistic transit times
- Consider traveler count for recommendations
- If budget specified, respect it for hotel recommendations
"""
        return context
    
    async def _generate_with_llm(self, context: str) -> str:
        """Generate itinerary using LLM"""
        response = await self.llm_client.chat([UserMessage(content=context)])
        return response.content
    
    def _extract_hotels(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract hotel recommendations from candidates"""
        hotels = []
        for candidate in candidates:
            if candidate.get('type') == 'hotel':
                hotels.append({
                    "id": candidate['id'],
                    "name": candidate['name'],
                    "price_estimate": candidate.get('price_estimate', 5000),
                    "rating": candidate.get('rating', 4.0),
                    "reason": f"Great {candidate.get('hotel_type', 'hotel')} with {candidate.get('rating', 4.0)} rating"
                })
        return hotels
    
    async def _fallback_itinerary(self, slots, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fallback itinerary if LLM fails"""
        
        # Create basic itinerary structure
        start_date = datetime.fromisoformat(slots.start_date) if slots.start_date else datetime.now()
        
        itinerary = []
        for day in range(3):  # 3-day fallback
            day_date = start_date + timedelta(days=day)
            
            activities = []
            if day == 0:  # Arrival day
                activities = [
                    {
                        "time": "10:00",
                        "type": "transit",
                        "id": "arrival",
                        "title": f"Arrive in {slots.destination}",
                        "notes": "Check into hotel and freshen up"
                    },
                    {
                        "time": "14:00", 
                        "type": "meal",
                        "id": "lunch",
                        "title": "Local Lunch",
                        "notes": "Try authentic local cuisine"
                    },
                    {
                        "time": "16:00",
                        "type": "poi",
                        "id": "exploration",
                        "title": f"Explore {slots.destination}",
                        "notes": "Walking tour and orientation"
                    }
                ]
            elif day == 1:  # Full day
                activities = [
                    {
                        "time": "09:00",
                        "type": "activity",
                        "id": "morning_activity",
                        "title": "Morning Adventure",
                        "notes": "Popular activity based on destination"
                    },
                    {
                        "time": "13:00",
                        "type": "meal", 
                        "id": "lunch2",
                        "title": "Lunch Break",
                        "notes": "Local restaurant"
                    },
                    {
                        "time": "15:00",
                        "type": "poi",
                        "id": "sightseeing",
                        "title": "Sightseeing",
                        "notes": "Visit key attractions"
                    }
                ]
            else:  # Departure day
                activities = [
                    {
                        "time": "10:00",
                        "type": "poi",
                        "id": "final_visit",
                        "title": "Final Exploration", 
                        "notes": "Last-minute shopping or sightseeing"
                    },
                    {
                        "time": "14:00",
                        "type": "transit",
                        "id": "departure",
                        "title": "Departure",
                        "notes": "Check out and head to transport"
                    }
                ]
            
            itinerary.append({
                "day": day + 1,
                "date": day_date.strftime("%Y-%m-%d"),
                "activities": activities
            })
        
        return {
            "itinerary": itinerary,
            "hotel_recommendations": self._extract_hotels(candidates)[:3],
            "followups": [
                {
                    "type": "clarify",
                    "slot": "preferences",
                    "question": "Would you like to customize any part of this itinerary?"
                }
            ]
        }