"""
UX Agent - LLM-powered user experience optimization and response formatting
"""
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class UXAgent:
    """Handles LLM-powered user experience optimization and response formatting"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def format_response(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM-powered conversion of planner JSON into friendly human text and micro-ui actions
        Returns: {"human_text": str, "actions": [...]}
        """
        try:
            # Try LLM-powered response formatting first
            llm_response = await self._format_with_llm(planner_output, validation_result)
            if llm_response:
                return llm_response
        except Exception as e:
            print(f"❌ LLM UX formatting failed: {e}")
        
        # Fallback to rule-based formatting
        return self._fallback_format_response(planner_output, validation_result)
    
    async def _format_with_llm(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to generate contextual, engaging user responses"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for UX formatting
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"ux_{hash(str(planner_output)) % 10000}",
                system_message="You are a friendly travel assistant UX expert. Create engaging, conversational responses that excite users about their travel plans."
            ).with_model("openai", "gpt-4o-mini")
            
            # Create UX formatting context
            context = self._prepare_ux_context(planner_output, validation_result)
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse the JSON response
            try:
                ux_response = json.loads(content)
                enhanced_response = self._enhance_ux_response(ux_response, planner_output, validation_result)
                print(f"✅ LLM UX formatting completed")
                return enhanced_response
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from LLM UX formatting")
                return None
                
        except Exception as e:
            print(f"❌ LLM UX formatting error: {e}")
            return None
    
    def _prepare_ux_context(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """Prepare context for LLM UX formatting"""
        
        itinerary = planner_output.get('itinerary', [])
        hotels = planner_output.get('hotel_recommendations', [])
        confidence = validation_result.get('confidence', 0.8)
        issues = validation_result.get('issues', [])
        
        # Extract key details
        days = len(itinerary)
        total_activities = sum(len(day.get('activities', [])) for day in itinerary)
        destination = ""
        if itinerary and itinerary[0].get('activities'):
            first_activity = itinerary[0]['activities'][0]
            destination = first_activity.get('title', '').split(' in ')[-1] if ' in ' in first_activity.get('title', '') else ""
        
        return f"""
Create an engaging, conversational response for this travel itinerary:

ITINERARY SUMMARY:
- Duration: {days} days
- Total activities: {total_activities}
- Hotels available: {len(hotels)}
- Validation confidence: {confidence:.2f}
- Issues found: {len(issues)}
- Destination: {destination}

VALIDATION DETAILS:
{json.dumps(validation_result.get('recommendations', []), indent=2)}

SAMPLE ACTIVITIES:
{json.dumps([day.get('activities', [])[0] if day.get('activities') else {} for day in itinerary[:3]], indent=2)}

HOTEL OPTIONS:
{json.dumps([{'name': h.get('name'), 'rating': h.get('rating', 4.0)} for h in hotels[:2]], indent=2)}

Generate JSON response:
{{
  "human_text": "Engaging 40-50 word response that excites the user about their trip",
  "actions": [
    {{
      "label": "Action Button Text",
      "action": "action_identifier",
      "priority": "high/medium/low"
    }}
  ]
}}

GUIDELINES:
- Keep human_text between 40-50 words, enthusiastic and personalized
- Generate 3-4 contextual action buttons based on itinerary quality
- If confidence > 0.9: Focus on "book now" type actions
- If confidence 0.7-0.9: Mix of "review details" and "customize" actions  
- If confidence < 0.7: Focus on "refine" and "improve" actions
- Include destination-specific language and activity highlights
- Make it sound like a knowledgeable local friend recommending the trip
"""
    
    def _enhance_ux_response(self, ux_response: Dict, planner_output: Dict, validation_result: Dict) -> Dict[str, Any]:
        """Enhance LLM UX response with additional metadata and fallback actions"""
        
        # Ensure required fields exist
        if "human_text" not in ux_response:
            ux_response["human_text"] = self._generate_human_text(planner_output, validation_result)
        
        if "actions" not in ux_response or not ux_response["actions"]:
            ux_response["actions"] = self._generate_actions(planner_output, validation_result)
        
        # Ensure human_text is appropriate length (40-60 words)
        human_text = ux_response["human_text"]
        word_count = len(human_text.split())
        if word_count > 60:
            # Truncate if too long
            words = human_text.split()[:60]
            ux_response["human_text"] = " ".join(words) + "..."
        elif word_count < 20:
            # Add enthusiasm if too short
            ux_response["human_text"] += " Ready to explore?"
        
        # Limit actions to 4 and ensure proper format
        actions = ux_response.get("actions", [])
        formatted_actions = []
        for action in actions[:4]:
            if isinstance(action, dict) and "label" in action and "action" in action:
                formatted_actions.append({
                    "label": action["label"],
                    "action": action["action"],
                    "priority": action.get("priority", "medium")
                })
        
        ux_response["actions"] = formatted_actions or self._generate_actions(planner_output, validation_result)
        
        return ux_response
    
    def _fallback_format_response(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback formatting with better messaging"""
        print(f"🔄 Using fallback UX formatting")
        
        # Generate human-friendly text
        human_text = self._generate_human_text(planner_output, validation_result)
        
        # Generate micro-actions
        actions = self._generate_actions(planner_output, validation_result)
        
        return {
            "human_text": human_text,
            "actions": actions
        }
    
    def _generate_human_text(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> str:
        """Generate concise, friendly human text (<=50 words)"""
        
        itinerary = planner_output.get('itinerary', [])
        hotels = planner_output.get('hotel_recommendations', [])
        confidence = validation_result.get('confidence', 0.8)
        
        # Count activities
        total_activities = sum(len(day.get('activities', [])) for day in itinerary)
        days = len(itinerary)
        
        # Generate appropriate message based on content
        if confidence >= 0.9:
            if days >= 3:
                return f"Perfect! I've crafted a {days}-day adventure with {total_activities} amazing experiences and {len(hotels)} handpicked hotels. Ready to explore?"
            else:
                return f"Great! Here's your {days}-day itinerary with {total_activities} experiences. Everything looks perfect!"
        
        elif confidence >= 0.7:
            if hotels:
                return f"I've created your {days}-day itinerary with {len(hotels)} hotel options. Some activities might need final confirmation—shall we proceed?"
            else:
                return f"Your {days}-day adventure is ready! I've included {total_activities} activities. Would you like to review the details?"
        
        else:
            return f"I've drafted your {days}-day itinerary. Let's refine a few details to make it perfect for you!"
    
    def _generate_actions(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate contextual micro-actions"""
        actions = []
        
        confidence = validation_result.get('confidence', 0.8)
        issues = validation_result.get('issues', [])
        itinerary = planner_output.get('itinerary', [])
        hotels = planner_output.get('hotel_recommendations', [])
        
        # Primary actions based on confidence
        if confidence >= 0.9:
            actions.append({"label": "Perfect! Book Now", "action": "accept_itinerary"})
        elif confidence >= 0.7:
            actions.append({"label": "Looks Great", "action": "accept_itinerary"})
        else:
            actions.append({"label": "Refine Details", "action": "edit_itinerary"})
        
        # Secondary actions
        if itinerary:
            actions.append({"label": "Modify Days", "action": "edit_itinerary"})
        
        if hotels:
            actions.append({"label": "Change Hotels", "action": "edit_hotels"})
        
        # Conditional actions based on validation issues
        if issues:
            issue_types = [issue.get('type', '') for issue in issues]
            if 'missing_reference' in issue_types:
                actions.append({"label": "Fix Activities", "action": "validate_activities"})
        
        # Contextual actions based on content
        if len(itinerary) >= 5:  # Long trip
            actions.append({"label": "Shorten Trip", "action": "reduce_days"})
        elif len(itinerary) <= 2:  # Short trip
            actions.append({"label": "Extend Trip", "action": "add_days"})
        
        # Budget-related actions
        if planner_output.get('followups'):
            followup_types = [f.get('slot', '') for f in planner_output.get('followups', [])]
            if 'budget' in followup_types:
                actions.append({"label": "Set Budget", "action": "edit_budget"})
            if 'preferences' in followup_types:
                actions.append({"label": "Update Preferences", "action": "edit_preferences"})
        
        # Limit to top 4 actions to avoid overwhelming
        return actions[:4]
    
    def _get_activity_summary(self, itinerary: List[Dict[str, Any]]) -> str:
        """Get a brief summary of activities"""
        activity_types = []
        for day in itinerary:
            for activity in day.get('activities', []):
                activity_type = activity.get('type', '')
                if activity_type and activity_type not in ['meal', 'transit']:
                    activity_types.append(activity_type)
        
        unique_types = list(set(activity_types))
        if len(unique_types) <= 2:
            return ', '.join(unique_types)
        else:
            return f"{unique_types[0]}, {unique_types[1]} and more"
    
    def _get_hotel_summary(self, hotels: List[Dict[str, Any]]) -> str:
        """Get a brief summary of hotels"""
        if not hotels:
            return ""
        
        if len(hotels) == 1:
            return f"staying at {hotels[0].get('name', 'selected hotel')}"
        else:
            return f"{len(hotels)} hotel options"
    
    async def format_general_response(self, message: str) -> Dict[str, Any]:
        """
        Format response for general queries without specific destination
        Returns: {"human_text": str, "actions": [...]}
        """
        message_lower = message.lower()
        
        # Determine response based on query type
        if "popular destinations" in message_lower or "destinations right now" in message_lower:
            human_text = "Here are some amazing destinations trending right now! Each offers unique experiences perfect for your next adventure."
            actions = [
                {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                {"label": "Manali", "action": "set_destination", "data": "Manali"},
                {"label": "Andaman Islands", "action": "set_destination", "data": "Andaman Islands"},
                {"label": "Goa", "action": "set_destination", "data": "Goa"}
            ]
        
        elif "weekend getaway" in message_lower:
            human_text = "Perfect for a weekend escape! These destinations are ideal for 2-3 day trips with great connectivity."
            actions = [
                {"label": "Rishikesh", "action": "set_destination", "data": "Rishikesh"},
                {"label": "Mussoorie", "action": "set_destination", "data": "Mussoorie"},
                {"label": "Agra", "action": "set_destination", "data": "Agra"},
                {"label": "Jaipur", "action": "set_destination", "data": "Jaipur"}
            ]
        
        elif any(word in message_lower for word in ["recommend", "suggest", "best places"]):
            human_text = "I'd love to help you discover the perfect destination! Here are some top picks across different experiences."
            actions = [
                {"label": "Adventure (Rishikesh)", "action": "set_destination", "data": "Rishikesh"},
                {"label": "Mountains (Manali)", "action": "set_destination", "data": "Manali"},
                {"label": "Beaches (Andaman)", "action": "set_destination", "data": "Andaman Islands"},
                {"label": "Culture (Rajasthan)", "action": "set_destination", "data": "Rajasthan"}
            ]
        
        else:
            # Default general response
            human_text = "I'm here to help you plan an amazing trip! Where would you like to explore?"
            actions = [
                {"label": "Popular Destinations", "action": "show_popular"},
                {"label": "Weekend Getaways", "action": "show_weekend"},
                {"label": "Adventure Trips", "action": "show_adventure"},
                {"label": "Tell me more", "action": "ask_preferences"}
            ]
        
        return {
            "human_text": human_text,
            "actions": actions
        }
    
    async def format_destination_specific_response(self, message: str, destination: str) -> Dict[str, Any]:
        """
        Format response for specific destination queries (e.g., "tell me about Kerala")
        Returns: {"human_text": str, "actions": [...]}
        """
        message_lower = message.lower()
        
        # Create destination-specific responses
        destination_info = {
            "kerala": {
                "text": "Kerala, 'God's Own Country', offers serene backwaters, lush hill stations, pristine beaches, and rich cultural heritage. Perfect for nature lovers and those seeking tranquility!",
                "highlights": ["Backwaters", "Hill Stations", "Beaches", "Ayurveda"]
            },
            "goa": {
                "text": "Goa combines stunning beaches, vibrant nightlife, Portuguese heritage, and delicious cuisine. Ideal for beach lovers, party enthusiasts, and culture seekers!",
                "highlights": ["Beaches", "Nightlife", "Heritage", "Cuisine"]
            },
            "rajasthan": {
                "text": "Rajasthan showcases magnificent palaces, desert landscapes, colorful culture, and royal heritage. Perfect for history buffs and cultural enthusiasts!",
                "highlights": ["Palaces", "Desert", "Culture", "Heritage"]
            },
            "manali": {
                "text": "Manali offers snow-capped mountains, adventure sports, apple orchards, and cool climate. Great for adventure seekers and mountain lovers!",
                "highlights": ["Mountains", "Adventure", "Nature", "Climate"]
            },
            "rishikesh": {
                "text": "Rishikesh, the 'Yoga Capital of the World', features river rafting, spiritual experiences, adventure sports, and scenic beauty. Perfect for adventure and spirituality!",
                "highlights": ["Yoga", "Rafting", "Spirituality", "Adventure"]
            }
        }
        
        # Get destination info or create generic response
        dest_key = destination.lower()
        if dest_key in destination_info:
            info = destination_info[dest_key]
            human_text = info["text"]
            highlights = info["highlights"]
        else:
            human_text = f"{destination} is a wonderful destination with unique experiences waiting for you! Let me help you plan an amazing trip there."
            highlights = ["Explore", "Discover", "Experience", "Adventure"]
        
        # Create contextual actions
        actions = [
            {"label": f"Plan Trip to {destination}", "action": "set_destination", "data": destination},
            {"label": "See Hotels", "action": "show_hotels", "data": destination},
            {"label": "Get Itinerary", "action": "plan_itinerary", "data": destination}
        ]
        
        # Add highlight-based actions
        if len(highlights) > 0:
            actions.append({"label": f"More about {highlights[0]}", "action": "explore_theme", "data": {"destination": destination, "theme": highlights[0]}})
        
        return {
            "human_text": human_text,
            "actions": actions[:4]  # Limit to 4 actions
        }