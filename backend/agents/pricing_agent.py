"""
Pricing Agent - Applies dynamic real-time pricing, competitor benchmarking, 
propensity-to-pay discounts, and transparent pricing breakdown
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import random
from models.schemas import ItineraryVariant, PricingResponse
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore

logger = logging.getLogger(__name__)

class PricingAgent:
    """Agent responsible for dynamic pricing and cost optimization"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        
        # Pricing configuration
        self.base_markup = 0.15  # 15% base markup
        self.seasonal_factors = {
            "peak": 1.4,      # 40% increase during peak season
            "high": 1.2,      # 20% increase during high season
            "normal": 1.0,    # Base pricing
            "low": 0.8        # 20% discount during low season
        }
        
        # Subscribe to pricing events
        self.event_bus.subscribe(EventTypes.PRICING_UPDATE_REQUESTED, self._handle_pricing_update)
    
    async def _handle_pricing_update(self, event):
        """Handle pricing update request event"""
        try:
            session_id = event.session_id
            pricing_data = event.data
            
            logger.info(f"💰 Handling pricing update for session {session_id}")
            
            result = await self.update_pricing(
                session_id, 
                pricing_data.get("itinerary_id")
            )
            
            await self.event_bus.emit(EventTypes.PRICING_UPDATED, {
                "pricing_result": result,
                "itinerary_id": pricing_data.get("itinerary_id")
            }, session_id)
            
        except Exception as e:
            logger.error(f"Pricing update handling error: {e}")

    async def apply_pricing(self, session_id: str, variants: List[ItineraryVariant]) -> List[ItineraryVariant]:
        """Apply dynamic pricing to itinerary variants"""
        try:
            logger.info(f"💰 Applying dynamic pricing to {len(variants)} variants")
            
            # Get session context for personalized pricing
            persona = self.context_store.get_persona(session_id)
            trip_details = self.context_store.get_trip_details(session_id)
            profile = self.context_store.get_profile(session_id)
            
            # Calculate pricing factors
            pricing_factors = await self._calculate_pricing_factors(session_id, trip_details, persona, profile)
            
            # Apply pricing to each variant
            priced_variants = []
            for variant in variants:
                priced_variant = await self._apply_variant_pricing(variant, pricing_factors)
                priced_variants.append(priced_variant)
            
            # Store pricing data
            self.context_store.set_pricing(session_id, {
                "factors": pricing_factors,
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "variants_count": len(variants)
            })
            
            return priced_variants
            
        except Exception as e:
            logger.error(f"Pricing application error: {e}")
            return variants  # Return original variants if pricing fails

    async def update_pricing(self, session_id: str, itinerary_id: str) -> PricingResponse:
        """Update pricing for a specific itinerary"""
        try:
            logger.info(f"💰 Updating pricing for itinerary {itinerary_id}")
            
            # Get itinerary
            itinerary_data = self.context_store.get_itinerary(session_id, itinerary_id)
            if not itinerary_data:
                raise ValueError(f"Itinerary {itinerary_id} not found")
            
            variant = ItineraryVariant(**itinerary_data)
            
            # Get current context
            persona = self.context_store.get_persona(session_id)
            trip_details = self.context_store.get_trip_details(session_id)
            profile = self.context_store.get_profile(session_id)
            
            # Recalculate pricing factors
            pricing_factors = await self._calculate_pricing_factors(session_id, trip_details, persona, profile)
            
            # Apply updated pricing
            updated_variant = await self._apply_variant_pricing(variant, pricing_factors)
            
            # Generate price breakdown
            price_breakdown = await self._generate_price_breakdown(updated_variant, pricing_factors)
            
            # Store updated itinerary
            self.context_store.add_itinerary(session_id, itinerary_id, updated_variant.dict())
            
            return PricingResponse(
                updated_pricing={"total_cost": updated_variant.total_cost},
                price_breakdown=price_breakdown,
                discounts_applied=pricing_factors.get("discounts_applied", [])
            )
            
        except Exception as e:
            logger.error(f"Pricing update error: {e}")
            raise

    async def _calculate_pricing_factors(self, session_id: str, trip_details: Dict[str, Any], 
                                       persona: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate dynamic pricing factors"""
        factors = {
            "base_markup": self.base_markup,
            "seasonal_factor": 1.0,
            "demand_factor": 1.0,
            "persona_factor": 1.0,
            "urgency_factor": 1.0,
            "group_factor": 1.0,
            "loyalty_factor": 1.0,
            "discounts_applied": []
        }
        
        try:
            # Seasonal pricing
            travel_date = trip_details.get("start_date", "")
            if travel_date:
                season = await self._determine_season(travel_date, trip_details.get("destination", ""))
                factors["seasonal_factor"] = self.seasonal_factors.get(season, 1.0)
                if season == "peak":
                    factors["discounts_applied"].append("Peak season pricing")
                elif season == "low":
                    factors["discounts_applied"].append("Low season discount (20%)")
            
            # Demand-based pricing
            factors["demand_factor"] = await self._calculate_demand_factor(trip_details)
            
            # Persona-based pricing
            propensity_to_pay = persona.get("propensity_to_pay", 0.5)
            if propensity_to_pay > 0.8:
                factors["persona_factor"] = 1.1  # 10% premium for high-budget travelers
            elif propensity_to_pay < 0.3:
                factors["persona_factor"] = 0.9  # 10% discount for budget travelers
                factors["discounts_applied"].append("Budget traveler discount (10%)")
            
            # Urgency factor (booking in advance vs last minute)
            urgency_factor = await self._calculate_urgency_factor(travel_date)
            factors["urgency_factor"] = urgency_factor
            if urgency_factor < 1.0:
                factors["discounts_applied"].append("Early booking discount")
            elif urgency_factor > 1.0:
                factors["discounts_applied"].append("Last-minute booking premium")
            
            # Group size factor
            adults = trip_details.get("adults", 1)
            children = trip_details.get("children", 0)
            total_travelers = adults + children
            
            if total_travelers >= 4:
                factors["group_factor"] = 0.95  # 5% group discount
                factors["discounts_applied"].append("Group discount (5%)")
            elif total_travelers == 1:
                factors["group_factor"] = 1.05  # 5% solo traveler premium
            
            # Loyalty factor (mock - would integrate with actual loyalty system)
            factors["loyalty_factor"] = 1.0  # No loyalty adjustment for now
            
        except Exception as e:
            logger.error(f"Pricing factors calculation error: {e}")
        
        return factors

    async def _apply_variant_pricing(self, variant: ItineraryVariant, factors: Dict[str, Any]) -> ItineraryVariant:
        """Apply pricing factors to a variant"""
        try:
            # Calculate overall multiplier
            multiplier = (
                (1 + factors["base_markup"]) *
                factors["seasonal_factor"] *
                factors["demand_factor"] *
                factors["persona_factor"] *
                factors["urgency_factor"] *
                factors["group_factor"] *
                factors["loyalty_factor"]
            )
            
            # Apply to daily costs
            for day in variant.daily_itinerary:
                for activity in day.activities:
                    activity.cost = round(activity.cost * multiplier, 2)
                
                # Recalculate daily total
                day.total_cost = sum(activity.cost for activity in day.activities)
            
            # Recalculate variant total
            variant.total_cost = sum(day.total_cost for day in variant.daily_itinerary)
            
            return variant
            
        except Exception as e:
            logger.error(f"Variant pricing application error: {e}")
            return variant

    async def _determine_season(self, travel_date: str, destination: str) -> str:
        """Determine travel season for pricing"""
        try:
            date = datetime.fromisoformat(travel_date)
            month = date.month
            
            # General Indian tourism seasons (simplified)
            if month in [12, 1, 2]:  # Winter - peak season
                return "peak"
            elif month in [3, 4, 11]:  # Pleasant weather
                return "high"
            elif month in [5, 6]:  # Hot season
                return "low"
            else:  # Monsoon and post-monsoon
                return "normal"
                
        except Exception as e:
            logger.error(f"Season determination error: {e}")
            return "normal"

    async def _calculate_demand_factor(self, trip_details: Dict[str, Any]) -> float:
        """Calculate demand-based pricing factor"""
        try:
            destination = trip_details.get("destination", "").lower()
            
            # Mock demand data - in production would use real-time booking data
            high_demand_destinations = ["goa", "kerala", "rajasthan", "manali"]
            
            if any(dest in destination for dest in high_demand_destinations):
                return 1.1  # 10% premium for high-demand destinations
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"Demand factor calculation error: {e}")
            return 1.0

    async def _calculate_urgency_factor(self, travel_date: str) -> float:
        """Calculate urgency-based pricing factor"""
        try:
            if not travel_date:
                return 1.0
            
            travel_dt = datetime.fromisoformat(travel_date)
            now = datetime.now()
            days_until_travel = (travel_dt - now).days
            
            if days_until_travel > 60:
                return 0.95  # 5% early booking discount
            elif days_until_travel < 7:
                return 1.2   # 20% last-minute premium
            elif days_until_travel < 14:
                return 1.1   # 10% short-notice premium
            else:
                return 1.0   # Standard pricing
                
        except Exception as e:
            logger.error(f"Urgency factor calculation error: {e}")
            return 1.0

    async def _generate_price_breakdown(self, variant: ItineraryVariant, factors: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed price breakdown"""
        try:
            # Calculate base cost (before markups)
            multiplier = (
                (1 + factors["base_markup"]) *
                factors["seasonal_factor"] *
                factors["demand_factor"] *
                factors["persona_factor"] *
                factors["urgency_factor"] *
                factors["group_factor"] *
                factors["loyalty_factor"]
            )
            
            base_cost = variant.total_cost / multiplier
            
            breakdown = {
                "base_cost": round(base_cost, 2),
                "markup": round(base_cost * factors["base_markup"], 2),
                "seasonal_adjustment": round(base_cost * (factors["seasonal_factor"] - 1), 2),
                "demand_adjustment": round(base_cost * (factors["demand_factor"] - 1), 2),
                "persona_adjustment": round(base_cost * (factors["persona_factor"] - 1), 2),
                "urgency_adjustment": round(base_cost * (factors["urgency_factor"] - 1), 2),
                "group_adjustment": round(base_cost * (factors["group_factor"] - 1), 2),
                "total_cost": variant.total_cost,
                "savings": max(0, round(base_cost - variant.total_cost, 2)),
                "daily_breakdown": []
            }
            
            # Daily breakdown
            for day in variant.daily_itinerary:
                day_breakdown = {
                    "day": day.day,
                    "date": day.date,
                    "total": day.total_cost,
                    "activities": []
                }
                
                for activity in day.activities:
                    activity_base_cost = activity.cost / multiplier
                    day_breakdown["activities"].append({
                        "name": activity.name,
                        "base_cost": round(activity_base_cost, 2),
                        "final_cost": activity.cost,
                        "type": activity.type.value
                    })
                
                breakdown["daily_breakdown"].append(day_breakdown)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Price breakdown generation error: {e}")
            return {"error": "Unable to generate price breakdown"}

    async def apply_competitive_pricing(self, session_id: str, variants: List[ItineraryVariant]) -> List[ItineraryVariant]:
        """Apply competitive pricing analysis"""
        try:
            logger.info(f"💰 Applying competitive pricing analysis")
            
            # Mock competitive analysis - in production would integrate with competitor APIs
            for variant in variants:
                # Simulate competitor price checking
                competitor_price = await self._get_competitor_price(variant)
                
                if competitor_price and competitor_price < variant.total_cost:
                    # Apply competitive pricing adjustment
                    adjustment_factor = min(0.95, competitor_price / variant.total_cost)
                    variant = await self._apply_competitive_adjustment(variant, adjustment_factor)
                    
                    # Add discount tag
                    existing_pricing = self.context_store.get_pricing(session_id)
                    if existing_pricing:
                        existing_pricing.setdefault("discounts_applied", []).append("Price match guarantee")
                        self.context_store.set_pricing(session_id, existing_pricing)
            
            return variants
            
        except Exception as e:
            logger.error(f"Competitive pricing error: {e}")
            return variants

    async def _get_competitor_price(self, variant: ItineraryVariant) -> Optional[float]:
        """Get competitor pricing (mock implementation)"""
        try:
            # Mock competitor pricing - would integrate with real APIs
            base_price = variant.total_cost
            
            # Simulate 30% chance of finding lower competitor price
            if random.random() < 0.3:
                # Return price 5-15% lower
                discount_factor = 0.85 + (random.random() * 0.1)  # 0.85 to 0.95
                return base_price * discount_factor
            
            return None
            
        except Exception as e:
            logger.error(f"Competitor price check error: {e}")
            return None

    async def _apply_competitive_adjustment(self, variant: ItineraryVariant, adjustment_factor: float) -> ItineraryVariant:
        """Apply competitive pricing adjustment"""
        try:
            # Apply adjustment to all costs
            for day in variant.daily_itinerary:
                for activity in day.activities:
                    activity.cost = round(activity.cost * adjustment_factor, 2)
                
                # Recalculate daily total
                day.total_cost = sum(activity.cost for activity in day.activities)
            
            # Recalculate variant total
            variant.total_cost = sum(day.total_cost for day in variant.daily_itinerary)
            
            return variant
            
        except Exception as e:
            logger.error(f"Competitive adjustment error: {e}")
            return variant

    def generate_pricing_summary(self, session_id: str) -> Dict[str, Any]:
        """Generate pricing summary for the session"""
        try:
            pricing_data = self.context_store.get_pricing(session_id)
            itineraries = self.context_store.get_all_itineraries(session_id)
            
            if not pricing_data or not itineraries:
                return {"error": "No pricing data available"}
            
            summary = {
                "total_variants": len(itineraries),
                "price_range": {
                    "min": min(itinerary["total_cost"] for itinerary in itineraries.values()),
                    "max": max(itinerary["total_cost"] for itinerary in itineraries.values())
                },
                "discounts_applied": pricing_data.get("discounts_applied", []),
                "pricing_factors": pricing_data.get("factors", {}),
                "last_updated": pricing_data.get("applied_at", ""),
                "savings_opportunities": []
            }
            
            # Identify savings opportunities
            factors = pricing_data.get("factors", {})
            if factors.get("urgency_factor", 1.0) > 1.0:
                summary["savings_opportunities"].append("Book earlier to save on urgency premiums")
            
            if factors.get("seasonal_factor", 1.0) > 1.0:
                summary["savings_opportunities"].append("Consider traveling in off-peak season")
            
            return summary
            
        except Exception as e:
            logger.error(f"Pricing summary generation error: {e}")
            return {"error": "Unable to generate pricing summary"}