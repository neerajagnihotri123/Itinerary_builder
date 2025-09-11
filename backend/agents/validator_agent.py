"""
Validator Agent - LLM-powered validation against retrieval database
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class ValidatorAgent:
    """LLM-powered validation to prevent hallucination in planner outputs"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def validate(self, planner_output: Dict[str, Any], retrieval_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        LLM-powered validation of planner output against retrieved facts
        Returns: {"valid": bool, "issues": [...], "corrections": [...], "confidence": float}
        """
        try:
            # Try LLM-powered validation first
            llm_validation = await self._validate_with_llm(planner_output, retrieval_candidates)
            if llm_validation:
                return llm_validation
        except Exception as e:
            print(f"❌ LLM validation failed: {e}")
        
        # Fallback to rule-based validation
        return await self._fallback_validation(planner_output, retrieval_candidates)
    
    async def _validate_with_llm(self, planner_output: Dict[str, Any], retrieval_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to intelligently validate planner output"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for validation
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"validation_{hash(str(planner_output)) % 10000}",
                system_message="You are a travel expert validator. Analyze itineraries for accuracy, feasibility, and consistency with available data."
            ).with_model("openai", "gpt-4o-mini")
            
            # Create validation context
            context = self._prepare_validation_context(planner_output, retrieval_candidates)
            user_message = UserMessage(text=context)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse the JSON response
            try:
                validation_result = json.loads(content)
                enhanced_result = self._enhance_validation_result(validation_result, planner_output)
                print(f"✅ LLM validation completed with {enhanced_result.get('confidence', 0.8):.2f} confidence")
                return enhanced_result
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON from LLM validation")
                return None
                
        except Exception as e:
            print(f"❌ LLM validation error: {e}")
            return None
    
    def _prepare_validation_context(self, planner_output: Dict[str, Any], retrieval_candidates: List[Dict[str, Any]]) -> str:
        """Prepare context for LLM validation"""
        
        # Extract available resources
        available_hotels = [c for c in retrieval_candidates if c.get('type') == 'hotel']
        available_pois = [c for c in retrieval_candidates if c.get('type') == 'poi']
        available_activities = [c for c in retrieval_candidates if c.get('type') == 'activity']
        
        return f"""
Validate this travel itinerary against available resources:

PLANNER OUTPUT TO VALIDATE:
{json.dumps(planner_output, indent=2)}

AVAILABLE RESOURCES:
Hotels ({len(available_hotels)}):
{json.dumps([{'id': h.get('id'), 'name': h.get('name'), 'type': h.get('type')} for h in available_hotels[:5]], indent=2)}

POIs ({len(available_pois)}):
{json.dumps([{'id': p.get('id'), 'name': p.get('name'), 'type': p.get('type')} for p in available_pois[:5]], indent=2)}

Activities ({len(available_activities)}):
{json.dumps([{'id': a.get('id'), 'name': a.get('name'), 'type': a.get('type')} for a in available_activities[:5]], indent=2)}

VALIDATION TASKS:
1. Check if all activity/hotel IDs in itinerary exist in available resources
2. Verify logical flow and timing of activities
3. Assess feasibility of daily schedules
4. Validate hotel recommendations match available options
5. Check for any inconsistencies or impossible combinations

Generate JSON response:
{{
  "valid": true/false,
  "issues": [
    {{
      "item": "Description of problematic item",
      "issue": "Detailed issue description",
      "type": "missing_reference/timing_issue/feasibility_issue/inconsistency",
      "severity": "high/medium/low"
    }}
  ],
  "corrections": [
    {{
      "original_id": "problematic_id",
      "corrected_id": "suggested_replacement_id", 
      "corrected_name": "Replacement name",
      "reason": "Why this replacement is better"
    }}
  ],
  "confidence": 0.85,
  "validation_notes": "Overall assessment of the itinerary quality",
  "recommendations": [
    "Specific improvement suggestions"
  ]
}}

Focus on:
- Accuracy: Do referenced IDs exist?
- Feasibility: Are daily schedules realistic?
- Logic: Does the flow make sense?
- Quality: Are recommendations appropriate?
"""
    
    def _enhance_validation_result(self, validation_result: Dict, planner_output: Dict) -> Dict[str, Any]:
        """Enhance LLM validation result with additional metadata"""
        
        # Add metadata about what was validated
        itinerary = planner_output.get('itinerary', [])
        hotels = planner_output.get('hotel_recommendations', [])
        
        total_activities = sum(len(day.get('activities', [])) for day in itinerary)
        
        enhanced_result = {
            **validation_result,
            "metadata": {
                "total_days_checked": len(itinerary),
                "total_activities_checked": total_activities,
                "hotels_checked": len(hotels),
                "validation_method": "llm_powered"
            }
        }
        
        # Ensure required fields exist
        if "valid" not in enhanced_result:
            enhanced_result["valid"] = len(enhanced_result.get("issues", [])) == 0
        
        if "confidence" not in enhanced_result:
            # Calculate confidence based on issues
            issues = enhanced_result.get("issues", [])
            if len(issues) == 0:
                enhanced_result["confidence"] = 0.95
            elif len(issues) <= 2:
                enhanced_result["confidence"] = 0.8
            else:
                enhanced_result["confidence"] = 0.6
        
        return enhanced_result
    
    async def _fallback_validation(self, planner_output: Dict[str, Any], retrieval_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced fallback validation with better logic"""
        print(f"🔄 Using fallback validation for planner output")
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
                            "type": "missing_reference",
                            "severity": "medium"
                        })
                        
                        # Try to find a correction
                        correction = self._find_activity_correction(activity, retrieval_candidates)
                        if correction:
                            corrections.append({
                                "original_id": activity_id,
                                "corrected_id": correction['id'],
                                "corrected_title": correction['name'],
                                "reason": "Found similar activity in database"
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
                        "type": "missing_reference",
                        "severity": "high"
                    })
                    
                    # Try to find a correction
                    correction = self._find_hotel_correction(hotel, retrieval_candidates)
                    if correction:
                        corrections.append({
                            "original_id": hotel_id,
                            "corrected_id": correction['id'],
                            "corrected_name": correction['name'],
                            "reason": "Found similar hotel in database"
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
                "validation_notes": f"Rule-based validation completed. Score: {validation_score:.2f}",
                "recommendations": self._generate_recommendations(issues, planner_output),
                "metadata": {
                    "total_items_checked": total_items,
                    "valid_items": valid_items,
                    "issues_found": len(issues),
                    "validation_method": "rule_based_fallback"
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [{"item": "validation", "issue": f"Validation error: {str(e)}", "type": "system_error", "severity": "high"}],
                "corrections": [],
                "confidence": 0.1,
                "validation_notes": "Validation system error occurred",
                "recommendations": ["Please try regenerating the itinerary"],
                "metadata": {"validation_method": "error_fallback"}
            }
    
    def _generate_recommendations(self, issues: List[Dict], planner_output: Dict) -> List[str]:
        """Generate actionable recommendations based on validation issues"""
        recommendations = []
        
        # Analyze issue types
        issue_types = [issue.get('type') for issue in issues]
        
        if 'missing_reference' in issue_types:
            recommendations.append("Some activities or hotels were not found in our database. Consider using suggested alternatives.")
        
        if len(issues) > 3:
            recommendations.append("Multiple issues detected. Consider simplifying the itinerary or choosing a different destination.")
        
        # Check itinerary structure
        itinerary = planner_output.get('itinerary', [])
        if len(itinerary) > 7:
            recommendations.append("Long itinerary detected. Consider splitting into multiple trips for better experience.")
        
        # Check daily activity count
        for day in itinerary:
            activities = day.get('activities', [])
            if len(activities) > 5:
                recommendations.append(f"Day {day.get('day')} has many activities. Consider reducing to 3-4 for better pacing.")
        
        if not recommendations:
            recommendations.append("Itinerary looks well-structured with minor adjustments needed.")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
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