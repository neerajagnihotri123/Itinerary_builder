"""
Customization Agent - Manages itinerary edits, swaps, reorderings, and conflict checks
Flags unrealistic plans with suggestions
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models.schemas import ItineraryVariant, Activity, CustomizationResponse
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class CustomizationAgent:
    """Agent responsible for managing itinerary customizations and edits"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        
        # Subscribe to customization events
        self.event_bus.subscribe(EventTypes.CUSTOMIZATION_REQUESTED, self._handle_customization_request)
    
    async def _handle_customization_request(self, event):
        """Handle customization request event"""
        try:
            session_id = event.session_id
            customization_data = event.data
            
            logger.info(f"✏️ Handling customization request for session {session_id}")
            
            result = await self.apply_customizations(
                session_id, 
                customization_data.get("itinerary_id"),
                customization_data.get("customizations", [])
            )
            
            await self.event_bus.emit(EventTypes.CUSTOMIZATION_APPLIED, {
                "customization_result": result,
                "itinerary_id": customization_data.get("itinerary_id")
            }, session_id)
            
        except Exception as e:
            logger.error(f"Customization request handling error: {e}")

    async def apply_customizations(self, session_id: str, itinerary_id: str, customizations: List[Dict[str, Any]]) -> CustomizationResponse:
        """Apply customizations to an itinerary"""
        try:
            logger.info(f"✏️ Applying customizations to itinerary {itinerary_id}")
            
            # Get current itinerary
            itinerary_data = self.context_store.get_itinerary(session_id, itinerary_id)
            if not itinerary_data:
                raise ValueError(f"Itinerary {itinerary_id} not found")
            
            # Parse itinerary
            itinerary = ItineraryVariant(**itinerary_data)
            
            # Apply each customization
            conflicts = []
            suggestions = []
            
            for customization in customizations:
                customization_result = await self._apply_single_customization(
                    itinerary, customization
                )
                conflicts.extend(customization_result.get("conflicts", []))
                suggestions.extend(customization_result.get("suggestions", []))
            
            # Validate updated itinerary
            validation_result = await self._validate_itinerary(itinerary)
            conflicts.extend(validation_result.get("conflicts", []))
            suggestions.extend(validation_result.get("suggestions", []))
            
            # Recalculate totals
            itinerary = self._recalculate_totals(itinerary)
            
            # Store updated itinerary
            self.context_store.add_itinerary(session_id, itinerary.id, itinerary.dict())
            
            # Log customization
            self.context_store.add_customization(session_id, {
                "itinerary_id": itinerary_id,
                "customizations": customizations,
                "conflicts": conflicts,
                "suggestions": suggestions
            })
            
            return CustomizationResponse(
                updated_variant=itinerary,
                conflicts=list(set(conflicts)),  # Remove duplicates
                suggestions=list(set(suggestions))
            )
            
        except Exception as e:
            logger.error(f"Customization application error: {e}")
            raise

    async def _apply_single_customization(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single customization to the itinerary"""
        customization_type = customization.get("type")
        conflicts = []
        suggestions = []
        
        if customization_type == "activity_swap":
            result = await self._swap_activity(itinerary, customization)
        elif customization_type == "activity_add":
            result = await self._add_activity(itinerary, customization)
        elif customization_type == "activity_remove":
            result = await self._remove_activity(itinerary, customization)
        elif customization_type == "reorder_activities":
            result = await self._reorder_activities(itinerary, customization)
        elif customization_type == "change_timing":
            result = await self._change_timing(itinerary, customization)
        elif customization_type == "adjust_budget":
            result = await self._adjust_budget(itinerary, customization)
        else:
            result = {"conflicts": [f"Unknown customization type: {customization_type}"]}
        
        return result

    async def _swap_activity(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Swap an activity with another"""
        day_index = customization.get("day") - 1
        activity_index = customization.get("activity_index")
        new_activity_data = customization.get("new_activity")
        
        conflicts = []
        suggestions = []
        
        try:
            if day_index >= len(itinerary.daily_itinerary):
                conflicts.append(f"Day {customization.get('day')} does not exist")
                return {"conflicts": conflicts}
            
            day = itinerary.daily_itinerary[day_index]
            
            if activity_index >= len(day.activities):
                conflicts.append(f"Activity index {activity_index} does not exist on day {customization.get('day')}")
                return {"conflicts": conflicts}
            
            # Create new activity
            new_activity = Activity(**new_activity_data)
            
            # Check timing conflicts
            timing_conflicts = self._check_timing_conflicts(day, new_activity, activity_index)
            conflicts.extend(timing_conflicts)
            
            if not conflicts:
                # Replace activity
                day.activities[activity_index] = new_activity
                suggestions.append(f"Successfully swapped activity on day {customization.get('day')}")
            
        except Exception as e:
            conflicts.append(f"Activity swap error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    async def _add_activity(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new activity to the itinerary"""
        day_index = customization.get("day") - 1
        new_activity_data = customization.get("activity")
        insert_index = customization.get("insert_index", -1)
        
        conflicts = []
        suggestions = []
        
        try:
            if day_index >= len(itinerary.daily_itinerary):
                conflicts.append(f"Day {customization.get('day')} does not exist")
                return {"conflicts": conflicts}
            
            day = itinerary.daily_itinerary[day_index]
            new_activity = Activity(**new_activity_data)
            
            # Check daily capacity
            if len(day.activities) >= 8:
                conflicts.append(f"Day {customization.get('day')} already has maximum activities (8)")
                suggestions.append("Consider moving some activities to another day")
                return {"conflicts": conflicts, "suggestions": suggestions}
            
            # Check timing conflicts
            timing_conflicts = self._check_timing_conflicts(day, new_activity)
            conflicts.extend(timing_conflicts)
            
            if not conflicts:
                if insert_index == -1:
                    day.activities.append(new_activity)
                else:
                    day.activities.insert(insert_index, new_activity)
                suggestions.append(f"Successfully added activity to day {customization.get('day')}")
            
        except Exception as e:
            conflicts.append(f"Activity addition error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    async def _remove_activity(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Remove an activity from the itinerary"""
        day_index = customization.get("day") - 1
        activity_index = customization.get("activity_index")
        
        conflicts = []
        suggestions = []
        
        try:
            if day_index >= len(itinerary.daily_itinerary):
                conflicts.append(f"Day {customization.get('day')} does not exist")
                return {"conflicts": conflicts}
            
            day = itinerary.daily_itinerary[day_index]
            
            if activity_index >= len(day.activities):
                conflicts.append(f"Activity index {activity_index} does not exist on day {customization.get('day')}")
                return {"conflicts": conflicts}
            
            # Check minimum activities
            if len(day.activities) <= 2:
                conflicts.append(f"Day {customization.get('day')} needs minimum 2 activities")
                suggestions.append("Consider replacing the activity instead of removing it")
                return {"conflicts": conflicts, "suggestions": suggestions}
            
            # Remove activity
            removed_activity = day.activities.pop(activity_index)
            suggestions.append(f"Successfully removed '{removed_activity.name}' from day {customization.get('day')}")
            
        except Exception as e:
            conflicts.append(f"Activity removal error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    async def _reorder_activities(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Reorder activities within a day"""
        day_index = customization.get("day") - 1
        new_order = customization.get("new_order")  # List of activity indices
        
        conflicts = []
        suggestions = []
        
        try:
            if day_index >= len(itinerary.daily_itinerary):
                conflicts.append(f"Day {customization.get('day')} does not exist")
                return {"conflicts": conflicts}
            
            day = itinerary.daily_itinerary[day_index]
            
            if len(new_order) != len(day.activities):
                conflicts.append("New order must include all activities")
                return {"conflicts": conflicts}
            
            # Reorder activities
            original_activities = day.activities.copy()
            day.activities = [original_activities[i] for i in new_order]
            
            # Check if reordering creates timing conflicts
            timing_conflicts = self._check_day_timing_flow(day)
            if timing_conflicts:
                # Revert if conflicts
                day.activities = original_activities
                conflicts.extend(timing_conflicts)
                suggestions.append("Consider adjusting activity timings after reordering")
            else:
                suggestions.append(f"Successfully reordered activities on day {customization.get('day')}")
            
        except Exception as e:
            conflicts.append(f"Activity reordering error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    async def _change_timing(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Change timing of an activity"""
        day_index = customization.get("day") - 1
        activity_index = customization.get("activity_index")
        new_time = customization.get("new_time")
        
        conflicts = []
        suggestions = []
        
        try:
            if day_index >= len(itinerary.daily_itinerary):
                conflicts.append(f"Day {customization.get('day')} does not exist")
                return {"conflicts": conflicts}
            
            day = itinerary.daily_itinerary[day_index]
            
            if activity_index >= len(day.activities):
                conflicts.append(f"Activity index {activity_index} does not exist on day {customization.get('day')}")
                return {"conflicts": conflicts}
            
            activity = day.activities[activity_index]
            original_time = activity.time
            
            # Update timing
            activity.time = new_time
            
            # Check timing conflicts
            timing_conflicts = self._check_day_timing_flow(day)
            if timing_conflicts:
                # Revert if conflicts
                activity.time = original_time
                conflicts.extend(timing_conflicts)
                suggestions.append("Consider adjusting other activities' timings to accommodate this change")
            else:
                suggestions.append(f"Successfully updated timing for '{activity.name}' to {new_time}")
            
        except Exception as e:
            conflicts.append(f"Timing change error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    async def _adjust_budget(self, itinerary: ItineraryVariant, customization: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust budget constraints for the itinerary"""
        target_budget = customization.get("target_budget")
        
        conflicts = []
        suggestions = []
        
        try:
            current_cost = itinerary.total_cost
            
            if target_budget < current_cost * 0.5:
                conflicts.append(f"Target budget ₹{target_budget} is too low (minimum ₹{current_cost * 0.5})")
                suggestions.append("Consider removing luxury activities or choosing budget alternatives")
            elif target_budget > current_cost * 2:
                suggestions.append("You have room to upgrade to premium experiences")
            else:
                suggestions.append(f"Budget adjustment from ₹{current_cost} to ₹{target_budget} is feasible")
            
        except Exception as e:
            conflicts.append(f"Budget adjustment error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    def _check_timing_conflicts(self, day, new_activity: Activity, exclude_index: Optional[int] = None) -> List[str]:
        """Check for timing conflicts when adding/changing an activity"""
        conflicts = []
        
        try:
            new_start = datetime.strptime(new_activity.time, "%H:%M")
            new_duration_hours = self._parse_duration(new_activity.duration)
            new_end = new_start + timedelta(hours=new_duration_hours)
            
            for i, existing_activity in enumerate(day.activities):
                if exclude_index is not None and i == exclude_index:
                    continue
                
                existing_start = datetime.strptime(existing_activity.time, "%H:%M")
                existing_duration_hours = self._parse_duration(existing_activity.duration)
                existing_end = existing_start + timedelta(hours=existing_duration_hours)
                
                # Check overlap
                if not (new_end <= existing_start or new_start >= existing_end):
                    conflicts.append(f"Timing conflict with '{existing_activity.name}' at {existing_activity.time}")
            
        except Exception as e:
            conflicts.append(f"Timing validation error: {str(e)}")
        
        return conflicts

    def _check_day_timing_flow(self, day) -> List[str]:
        """Check the overall timing flow of a day"""
        conflicts = []
        
        try:
            # Sort activities by time
            sorted_activities = sorted(day.activities, key=lambda x: datetime.strptime(x.time, "%H:%M"))
            
            for i in range(len(sorted_activities) - 1):
                current_activity = sorted_activities[i]
                next_activity = sorted_activities[i + 1]
                
                current_start = datetime.strptime(current_activity.time, "%H:%M")
                current_duration = self._parse_duration(current_activity.duration)
                current_end = current_start + timedelta(hours=current_duration)
                
                next_start = datetime.strptime(next_activity.time, "%H:%M")
                
                # Check for overlap
                if current_end > next_start:
                    conflicts.append(f"'{current_activity.name}' overlaps with '{next_activity.name}'")
                
                # Check for reasonable gaps (minimum 30 minutes for transitions)
                gap = (next_start - current_end).total_seconds() / 60
                if gap < 30 and gap > 0:
                    conflicts.append(f"Too little time ({int(gap)} minutes) between '{current_activity.name}' and '{next_activity.name}'")
            
        except Exception as e:
            conflicts.append(f"Day timing flow error: {str(e)}")
        
        return conflicts

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to hours"""
        try:
            if "hour" in duration_str.lower():
                return float(duration_str.lower().split("hour")[0].strip())
            elif "minute" in duration_str.lower():
                minutes = float(duration_str.lower().split("minute")[0].strip())
                return minutes / 60
            else:
                return 2.0  # Default 2 hours
        except:
            return 2.0  # Default fallback

    async def _validate_itinerary(self, itinerary: ItineraryVariant) -> Dict[str, Any]:
        """Validate the entire itinerary for consistency and feasibility"""
        conflicts = []
        suggestions = []
        
        try:
            # Check daily activity counts
            for day_index, day in enumerate(itinerary.daily_itinerary):
                if len(day.activities) < 2:
                    conflicts.append(f"Day {day.day} has too few activities (minimum 2)")
                elif len(day.activities) > 8:
                    conflicts.append(f"Day {day.day} has too many activities (maximum 8)")
                
                # Check day timing flow
                timing_conflicts = self._check_day_timing_flow(day)
                conflicts.extend(timing_conflicts)
                
                # Check realistic daily budget
                if day.total_cost > 50000:
                    suggestions.append(f"Day {day.day} budget is very high (₹{day.total_cost})")
                elif day.total_cost < 2000:
                    suggestions.append(f"Day {day.day} budget seems low (₹{day.total_cost})")
            
            # Check overall itinerary balance
            activity_types = [activity.type.value for day in itinerary.daily_itinerary for activity in day.activities]
            
            if activity_types.count("dining") < itinerary.days:
                suggestions.append("Consider adding more dining experiences")
            
            if activity_types.count("relaxation") == 0 and itinerary.days > 3:
                suggestions.append("Consider adding relaxation activities for longer trips")
            
        except Exception as e:
            conflicts.append(f"Itinerary validation error: {str(e)}")
        
        return {"conflicts": conflicts, "suggestions": suggestions}

    def _recalculate_totals(self, itinerary: ItineraryVariant) -> ItineraryVariant:
        """Recalculate totals after customizations"""
        try:
            # Recalculate daily totals
            for day in itinerary.daily_itinerary:
                day.total_cost = sum(activity.cost for activity in day.activities)
            
            # Recalculate itinerary totals
            itinerary.total_cost = sum(day.total_cost for day in itinerary.daily_itinerary)
            itinerary.total_activities = sum(len(day.activities) for day in itinerary.daily_itinerary)
            
            # Update activity types
            activity_types = list(set([
                activity.type.value for day in itinerary.daily_itinerary 
                for activity in day.activities
            ]))
            itinerary.activity_types = activity_types
            
        except Exception as e:
            logger.error(f"Total recalculation error: {e}")
        
        return itinerary