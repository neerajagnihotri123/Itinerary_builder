"""
Planner Agent - Generates day-by-day itineraries using retrieved facts
"""
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from .conversation_manager import get_cached_response, cache_response

class PlannerAgent:
    """Generates detailed itineraries using grounding facts"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def generate_itinerary(self, slots, retrieval_candidates: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive day-by-day itinerary using LLM and retrieval facts
        Returns: Structured JSON response for frontend consumption
        """
        print(f"🗓️ Generating itinerary for {slots.destination}")
        
        # Build context using retrieval facts
        context = self._build_context(slots, retrieval_candidates or [])
        
        try:
            # Generate using LLM
            llm_response = await self._generate_with_llm(context)
            
            # Parse and structure the response
            try:
                itinerary_data = json.loads(llm_response)
                
                # Ensure proper structure for frontend
                structured_response = {
                    "itinerary": itinerary_data.get('itinerary', []),
                    "hotel_recommendations": itinerary_data.get('hotel_recommendations', []),
                    "total_days": len(itinerary_data.get('itinerary', [])),
                    "destination": slots.destination,
                    "travelers": getattr(slots, 'adults', 2),
                    "budget_estimate": self._calculate_budget_estimate(itinerary_data, slots),
                    "highlights": self._extract_highlights(itinerary_data),
                    "metadata": {
                        "generated_by": "planner_agent",
                        "generation_method": "llm_powered",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "facts_used": len(retrieval_candidates) if retrieval_candidates else 0
                    }
                }
                
                print(f"✅ Generated {len(structured_response['itinerary'])} day itinerary")
                return structured_response
                
            except json.JSONDecodeError:
                print(f"❌ LLM returned invalid JSON, using fallback")
                return self._generate_fallback_itinerary(context)
                
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return self._generate_fallback_itinerary(context)
    
    def _build_context(self, slots, retrieval_candidates: List[Dict[str, Any]]) -> str:
        """Build context for LLM generation using slots and retrieval facts"""
        # Calculate trip duration
        if slots.start_date and slots.end_date:
            start = datetime.fromisoformat(slots.start_date)
            end = datetime.fromisoformat(slots.end_date)
            days = (end - start).days + 1
        else:
            days = 5  # Default trip length
        
        # Use the existing _prepare_planning_context method
        return self._prepare_planning_context(slots, retrieval_candidates, days)
    
    def _calculate_budget_estimate(self, itinerary_data: Dict, slots) -> Dict[str, Any]:
        """Calculate budget estimate from itinerary data"""
        try:
            itinerary = itinerary_data.get('itinerary', [])
            hotels = itinerary_data.get('hotel_recommendations', [])
            
            # Calculate accommodation costs
            accommodation_cost = 0
            if hotels:
                avg_hotel_price = sum(h.get('price_estimate', 5000) for h in hotels) / len(hotels)
                nights = len(itinerary) - 1 if len(itinerary) > 1 else 1
                accommodation_cost = avg_hotel_price * nights
            
            # Calculate activity costs
            activity_cost = 0
            for day in itinerary:
                for activity in day.get('activities', []):
                    activity_cost += activity.get('price_estimate', 1000)
            
            # Calculate total per person
            total_per_person = accommodation_cost + activity_cost
            travelers = getattr(slots, 'adults', 2) + getattr(slots, 'children', 0)
            
            return {
                "total_per_person": int(total_per_person),
                "accommodation": int(accommodation_cost),
                "activities": int(activity_cost),
                "total_for_group": int(total_per_person * travelers),
                "currency": "INR",
                "travelers": travelers
            }
            
        except Exception as e:
            print(f"⚠️ Budget calculation error: {e}")
            return {
                "total_per_person": 15000,
                "accommodation": 10000,
                "activities": 5000,
                "total_for_group": 30000,
                "currency": "INR",
                "travelers": 2
            }
    
    def _extract_highlights(self, itinerary_data: Dict) -> List[str]:
        """Extract key highlights from itinerary"""
        highlights = []
        
        try:
            itinerary = itinerary_data.get('itinerary', [])
            
            for day in itinerary[:3]:  # First 3 days for highlights
                for activity in day.get('activities', [])[:2]:  # Top 2 activities per day
                    title = activity.get('title', '')
                    if title and len(highlights) < 6:
                        highlights.append(title)
            
            if not highlights:
                highlights = ["Scenic destinations", "Cultural experiences", "Adventure activities"]
                
        except Exception:
            highlights = ["Amazing experiences await", "Unforgettable memories", "Perfect getaway"]
        
        return highlights

    def _generate_fallback_itinerary(self, context: str) -> Dict[str, Any]:
        """Generate fallback itinerary when LLM fails"""
        # Use the existing fallback logic but adapt the return format
        try:
            # Extract basic info from context
            destination = "Unknown Destination"
            if "Destination:" in context:
                lines = context.split('\n')
                for line in lines:
                    if line.strip().startswith("- Destination:"):
                        destination = line.split(":")[1].strip()
                        break
            
            # Create basic structured response
            fallback_data = {
                "itinerary": [
                    {
                        "day": 1,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "activities": [
                            {
                                "time": "10:00",
                                "type": "arrival",
                                "id": "arrival",
                                "title": f"Arrival in {destination}",
                                "notes": "Check-in and orientation"
                            },
                            {
                                "time": "15:00",
                                "type": "poi",
                                "id": "exploration",
                                "title": "Local Exploration",
                                "notes": "Discover the area"
                            }
                        ]
                    }
                ],
                "hotel_recommendations": [
                    {
                        "id": "fallback_hotel",
                        "name": f"Recommended Hotel in {destination}",
                        "price_estimate": 5000,
                        "reason": "Comfortable accommodation with good amenities"
                    }
                ],
                "total_days": 1,
                "destination": destination,
                "travelers": 2,
                "budget_estimate": {
                    "total_per_person": 10000,
                    "accommodation": 5000,
                    "activities": 5000,
                    "total_for_group": 20000,
                    "currency": "INR",
                    "travelers": 2
                },
                "highlights": ["Local exploration", "Cultural immersion", "Relaxation"],
                "metadata": {
                    "generated_by": "planner_agent",
                    "generation_method": "fallback",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "facts_used": 0
                }
            }
            
            return fallback_data
            
        except Exception as e:
            print(f"❌ Fallback generation failed: {e}")
            # Return minimal valid structure
            return {
                "itinerary": [],
                "hotel_recommendations": [],
                "total_days": 0,
                "destination": "Unknown",
                "travelers": 2,
                "budget_estimate": {
                    "total_per_person": 0,
                    "accommodation": 0,
                    "activities": 0,
                    "total_for_group": 0,
                    "currency": "INR",
                    "travelers": 2
                },
                "highlights": [],
                "metadata": {
                    "generated_by": "planner_agent",
                    "generation_method": "minimal_fallback",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "facts_used": 0
                }
            }
    
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
        """Generate comprehensive itinerary using LLM with caching and optimized prompts"""
        try:
            # Use the same approach as in the main server - create a new LlmChat instance
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import os
            import asyncio
            
            # Create a new LLM client for this specific call
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"planner_{hash(context) % 10000}",
                system_message="You are an expert travel planner with extensive knowledge of Indian destinations. Generate detailed, realistic travel itineraries in JSON format with accurate information about places, activities, and logistics."
            ).with_model("openai", "gpt-4o-mini")
            
            # Enhanced context with better structure
            enhanced_context = f"""
{context}

Additional Guidelines:
- Ensure all locations and activities are REAL and accurate
- Include realistic travel times between locations
- Consider local weather, seasons, and best visiting times
- Add specific details like opening hours, entry fees where relevant
- Include meal breaks at appropriate times
- Balance active and relaxing activities
- Consider the traveler profile (adults/children) for activity selection
- Use actual place names, not generic descriptions
- Include specific recommendations for authentic local experiences

Focus on creating an itinerary that a real traveler could actually follow.
"""
            
            # Create and send the message with timeout
            user_message = UserMessage(text=enhanced_context)
            try:
                response = await asyncio.wait_for(
                    llm_client.send_message(user_message),
                    timeout=15.0  # 15 second timeout
                )
            except asyncio.TimeoutError:
                print(f"❌ LLM generation timed out for planner")
                return self._generate_fallback_itinerary(enhanced_context)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Validate JSON structure before returning
            try:
                # Clean content
                content = content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                json.loads(content)
                print(f"✅ LLM generation successful: {len(content)} characters, valid JSON")
                return content
            except json.JSONDecodeError:
                print(f"❌ LLM generated invalid JSON, using intelligent fallback")
                fallback_result = self._generate_fallback_itinerary(enhanced_context)
                return json.dumps(fallback_result)
            
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            print(f"🔄 Using intelligent fallback for context: {context[:100]}...")
            # Generate a more realistic fallback itinerary based on input
            fallback_result = self._generate_fallback_itinerary(context)
            return json.dumps(fallback_result)
    
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
    
