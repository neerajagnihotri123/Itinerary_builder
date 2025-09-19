"""
Conflict Detection Agent - Validates itinerary feasibility
Checks for timing conflicts, travel distances, and unrealistic schedules
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

logger = logging.getLogger(__name__)

class ConflictDetectionAgent:
    """Agent for detecting conflicts and unrealistic elements in itineraries"""
    
    def __init__(self):
        self.max_travel_hours_per_day = 8
        self.max_activities_per_day = 4
        self.min_activity_duration = 30  # minutes
        self.max_activity_duration = 12 * 60  # 12 hours in minutes
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for conflict analysis"""
        return LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=session_id,
            system_message="You are a travel logistics expert who identifies conflicts and suggests realistic itinerary adjustments."
        ).with_model("openai", "gpt-4o-mini")
    
    async def check_itinerary_conflicts(self, 
                                      session_id: str,
                                      itinerary: List[Dict]) -> Dict[str, Any]:
        """
        Comprehensive conflict detection for entire itinerary
        
        Args:
            session_id: User session ID
            itinerary: List of day-wise itinerary data
        
        Returns:
            Dict with conflicts, warnings, and suggestions
        """
        try:
            conflicts = []
            warnings = []
            suggestions = []
            
            for day_idx, day in enumerate(itinerary):
                day_conflicts = await self._check_day_conflicts(day, day_idx + 1)
                conflicts.extend(day_conflicts.get('conflicts', []))
                warnings.extend(day_conflicts.get('warnings', []))
                suggestions.extend(day_conflicts.get('suggestions', []))
            
            # Check inter-day conflicts
            inter_day_issues = await self._check_inter_day_conflicts(itinerary)
            conflicts.extend(inter_day_issues.get('conflicts', []))
            warnings.extend(inter_day_issues.get('warnings', []))
            suggestions.extend(inter_day_issues.get('suggestions', []))
            
            # Get LLM analysis for complex conflicts
            llm_analysis = await self._get_llm_conflict_analysis(session_id, itinerary, conflicts, warnings)
            
            return {
                "has_conflicts": len(conflicts) > 0,
                "has_warnings": len(warnings) > 0,
                "conflicts": conflicts,
                "warnings": warnings,
                "suggestions": suggestions,
                "llm_analysis": llm_analysis,
                "feasibility_score": self._calculate_feasibility_score(conflicts, warnings),
                "total_issues": len(conflicts) + len(warnings)
            }
            
        except Exception as e:
            logger.error(f"Conflict detection error: {e}")
            return {
                "has_conflicts": False,
                "has_warnings": False,
                "conflicts": [],
                "warnings": [],
                "suggestions": [],
                "llm_analysis": "Unable to perform conflict analysis",
                "feasibility_score": 0.7,
                "total_issues": 0
            }
    
    async def _check_day_conflicts(self, day: Dict, day_number: int) -> Dict[str, List]:
        """Check conflicts within a single day"""
        conflicts = []
        warnings = []
        suggestions = []
        
        activities = day.get('activities', [])
        
        # Check 1: Too many activities
        if len(activities) > self.max_activities_per_day:
            conflicts.append({
                "type": "too_many_activities",
                "severity": "high",
                "day": day_number,
                "message": f"Day {day_number} has {len(activities)} activities (max recommended: {self.max_activities_per_day})",
                "suggestion": f"Consider moving {len(activities) - self.max_activities_per_day} activities to other days"
            })
        
        # Check 2: Time conflicts and overlaps
        time_conflicts = self._check_time_overlaps(activities, day_number)
        conflicts.extend(time_conflicts)
        
        # Check 3: Unrealistic travel times
        travel_warnings = self._check_travel_feasibility(activities, day_number)
        warnings.extend(travel_warnings)
        
        # Check 4: Activity duration reasonableness
        duration_issues = self._check_activity_durations(activities, day_number)
        warnings.extend(duration_issues)
        
        # Check 5: Day overload (total time)
        total_time_check = self._check_total_day_time(activities, day_number)
        if total_time_check:
            warnings.append(total_time_check)
        
        return {
            "conflicts": conflicts,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _check_time_overlaps(self, activities: List[Dict], day_number: int) -> List[Dict]:
        """Check for time overlaps between activities"""
        conflicts = []
        
        # Parse and sort activities by time
        timed_activities = []
        for i, activity in enumerate(activities):
            time_str = activity.get('time', '')
            try:
                # Parse time (assuming format like "9:00 AM", "2:30 PM")
                time_obj = datetime.strptime(time_str, "%I:%M %p") if time_str else None
                duration_str = activity.get('duration', '2 hours')
                duration_minutes = self._parse_duration(duration_str)
                
                if time_obj and duration_minutes:
                    end_time = time_obj + timedelta(minutes=duration_minutes)
                    timed_activities.append({
                        "index": i,
                        "start": time_obj,
                        "end": end_time,
                        "activity": activity
                    })
            except:
                continue
        
        # Check for overlaps
        timed_activities.sort(key=lambda x: x['start'])
        
        for i in range(len(timed_activities) - 1):
            current = timed_activities[i]
            next_activity = timed_activities[i + 1]
            
            if current['end'] > next_activity['start']:
                conflicts.append({
                    "type": "time_overlap",
                    "severity": "high",
                    "day": day_number,
                    "message": f"Activity '{current['activity']['title']}' overlaps with '{next_activity['activity']['title']}'",
                    "activities": [current['activity']['title'], next_activity['activity']['title']],
                    "suggestion": "Adjust timing or reduce duration of activities"
                })
        
        return conflicts
    
    def _check_travel_feasibility(self, activities: List[Dict], day_number: int) -> List[Dict]:
        """Check if travel between locations is feasible"""
        warnings = []
        
        for i in range(len(activities) - 1):
            current_location = activities[i].get('location', '')
            next_location = activities[i + 1].get('location', '')
            
            if current_location and next_location and current_location != next_location:
                # Estimate travel time (simple heuristic)
                estimated_travel = self._estimate_travel_time(current_location, next_location)
                
                if estimated_travel > 120:  # More than 2 hours
                    warnings.append({
                        "type": "long_travel_time",
                        "severity": "medium",
                        "day": day_number,
                        "message": f"Long travel time (~{estimated_travel//60}h) from {current_location} to {next_location}",
                        "suggestion": "Consider grouping activities by location or adding buffer time"
                    })
        
        return warnings
    
    def _estimate_travel_time(self, location1: str, location2: str) -> int:
        """Estimate travel time between locations (in minutes)"""
        # Simple heuristic - in real implementation, use mapping APIs
        if "airport" in location1.lower() or "airport" in location2.lower():
            return 60  # 1 hour to/from airport
        elif any(word in location1.lower() for word in ["city", "center", "downtown"]):
            return 30  # Within city
        else:
            return 45  # Default inter-location travel
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to minutes"""
        try:
            duration_str = duration_str.lower()
            if 'hour' in duration_str:
                hours = float(duration_str.split()[0])
                return int(hours * 60)
            elif 'minute' in duration_str:
                minutes = float(duration_str.split()[0])
                return int(minutes)
            else:
                return 120  # Default 2 hours
        except:
            return 120
    
    def _check_activity_durations(self, activities: List[Dict], day_number: int) -> List[Dict]:
        """Check if activity durations are reasonable"""
        warnings = []
        
        for activity in activities:
            duration_str = activity.get('duration', '2 hours')
            duration_minutes = self._parse_duration(duration_str)
            
            if duration_minutes < self.min_activity_duration:
                warnings.append({
                    "type": "too_short_activity",
                    "severity": "low",
                    "day": day_number,
                    "message": f"Activity '{activity['title']}' duration ({duration_str}) seems too short",
                    "suggestion": "Consider extending duration or combining with nearby activities"
                })
            elif duration_minutes > self.max_activity_duration:
                warnings.append({
                    "type": "too_long_activity",
                    "severity": "medium",
                    "day": day_number,
                    "message": f"Activity '{activity['title']}' duration ({duration_str}) seems too long",
                    "suggestion": "Consider breaking into multiple activities or reducing duration"
                })
        
        return warnings
    
    def _check_total_day_time(self, activities: List[Dict], day_number: int) -> Optional[Dict]:
        """Check if total day time is reasonable"""
        total_minutes = sum(self._parse_duration(activity.get('duration', '2 hours')) for activity in activities)
        total_hours = total_minutes / 60
        
        if total_hours > 14:  # More than 14 hours of activities
            return {
                "type": "day_overload",
                "severity": "high",
                "day": day_number,
                "message": f"Day {day_number} has {total_hours:.1f} hours of activities (very packed)",
                "suggestion": "Consider reducing activities or spreading across multiple days"
            }
        elif total_hours > 10:  # More than 10 hours
            return {
                "type": "busy_day",
                "severity": "medium",
                "day": day_number,
                "message": f"Day {day_number} has {total_hours:.1f} hours of activities (quite busy)",
                "suggestion": "Ensure adequate rest time between activities"
            }
        
        return None
    
    async def _check_inter_day_conflicts(self, itinerary: List[Dict]) -> Dict[str, List]:
        """Check conflicts between days"""
        conflicts = []
        warnings = []
        
        for i in range(len(itinerary) - 1):
            current_day = itinerary[i]
            next_day = itinerary[i + 1]
            
            # Check if last activity of current day and first activity of next day are feasible
            current_activities = current_day.get('activities', [])
            next_activities = next_day.get('activities', [])
            
            if current_activities and next_activities:
                last_activity = current_activities[-1]
                first_activity = next_activities[0]
                
                # Check overnight location change
                last_location = last_activity.get('location', '')
                first_location = first_activity.get('location', '')
                
                if last_location and first_location and last_location != first_location:
                    travel_time = self._estimate_travel_time(last_location, first_location)
                    if travel_time > 180:  # More than 3 hours
                        warnings.append({
                            "type": "overnight_travel",
                            "severity": "medium",
                            "days": [i + 1, i + 2],
                            "message": f"Long travel required between Day {i+1} and Day {i+2}",
                            "suggestion": "Consider overnight stay or early start time"
                        })
        
        return {"conflicts": conflicts, "warnings": warnings, "suggestions": []}
    
    async def _get_llm_conflict_analysis(self, 
                                       session_id: str, 
                                       itinerary: List[Dict], 
                                       conflicts: List[Dict],
                                       warnings: List[Dict]) -> str:
        """Get LLM analysis of complex conflicts"""
        try:
            if not conflicts and not warnings:
                return "Itinerary looks well-structured with no major conflicts detected."
            
            prompt = f"""
            Analyze this travel itinerary for feasibility and provide expert recommendations:
            
            Itinerary Summary: {len(itinerary)} days with {sum(len(day.get('activities', [])) for day in itinerary)} total activities
            
            Detected Issues:
            Conflicts: {len(conflicts)}
            Warnings: {len(warnings)}
            
            Key Issues:
            {[issue['message'] for issue in conflicts[:3]]}
            {[issue['message'] for issue in warnings[:3]]}
            
            Provide a brief expert analysis (2-3 sentences) focusing on:
            1. Overall feasibility
            2. Main concerns
            3. Priority adjustments needed
            
            Keep response concise and actionable.
            """
            
            llm_client = self._get_llm_client(session_id)
            response = await llm_client.send_message(UserMessage(text=prompt))
            return response
            
        except Exception as e:
            logger.error(f"LLM conflict analysis error: {e}")
            return "Unable to perform detailed analysis. Please review conflicts and warnings manually."
    
    def _calculate_feasibility_score(self, conflicts: List[Dict], warnings: List[Dict]) -> float:
        """Calculate feasibility score (0-1, higher is better)"""
        base_score = 1.0
        
        # Deduct for conflicts
        for conflict in conflicts:
            severity = conflict.get('severity', 'medium')
            if severity == 'high':
                base_score -= 0.15
            elif severity == 'medium':
                base_score -= 0.08
            else:
                base_score -= 0.03
        
        # Deduct for warnings
        for warning in warnings:
            severity = warning.get('severity', 'low')
            if severity == 'high':
                base_score -= 0.08
            elif severity == 'medium':
                base_score -= 0.04
            else:
                base_score -= 0.02
        
        return max(0.0, min(1.0, base_score))
    
    async def suggest_conflict_resolutions(self, 
                                         session_id: str,
                                         conflicts: List[Dict],
                                         itinerary: List[Dict]) -> List[Dict]:
        """Generate specific suggestions to resolve conflicts"""
        try:
            resolutions = []
            
            for conflict in conflicts:
                if conflict['type'] == 'time_overlap':
                    resolutions.append({
                        "conflict_id": f"conflict_{len(resolutions)}",
                        "type": "reschedule",
                        "priority": "high",
                        "description": "Adjust activity timing to prevent overlap",
                        "actions": [
                            {"type": "move_time", "activity": conflict['activities'][1], "new_time": "auto"},
                            {"type": "reduce_duration", "activity": conflict['activities'][0], "new_duration": "auto"}
                        ]
                    })
                elif conflict['type'] == 'too_many_activities':
                    resolutions.append({
                        "conflict_id": f"conflict_{len(resolutions)}",
                        "type": "redistribute",
                        "priority": "medium",
                        "description": "Move some activities to other days",
                        "actions": [
                            {"type": "move_activity", "from_day": conflict['day'], "to_day": "auto", "count": 1}
                        ]
                    })
            
            return resolutions
            
        except Exception as e:
            logger.error(f"Resolution suggestion error: {e}")
            return []