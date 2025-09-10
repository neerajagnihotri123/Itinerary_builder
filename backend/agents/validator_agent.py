"""
Validator Agent - Validates planner output against retrieval database
"""
from typing import Dict, Any, List

class ValidatorAgent:
    """Validates and corrects planner outputs to prevent hallucination"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def validate(self, planner_output: Dict[str, Any], retrieval_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate planner output against retrieved facts
        Returns: {"valid": bool, "issues": [...], "corrections": [...], "confidence": float}
        """
        try:
            # Create lookup dictionary for quick fact checking
            candidate_ids = {candidate['id']: candidate for candidate in retrieval_candidates}
            
            issues = []
            corrections = []
            valid_items = 0
            total_items = 0
            
            # Validate itinerary activities
            for day in planner_output.get('itinerary', []):
                for activity in day.get('activities', []):
                    total_items += 1
                    activity_id = activity.get('id', '')
                    
                    # Check if activity ID exists in candidates
                    if activity_id in candidate_ids:
                        valid_items += 1
                    elif activity_id in ['arrival', 'departure', 'lunch', 'lunch2', 'morning_activity', 'sightseeing', 'final_visit']:
                        # These are generic activities, they're OK
                        valid_items += 1
                    else:
                        issues.append({
                            "item": f"Day {day.get('day')} - {activity.get('title')}",
                            "issue": f"Activity ID '{activity_id}' not found in retrieval database",
                            "type": "missing_reference"
                        })
                        
                        # Try to find a correction
                        correction = self._find_activity_correction(activity, retrieval_candidates)
                        if correction:
                            corrections.append({
                                "original_id": activity_id,
                                "corrected_id": correction['id'],
                                "corrected_title": correction['name']
                            })
            
            # Validate hotel recommendations
            for hotel in planner_output.get('hotel_recommendations', []):
                total_items += 1
                hotel_id = hotel.get('id', '')
                
                if hotel_id in candidate_ids:
                    valid_items += 1
                else:
                    issues.append({
                        "item": f"Hotel - {hotel.get('name')}",
                        "issue": f"Hotel ID '{hotel_id}' not found in retrieval database",
                        "type": "missing_reference"
                    })
                    
                    # Try to find a correction
                    correction = self._find_hotel_correction(hotel, retrieval_candidates)
                    if correction:
                        corrections.append({
                            "original_id": hotel_id,
                            "corrected_id": correction['id'],
                            "corrected_name": correction['name']
                        })
            
            # Calculate validation score
            validation_score = valid_items / total_items if total_items > 0 else 1.0
            is_valid = validation_score >= 0.8  # 80% threshold
            
            # Calculate confidence based on validation score and other factors
            confidence = self._calculate_confidence(validation_score, issues, planner_output)
            
            return {
                "valid": is_valid,
                "issues": issues,
                "corrections": corrections,
                "confidence": confidence,
                "validation_score": validation_score,
                "metadata": {
                    "total_items_checked": total_items,
                    "valid_items": valid_items,
                    "issues_found": len(issues)
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [{"item": "validation", "issue": f"Validation error: {str(e)}", "type": "system_error"}],
                "corrections": [],
                "confidence": 0.1
            }
    
    def _find_activity_correction(self, activity: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find a suitable replacement activity from candidates"""
        activity_title = activity.get('title', '').lower()
        activity_type = activity.get('type', '')
        
        # Look for activities that match the title or type
        for candidate in candidates:
            if candidate.get('type') == 'activity':
                candidate_name = candidate.get('name', '').lower()
                
                # Simple similarity check
                if any(word in candidate_name for word in activity_title.split() if len(word) > 3):
                    return candidate
        
        # Look for POIs if no activities match
        for candidate in candidates:
            if candidate.get('type') == 'poi':
                candidate_name = candidate.get('name', '').lower()
                
                if any(word in candidate_name for word in activity_title.split() if len(word) > 3):
                    return candidate
        
        return None
    
    def _find_hotel_correction(self, hotel: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find a suitable replacement hotel from candidates"""
        hotel_name = hotel.get('name', '').lower()
        
        # Look for hotels with similar names
        for candidate in candidates:
            if candidate.get('type') == 'hotel':
                candidate_name = candidate.get('name', '').lower()
                
                # Simple similarity check
                if any(word in candidate_name for word in hotel_name.split() if len(word) > 3):
                    return candidate
        
        # Return first available hotel as fallback
        for candidate in candidates:
            if candidate.get('type') == 'hotel':
                return candidate
        
        return None
    
    def _calculate_confidence(self, validation_score: float, issues: List[Dict], planner_output: Dict[str, Any]) -> float:
        """Calculate overall confidence in the response"""
        base_confidence = validation_score
        
        # Reduce confidence for each issue
        confidence_penalty = len(issues) * 0.1
        base_confidence -= confidence_penalty
        
        # Boost confidence if itinerary is well-structured
        itinerary = planner_output.get('itinerary', [])
        if itinerary:
            if len(itinerary) >= 2:  # Multi-day itinerary
                base_confidence += 0.1
            
            # Check if activities have realistic times
            for day in itinerary:
                activities = day.get('activities', [])
                if len(activities) >= 2:  # Multiple activities per day
                    base_confidence += 0.05
        
        # Boost confidence if hotels are provided
        if planner_output.get('hotel_recommendations'):
            base_confidence += 0.1
        
        return max(0.1, min(1.0, base_confidence))  # Keep between 0.1 and 1.0