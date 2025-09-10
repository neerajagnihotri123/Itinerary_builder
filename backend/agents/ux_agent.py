"""
UX Agent - Converts structured outputs into user-friendly text and actions
"""
from typing import Dict, Any, List

class UXAgent:
    """Handles user experience optimization and response formatting"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def format_response(self, planner_output: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert planner JSON into short, friendly human_text and micro-ui actions
        Returns: {"human_text": str, "actions": [...]}
        """
        try:
            # Generate human-friendly text
            human_text = self._generate_human_text(planner_output, validation_result)
            
            # Generate micro-actions
            actions = self._generate_actions(planner_output, validation_result)
            
            return {
                "human_text": human_text,
                "actions": actions
            }
            
        except Exception as e:
            return {
                "human_text": "I've created a personalized itinerary for you! Let me know if you'd like to make any changes.",
                "actions": [
                    {"label": "Accept", "action": "accept_itinerary"},
                    {"label": "Modify", "action": "edit_itinerary"}
                ]
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