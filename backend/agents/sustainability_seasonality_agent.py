"""
Sustainability & Seasonality Agent - Tags eco-friendly options and adjusts plans 
based on seasonality and events
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import calendar
from models.schemas import ItineraryVariant, Activity
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class SustainabilitySeasonalityAgent:
    """Agent responsible for sustainability tagging and seasonality adjustments"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        
        # Sustainability criteria
        self.sustainability_criteria = {
            "eco_friendly": {
                "keywords": ["nature", "wildlife", "conservation", "organic", "local", "walking", "cycling"],
                "activity_types": ["sightseeing", "cultural", "relaxation"],
                "score_weight": 1.0
            },
            "local_community": {
                "keywords": ["local", "artisan", "community", "traditional", "heritage", "village"],
                "activity_types": ["cultural", "dining", "shopping"],
                "score_weight": 0.8
            },
            "minimal_impact": {
                "keywords": ["small_group", "private", "guided", "educational", "respectful"],
                "activity_types": ["sightseeing", "cultural", "adventure"],
                "score_weight": 0.6
            },
            "sustainable_transport": {
                "keywords": ["walking", "cycling", "local_transport", "shared", "electric"],
                "activity_types": ["transportation"],
                "score_weight": 0.9
            }
        }
        
        # Seasonal data for different destinations
        self.seasonal_data = {
            "goa": {
                "peak_season": [(11, 3)],  # November to March
                "monsoon": [(6, 9)],       # June to September
                "best_weather": [(12, 2)], # December to February
                "events": {
                    "christmas_new_year": {"dates": [(12, 20, 1, 5)], "impact": "high_demand"},
                    "carnival": {"dates": [(2, 15, 2, 20)], "impact": "cultural_highlight"},
                    "monsoon_festivals": {"dates": [(8, 1, 8, 31)], "impact": "indoor_activities"}
                }
            },
            "kerala": {
                "peak_season": [(10, 3)],
                "monsoon": [(6, 8)],
                "best_weather": [(12, 2)],
                "events": {
                    "onam": {"dates": [(8, 15, 8, 25)], "impact": "cultural_highlight"},
                    "boat_races": {"dates": [(8, 1, 9, 30)], "impact": "special_attractions"},
                    "ayurveda_season": {"dates": [(6, 1, 8, 31)], "impact": "wellness_focus"}
                }
            },
            "rajasthan": {
                "peak_season": [(10, 3)],
                "hot_season": [(4, 6)],
                "best_weather": [(11, 2)],
                "events": {
                    "desert_festival": {"dates": [(2, 10, 2, 15)], "impact": "cultural_highlight"},
                    "pushkar_fair": {"dates": [(11, 1, 11, 15)], "impact": "high_demand"},
                    "holi": {"dates": [(3, 10, 3, 15)], "impact": "festive_season"}
                }
            }
        }
    
    async def enhance_variants(self, session_id: str, variants: List[ItineraryVariant]) -> List[ItineraryVariant]:
        """Enhance variants with sustainability and seasonality data"""
        try:
            logger.info(f"🌱 Enhancing {len(variants)} variants with sustainability and seasonality data")
            
            trip_details = self.context_store.get_trip_details(session_id)
            destination = trip_details.get("destination", "").lower()
            travel_date = trip_details.get("start_date", "")
            
            enhanced_variants = []
            for variant in variants:
                enhanced_variant = await self._enhance_single_variant(variant, destination, travel_date)
                enhanced_variants.append(enhanced_variant)
            
            return enhanced_variants
            
        except Exception as e:
            logger.error(f"Variant enhancement error: {e}")
            return variants

    async def _enhance_single_variant(self, variant: ItineraryVariant, destination: str, travel_date: str) -> ItineraryVariant:
        """Enhance a single variant with sustainability and seasonality data"""
        try:
            # Apply sustainability tagging
            variant = await self._apply_sustainability_tags(variant)
            
            # Apply seasonality adjustments
            variant = await self._apply_seasonality_adjustments(variant, destination, travel_date)
            
            # Recalculate sustainability score
            variant.sustainability_score = await self._calculate_sustainability_score(variant)
            
            return variant
            
        except Exception as e:
            logger.error(f"Single variant enhancement error: {e}")
            return variant

    async def _apply_sustainability_tags(self, variant: ItineraryVariant) -> ItineraryVariant:
        """Apply sustainability tags to activities"""
        try:
            for day in variant.daily_itinerary:
                for activity in day.activities:
                    # Clear existing sustainability tags
                    activity.sustainability_tags = []
                    
                    # Apply tags based on criteria
                    for tag_type, criteria in self.sustainability_criteria.items():
                        if self._activity_matches_criteria(activity, criteria):
                            activity.sustainability_tags.append(tag_type)
                    
                    # Add specific tags based on activity analysis
                    specific_tags = await self._get_specific_sustainability_tags(activity)
                    activity.sustainability_tags.extend(specific_tags)
                    
                    # Remove duplicates
                    activity.sustainability_tags = list(set(activity.sustainability_tags))
            
            return variant
            
        except Exception as e:
            logger.error(f"Sustainability tagging error: {e}")
            return variant

    def _activity_matches_criteria(self, activity: Activity, criteria: Dict[str, Any]) -> bool:
        """Check if activity matches sustainability criteria"""
        try:
            # Check keywords in name and description
            text_to_check = f"{activity.name} {activity.description}".lower()
            keyword_match = any(keyword in text_to_check for keyword in criteria["keywords"])
            
            # Check activity type
            type_match = activity.type.value in criteria["activity_types"]
            
            return keyword_match or type_match
            
        except Exception as e:
            logger.error(f"Criteria matching error: {e}")
            return False

    async def _get_specific_sustainability_tags(self, activity: Activity) -> List[str]:
        """Get specific sustainability tags for an activity"""
        try:
            tags = []
            
            activity_text = f"{activity.name} {activity.description}".lower()
            
            # Specific sustainability indicators
            if any(word in activity_text for word in ["organic", "bio", "natural", "chemical-free"]):
                tags.append("organic_certified")
            
            if any(word in activity_text for word in ["carbon", "offset", "neutral", "green"]):
                tags.append("carbon_conscious")
            
            if any(word in activity_text for word in ["waste", "plastic-free", "zero-waste", "recycle"]):
                tags.append("waste_reduction")
            
            if any(word in activity_text for word in ["women", "cooperative", "fair-trade", "social"]):
                tags.append("social_impact")
            
            if any(word in activity_text for word in ["wildlife", "conservation", "protect", "sanctuary"]):
                tags.append("wildlife_conservation")
            
            if any(word in activity_text for word in ["renewable", "solar", "wind", "clean_energy"]):
                tags.append("clean_energy")
            
            # Location-based tags
            if "forest" in activity.location.lower() or "nature" in activity.location.lower():
                tags.append("nature_immersion")
            
            if "village" in activity.location.lower() or "rural" in activity.location.lower():
                tags.append("rural_tourism")
            
            return tags
            
        except Exception as e:
            logger.error(f"Specific sustainability tagging error: {e}")
            return []

    async def _apply_seasonality_adjustments(self, variant: ItineraryVariant, destination: str, travel_date: str) -> ItineraryVariant:
        """Apply seasonality adjustments to variant"""
        try:
            if not travel_date:
                return variant
            
            date_obj = datetime.fromisoformat(travel_date)
            month = date_obj.month
            
            # Get destination seasonal data
            seasonal_info = self._get_seasonal_info(destination, month)
            
            if seasonal_info:
                # Adjust activities based on season
                variant = await self._adjust_activities_for_season(variant, seasonal_info, date_obj)
                
                # Add seasonal recommendations to highlights
                seasonal_highlights = self._get_seasonal_highlights(seasonal_info, date_obj)
                variant.highlights.extend(seasonal_highlights)
                
                # Update title and description with seasonal context
                variant = self._update_variant_for_season(variant, seasonal_info)
            
            return variant
            
        except Exception as e:
            logger.error(f"Seasonality adjustment error: {e}")
            return variant

    def _get_seasonal_info(self, destination: str, month: int) -> Optional[Dict[str, Any]]:
        """Get seasonal information for destination and month"""
        try:
            # Find matching destination
            dest_key = None
            for key in self.seasonal_data.keys():
                if key in destination:
                    dest_key = key
                    break
            
            if not dest_key:
                return None
            
            dest_data = self.seasonal_data[dest_key]
            seasonal_info = {"destination": dest_key, "month": month}
            
            # Determine season type
            if self._is_in_season_range(month, dest_data.get("peak_season", [])):
                seasonal_info["season_type"] = "peak"
            elif self._is_in_season_range(month, dest_data.get("monsoon", [])):
                seasonal_info["season_type"] = "monsoon"
            elif self._is_in_season_range(month, dest_data.get("best_weather", [])):
                seasonal_info["season_type"] = "ideal"
            else:
                seasonal_info["season_type"] = "normal"
            
            # Check for events
            seasonal_info["events"] = []
            for event_name, event_data in dest_data.get("events", {}).items():
                for date_range in event_data["dates"]:
                    if self._is_date_in_range(month, date_range):
                        seasonal_info["events"].append({
                            "name": event_name,
                            "impact": event_data["impact"]
                        })
            
            return seasonal_info
            
        except Exception as e:
            logger.error(f"Seasonal info retrieval error: {e}")
            return None

    def _is_in_season_range(self, month: int, season_ranges: List[tuple]) -> bool:
        """Check if month is in season range"""
        for start_month, end_month in season_ranges:
            if start_month <= end_month:  # Same year range
                if start_month <= month <= end_month:
                    return True
            else:  # Cross-year range (e.g., Nov to Mar)
                if month >= start_month or month <= end_month:
                    return True
        return False

    def _is_date_in_range(self, month: int, date_range: tuple) -> bool:
        """Check if date is in event range"""
        if len(date_range) == 4:  # (start_month, start_day, end_month, end_day)
            start_month, start_day, end_month, end_day = date_range
            if start_month <= end_month:  # Same year
                return start_month <= month <= end_month
            else:  # Cross-year
                return month >= start_month or month <= end_month
        return False

    async def _adjust_activities_for_season(self, variant: ItineraryVariant, seasonal_info: Dict[str, Any], travel_date: datetime) -> ItineraryVariant:
        """Adjust activities based on seasonal information"""
        try:
            season_type = seasonal_info.get("season_type", "normal")
            events = seasonal_info.get("events", [])
            
            for day in variant.daily_itinerary:
                for activity in day.activities:
                    # Adjust for monsoon season
                    if season_type == "monsoon":
                        if activity.type.value in ["adventure", "sightseeing"] and "outdoor" in activity.description.lower():
                            # Add monsoon-specific note
                            activity.description += " (Weather-dependent during monsoon season - indoor alternatives available)"
                            activity.sustainability_tags.append("weather_flexible")
                    
                    # Adjust for peak season
                    elif season_type == "peak":
                        # Add advance booking recommendation
                        activity.description += " (Advance booking recommended during peak season)"
                        activity.sustainability_tags.append("advance_booking")
                    
                    # Add event-specific adjustments
                    for event in events:
                        if event["impact"] == "cultural_highlight":
                            if activity.type.value == "cultural":
                                activity.description += f" (Enhanced during {event['name']} festivities)"
                                activity.sustainability_tags.append("cultural_event")
                        elif event["impact"] == "high_demand":
                            activity.description += f" (High demand during {event['name']} - book early)"
            
            return variant
            
        except Exception as e:
            logger.error(f"Activity season adjustment error: {e}")
            return variant

    def _get_seasonal_highlights(self, seasonal_info: Dict[str, Any], travel_date: datetime) -> List[str]:
        """Get seasonal highlights for the variant"""
        try:
            highlights = []
            season_type = seasonal_info.get("season_type", "normal")
            events = seasonal_info.get("events", [])
            month_name = calendar.month_name[travel_date.month]
            
            # Season-specific highlights
            if season_type == "peak":
                highlights.append(f"Perfect {month_name} weather")
            elif season_type == "monsoon":
                highlights.append(f"Monsoon season charm in {month_name}")
                highlights.append("Lush green landscapes")
            elif season_type == "ideal":
                highlights.append(f"Ideal {month_name} conditions")
            
            # Event-specific highlights
            for event in events:
                event_name = event["name"].replace("_", " ").title()
                if event["impact"] == "cultural_highlight":
                    highlights.append(f"Experience {event_name} celebrations")
                elif event["impact"] == "special_attractions":
                    highlights.append(f"Witness {event_name}")
                elif event["impact"] == "wellness_focus":
                    highlights.append(f"Perfect time for {event_name}")
            
            return highlights
            
        except Exception as e:
            logger.error(f"Seasonal highlights error: {e}")
            return []

    def _update_variant_for_season(self, variant: ItineraryVariant, seasonal_info: Dict[str, Any]) -> ItineraryVariant:
        """Update variant title and description with seasonal context"""
        try:
            season_type = seasonal_info.get("season_type", "normal")
            destination = seasonal_info.get("destination", "").title()
            
            # Add seasonal context to description
            seasonal_contexts = {
                "peak": f"optimized for {destination}'s peak season with perfect weather conditions",
                "monsoon": f"designed for {destination}'s monsoon season with indoor alternatives and rain-friendly activities",
                "ideal": f"crafted for {destination}'s ideal weather period with optimal outdoor experiences",
                "normal": f"tailored for comfortable {destination} exploration"
            }
            
            context = seasonal_contexts.get(season_type, seasonal_contexts["normal"])
            variant.description += f" - {context}"
            
            return variant
            
        except Exception as e:
            logger.error(f"Variant season update error: {e}")
            return variant

    async def _calculate_sustainability_score(self, variant: ItineraryVariant) -> float:
        """Calculate overall sustainability score for variant"""
        try:
            total_activities = sum(len(day.activities) for day in variant.daily_itinerary)
            if total_activities == 0:
                return 0.0
            
            sustainability_score = 0.0
            
            for day in variant.daily_itinerary:
                for activity in day.activities:
                    activity_score = 0.0
                    
                    # Score based on sustainability tags
                    for tag in activity.sustainability_tags:
                        if tag in ["eco_friendly", "organic_certified", "carbon_conscious"]:
                            activity_score += 1.0
                        elif tag in ["local_community", "social_impact", "fair_trade"]:
                            activity_score += 0.8
                        elif tag in ["minimal_impact", "waste_reduction", "sustainable_transport"]:
                            activity_score += 0.6
                        elif tag in ["nature_immersion", "wildlife_conservation", "clean_energy"]:
                            activity_score += 0.4
                        else:
                            activity_score += 0.2
                    
                    # Normalize activity score (max 5.0)
                    activity_score = min(activity_score, 5.0) / 5.0
                    sustainability_score += activity_score
            
            # Return average sustainability score
            return sustainability_score / total_activities
            
        except Exception as e:
            logger.error(f"Sustainability score calculation error: {e}")
            return 0.5  # Default middle score

    async def get_sustainability_recommendations(self, session_id: str) -> Dict[str, Any]:
        """Get sustainability recommendations for the session"""
        try:
            itineraries = self.context_store.get_all_itineraries(session_id)
            trip_details = self.context_store.get_trip_details(session_id)
            
            if not itineraries:
                return {"error": "No itineraries available"}
            
            recommendations = {
                "overall_sustainability": {},
                "eco_alternatives": [],
                "local_impact": [],
                "seasonal_benefits": [],
                "carbon_footprint": {}
            }
            
            # Analyze all variants
            all_activities = []
            for itinerary_data in itineraries.values():
                variant = ItineraryVariant(**itinerary_data)
                for day in variant.daily_itinerary:
                    all_activities.extend(day.activities)
            
            # Calculate overall sustainability metrics
            total_activities = len(all_activities)
            eco_activities = sum(1 for activity in all_activities if "eco_friendly" in activity.sustainability_tags)
            local_activities = sum(1 for activity in all_activities if "local_community" in activity.sustainability_tags)
            
            recommendations["overall_sustainability"] = {
                "eco_friendly_percentage": (eco_activities / max(total_activities, 1)) * 100,
                "local_community_percentage": (local_activities / max(total_activities, 1)) * 100,
                "sustainability_grade": self._get_sustainability_grade(eco_activities + local_activities, total_activities)
            }
            
            # Generate recommendations
            if eco_activities / max(total_activities, 1) < 0.3:
                recommendations["eco_alternatives"].append("Consider more nature-based activities")
                recommendations["eco_alternatives"].append("Look for organic and sustainable dining options")
            
            if local_activities / max(total_activities, 1) < 0.4:
                recommendations["local_impact"].append("Add more local artisan and community experiences")
                recommendations["local_impact"].append("Choose local guides and smaller group tours")
            
            # Seasonal sustainability benefits
            travel_date = trip_details.get("start_date", "")
            if travel_date:
                seasonal_benefits = self._get_seasonal_sustainability_benefits(travel_date, trip_details.get("destination", ""))
                recommendations["seasonal_benefits"] = seasonal_benefits
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Sustainability recommendations error: {e}")
            return {"error": str(e)}

    def _get_sustainability_grade(self, sustainable_activities: int, total_activities: int) -> str:
        """Get sustainability grade based on activity ratio"""
        if total_activities == 0:
            return "N/A"
        
        ratio = sustainable_activities / total_activities
        
        if ratio >= 0.8:
            return "A+ (Excellent)"
        elif ratio >= 0.6:
            return "A (Very Good)"
        elif ratio >= 0.4:
            return "B (Good)"
        elif ratio >= 0.2:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"

    def _get_seasonal_sustainability_benefits(self, travel_date: str, destination: str) -> List[str]:
        """Get seasonal sustainability benefits"""
        try:
            benefits = []
            
            date_obj = datetime.fromisoformat(travel_date)
            month = date_obj.month
            
            # General seasonal benefits
            if month in [6, 7, 8, 9]:  # Monsoon season
                benefits.append("Reduced water usage stress on local resources")
                benefits.append("Supporting local economy during slower tourism period")
                benefits.append("Experiencing natural rain-fed agriculture")
            
            if month in [4, 5]:  # Hot season
                benefits.append("Lower tourism impact due to off-peak travel")
                benefits.append("Supporting local communities during lean period")
            
            if month in [10, 11, 12, 1, 2, 3]:  # Peak/pleasant season
                benefits.append("Optimal conditions for outdoor eco-activities")
                benefits.append("Supporting peak local employment")
            
            return benefits
            
        except Exception as e:
            logger.error(f"Seasonal sustainability benefits error: {e}")
            return []