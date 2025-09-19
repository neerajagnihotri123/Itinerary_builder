"""
Dynamic Pricing Agent - Comprehensive pricing system with real-time adjustments
Handles base pricing, dynamic adjustments, competitor analysis, and profile-based discounts
"""

import asyncio
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os

logger = logging.getLogger(__name__)

class DynamicPricingAgent:
    """Agent for dynamic pricing with competitor awareness and profile-based discounts"""
    
    def __init__(self):
        self.base_rates = {
            # Base rates per category (in INR)
            "accommodation": {"budget": 2000, "moderate": 4000, "luxury": 8000},
            "activities": {"adventure": 1500, "culture": 1000, "nature": 1200, "food": 800},
            "transportation": {"economy": 500, "standard": 1000, "premium": 2000},
            "flight": {"economy": 8000, "business": 25000, "first": 50000}
        }
        
        self.demand_multipliers = {
            "low": 0.8,    # 20% discount during low demand
            "medium": 1.0,  # Base price
            "high": 1.3,   # 30% premium during high demand
            "peak": 1.5    # 50% premium during peak season
        }
        
        self.loyalty_tiers = {
            "new": {"discount": 0.0, "threshold": 0},
            "bronze": {"discount": 0.05, "threshold": 10000},  # 5% discount
            "silver": {"discount": 0.10, "threshold": 25000},  # 10% discount
            "gold": {"discount": 0.15, "threshold": 50000},    # 15% discount
            "platinum": {"discount": 0.20, "threshold": 100000} # 20% discount
        }
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for pricing analysis"""
        return LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            session_id=session_id,
            system_message="You are a travel pricing expert who analyzes market rates and provides competitive pricing strategies."
        ).with_model("openai", "gpt-4o-mini")
    
    async def calculate_dynamic_pricing(self, 
                                      session_id: str,
                                      itinerary: List[Dict],
                                      traveler_profile: Dict,
                                      travel_dates: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive dynamic pricing for entire itinerary
        
        Args:
            session_id: User session ID
            itinerary: Complete itinerary with activities
            traveler_profile: User profile with budget preferences and history
            travel_dates: Start and end dates for travel
        
        Returns:
            Complete pricing breakdown with discounts and justifications
        """
        try:
            pricing_breakdown = {
                "base_total": 0,
                "adjusted_total": 0,
                "final_total": 0,
                "total_savings": 0,
                "line_items": [],
                "discounts_applied": [],
                "demand_analysis": {},
                "competitor_comparison": {},
                "justification": ""
            }
            
            # Calculate base pricing for each component
            base_breakdown = await self._calculate_base_pricing(itinerary, traveler_profile)
            pricing_breakdown["base_total"] = base_breakdown["total"]
            pricing_breakdown["line_items"] = base_breakdown["items"]
            
            # Apply dynamic pricing based on demand
            demand_analysis = await self._analyze_demand(travel_dates, itinerary)
            pricing_breakdown["demand_analysis"] = demand_analysis
            
            # Apply demand multipliers
            adjusted_breakdown = self._apply_demand_pricing(
                base_breakdown["items"], 
                demand_analysis
            )
            pricing_breakdown["adjusted_total"] = adjusted_breakdown["total"]
            pricing_breakdown["line_items"] = adjusted_breakdown["items"]
            
            # Get competitor analysis
            competitor_data = await self._get_competitor_analysis(
                session_id, itinerary, travel_dates
            )
            pricing_breakdown["competitor_comparison"] = competitor_data
            
            # Apply competitive adjustments
            competitive_pricing = self._apply_competitive_adjustments(
                adjusted_breakdown["items"],
                competitor_data
            )
            
            # Apply profile-based discounts
            profile_discounts = self._calculate_profile_discounts(
                traveler_profile,
                competitive_pricing["total"]
            )
            
            # Calculate final pricing
            final_total = competitive_pricing["total"] - profile_discounts["total_discount"]
            
            pricing_breakdown.update({
                "adjusted_total": competitive_pricing["total"],
                "final_total": final_total,
                "total_savings": pricing_breakdown["base_total"] - final_total,
                "line_items": competitive_pricing["items"],
                "discounts_applied": profile_discounts["discounts"],
                "justification": await self._generate_pricing_justification(
                    session_id, pricing_breakdown, competitor_data, profile_discounts
                )
            })
            
            return pricing_breakdown
            
        except Exception as e:
            logger.error(f"Dynamic pricing calculation error: {e}")
            return self._get_fallback_pricing(itinerary)
    
    async def _calculate_base_pricing(self, itinerary: List[Dict], profile: Dict) -> Dict:
        """Calculate base pricing from OTA database"""
        total = 0
        items = []
        
        budget_level = profile.get('budget_level', 'moderate')
        
        for day_idx, day in enumerate(itinerary):
            for activity in day.get('activities', []):
                category = activity.get('category', 'activities')
                
                # Get base rate
                if category in self.base_rates:
                    if category == 'accommodation':
                        base_price = self.base_rates[category].get(budget_level, 4000)
                    elif category in ['adventure', 'culture', 'nature', 'food']:
                        base_price = self.base_rates['activities'].get(category, 1200)
                    else:
                        base_price = self.base_rates['transportation'].get(budget_level, 1000)
                else:
                    base_price = 1500  # Default activity price
                
                # Add some variation based on activity specifics
                duration_multiplier = self._get_duration_multiplier(
                    activity.get('duration', '2 hours')
                )
                final_price = int(base_price * duration_multiplier)
                
                item = {
                    "id": f"day_{day_idx + 1}_{activity.get('title', 'activity')}",
                    "title": activity.get('title', 'Activity'),
                    "category": category,
                    "base_price": final_price,
                    "current_price": final_price,
                    "day": day_idx + 1,
                    "duration": activity.get('duration', '2 hours'),
                    "demand_level": "medium"
                }
                
                items.append(item)
                total += final_price
        
        # Add accommodation costs (per night)
        num_nights = len(itinerary) - 1 if len(itinerary) > 1 else 1
        accommodation_rate = self.base_rates['accommodation'].get(budget_level, 4000)
        
        accommodation_item = {
            "id": "accommodation_total",
            "title": f"Accommodation ({num_nights} nights)",
            "category": "accommodation",
            "base_price": accommodation_rate * num_nights,
            "current_price": accommodation_rate * num_nights,
            "nights": num_nights,
            "rate_per_night": accommodation_rate,
            "demand_level": "medium"
        }
        
        items.append(accommodation_item)
        total += accommodation_item["base_price"]
        
        return {"total": total, "items": items}
    
    def _get_duration_multiplier(self, duration_str: str) -> float:
        """Get pricing multiplier based on activity duration"""
        try:
            if 'hour' in duration_str.lower():
                hours = float(duration_str.split()[0])
                if hours <= 1:
                    return 0.7
                elif hours <= 3:
                    return 1.0
                elif hours <= 6:
                    return 1.4
                else:
                    return 1.8
            else:
                return 1.0
        except:
            return 1.0
    
    async def _analyze_demand(self, travel_dates: Dict, itinerary: List[Dict]) -> Dict:
        """Analyze demand patterns for pricing adjustments"""
        try:
            start_date = datetime.fromisoformat(travel_dates.get('start_date', '2024-12-15'))
            
            # Simulate demand analysis based on season, month, and day of week
            month = start_date.month
            day_of_week = start_date.weekday()
            
            # Seasonal demand
            peak_months = [12, 1, 4, 5, 10, 11]  # Winter and pleasant months in India
            if month in peak_months:
                seasonal_demand = "high"
            elif month in [6, 7, 8, 9]:  # Monsoon
                seasonal_demand = "low"
            else:
                seasonal_demand = "medium"
            
            # Weekend demand
            weekend_demand = "high" if day_of_week in [4, 5, 6] else "medium"
            
            # Overall demand level
            demand_factors = [seasonal_demand, weekend_demand]
            high_count = demand_factors.count("high")
            low_count = demand_factors.count("low")
            
            if high_count >= 2:
                overall_demand = "peak"
            elif high_count >= 1 and low_count == 0:
                overall_demand = "high"
            elif low_count >= 1:
                overall_demand = "low"
            else:
                overall_demand = "medium"
            
            return {
                "overall_level": overall_demand,
                "seasonal": seasonal_demand,
                "weekend_factor": weekend_demand,
                "multiplier": self.demand_multipliers[overall_demand],
                "analysis": f"Travel dates show {overall_demand} demand period"
            }
            
        except Exception as e:
            logger.error(f"Demand analysis error: {e}")
            return {
                "overall_level": "medium",
                "multiplier": 1.0,
                "analysis": "Standard demand period"
            }
    
    def _apply_demand_pricing(self, items: List[Dict], demand_analysis: Dict) -> Dict:
        """Apply demand-based pricing adjustments"""
        multiplier = demand_analysis.get("multiplier", 1.0)
        total = 0
        
        for item in items:
            # Apply demand multiplier
            new_price = int(item["base_price"] * multiplier)
            item["current_price"] = new_price
            item["demand_level"] = demand_analysis.get("overall_level", "medium")
            item["demand_adjustment"] = new_price - item["base_price"]
            total += new_price
        
        return {"total": total, "items": items}
    
    async def _get_competitor_analysis(self, session_id: str, itinerary: List[Dict], travel_dates: Dict) -> Dict:
        """Get competitor pricing analysis using LLM"""
        try:
            # Simulate competitor analysis
            destinations = set()
            for day in itinerary:
                for activity in day.get('activities', []):
                    if activity.get('location'):
                        destinations.add(activity['location'])
            
            # Mock competitor data with realistic variations
            competitors = ["MakeMyTrip", "Booking.com", "Agoda", "Cleartrip"]
            comparison = {}
            
            for dest in list(destinations)[:3]:  # Limit to 3 destinations
                competitor_prices = []
                for comp in competitors:
                    # Generate realistic competitor prices with variation
                    base_variation = random.uniform(0.85, 1.15)
                    competitor_prices.append({
                        "name": comp,
                        "price_variation": base_variation,
                        "estimated_total": int(25000 * base_variation)  # Mock total
                    })
                
                comparison[dest] = competitor_prices
            
            # Calculate average competitor pricing
            all_variations = []
            for dest_prices in comparison.values():
                for comp in dest_prices:
                    all_variations.append(comp["price_variation"])
            
            avg_competitor_multiplier = sum(all_variations) / len(all_variations) if all_variations else 1.0
            
            return {
                "destinations": comparison,
                "average_market_multiplier": avg_competitor_multiplier,
                "market_position": "competitive" if 0.95 <= avg_competitor_multiplier <= 1.05 else "below_market" if avg_competitor_multiplier > 1.05 else "above_market"
            }
            
        except Exception as e:
            logger.error(f"Competitor analysis error: {e}")
            return {"average_market_multiplier": 1.0, "market_position": "competitive"}
    
    def _apply_competitive_adjustments(self, items: List[Dict], competitor_data: Dict) -> Dict:
        """Apply competitive pricing adjustments"""
        market_multiplier = competitor_data.get("average_market_multiplier", 1.0)
        
        # Adjust to stay competitive (slight undercut if market is higher)
        if market_multiplier > 1.02:
            competitive_multiplier = 0.98  # 2% undercut
        elif market_multiplier < 0.98:
            competitive_multiplier = 1.02  # 2% premium for quality
        else:
            competitive_multiplier = 1.0   # Match market
        
        total = 0
        for item in items:
            competitive_price = int(item["current_price"] * competitive_multiplier)
            item["competitive_adjustment"] = competitive_price - item["current_price"]
            item["current_price"] = competitive_price
            total += competitive_price
        
        return {"total": total, "items": items}
    
    def _calculate_profile_discounts(self, profile: Dict, current_total: float) -> Dict:
        """Calculate profile-based discounts and loyalty benefits"""
        discounts = []
        total_discount = 0
        
        # Budget-based discounts
        budget_level = profile.get('budget_level', 'moderate')
        if budget_level == 'budget':
            budget_discount = current_total * 0.08  # 8% discount for budget travelers
            discounts.append({
                "type": "budget_friendly",
                "amount": budget_discount,
                "description": "Budget traveler discount"
            })
            total_discount += budget_discount
        elif budget_level == 'luxury':
            # Luxury travelers get premium services but smaller discounts
            luxury_discount = current_total * 0.03  # 3% small discount
            discounts.append({
                "type": "premium_service",
                "amount": luxury_discount,
                "description": "Premium service value discount"
            })
            total_discount += luxury_discount
        
        # Loyalty tier discounts (mock calculation)
        spending_history = profile.get('spending_history', 0)
        loyalty_tier = self._get_loyalty_tier(spending_history)
        
        if loyalty_tier != 'new':
            loyalty_discount = current_total * self.loyalty_tiers[loyalty_tier]['discount']
            discounts.append({
                "type": "loyalty",
                "tier": loyalty_tier,
                "amount": loyalty_discount,
                "description": f"{loyalty_tier.title()} member discount"
            })
            total_discount += loyalty_discount
        
        # Propensity-to-pay adjustments
        propensity = profile.get('propensity_to_pay', 'medium')
        if propensity == 'low':
            propensity_discount = current_total * 0.05  # Additional 5% for price-sensitive customers
            discounts.append({
                "type": "price_sensitive",
                "amount": propensity_discount,
                "description": "Price-sensitive customer discount"
            })
            total_discount += propensity_discount
        
        return {
            "discounts": discounts,
            "total_discount": total_discount,
            "loyalty_tier": loyalty_tier
        }
    
    def _get_loyalty_tier(self, spending_history: float) -> str:
        """Determine loyalty tier based on spending history"""
        for tier, data in reversed(list(self.loyalty_tiers.items())):
            if spending_history >= data['threshold']:
                return tier
        return 'new'
    
    async def _generate_pricing_justification(self, session_id: str, pricing: Dict, 
                                            competitor_data: Dict, discounts: Dict) -> str:
        """Generate pricing justification message using LLM"""
        try:
            total_savings = pricing.get('total_savings', 0)
            market_position = competitor_data.get('market_position', 'competitive')
            
            justification_parts = []
            
            if total_savings > 0:
                justification_parts.append(f"You're saving ₹{int(total_savings):,} compared to standard rates")
            
            if market_position == 'above_market':
                justification_parts.append("Our prices are highly competitive in the current market")
            elif market_position == 'below_market':
                justification_parts.append("Exceptional value - below typical market rates")
            
            if discounts['discounts']:
                discount_types = [d['type'] for d in discounts['discounts']]
                if 'loyalty' in discount_types:
                    justification_parts.append(f"Exclusive {discounts['loyalty_tier']} member benefits applied")
                if 'budget_friendly' in discount_types:
                    justification_parts.append("Special discount for budget-conscious travelers")
            
            return " • ".join(justification_parts) if justification_parts else "Competitive market pricing applied"
            
        except Exception as e:
            logger.error(f"Justification generation error: {e}")
            return "Dynamic pricing applied based on current market conditions"
    
    def _get_fallback_pricing(self, itinerary: List[Dict]) -> Dict:
        """Fallback pricing if dynamic calculation fails"""
        estimated_total = len(itinerary) * 5000  # Basic estimate
        
        return {
            "base_total": estimated_total,
            "adjusted_total": estimated_total,
            "final_total": estimated_total,
            "total_savings": 0,
            "line_items": [{
                "id": "fallback_estimate",
                "title": "Trip Package",
                "category": "package",
                "base_price": estimated_total,
                "current_price": estimated_total
            }],
            "discounts_applied": [],
            "justification": "Standard package pricing applied"
        }
    
    async def create_checkout_cart(self, session_id: str, pricing_data: Dict, 
                                 itinerary: List[Dict], user_details: Dict) -> Dict:
        """Create checkout cart with all services bundled"""
        try:
            cart_id = f"cart_{session_id}_{int(datetime.now().timestamp())}"
            
            cart = {
                "cart_id": cart_id,
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "status": "pending",
                "user_details": user_details,
                "pricing": pricing_data,
                "itinerary_summary": {
                    "total_days": len(itinerary),
                    "total_activities": sum(len(day.get('activities', [])) for day in itinerary),
                    "destinations": list(set(
                        activity.get('location', '') 
                        for day in itinerary 
                        for activity in day.get('activities', [])
                        if activity.get('location')
                    ))
                },
                "booking_components": [],
                "payment_summary": {
                    "subtotal": pricing_data.get("base_total", 0),
                    "adjustments": pricing_data.get("adjusted_total", 0) - pricing_data.get("base_total", 0),
                    "discounts": -sum(d.get("amount", 0) for d in pricing_data.get("discounts_applied", [])),
                    "total": pricing_data.get("final_total", 0),
                    "currency": "INR"
                }
            }
            
            # Add booking components
            for item in pricing_data.get("line_items", []):
                component = {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "category": item.get("category"),
                    "price": item.get("current_price", 0),
                    "status": "pending_booking",
                    "provider": "OTA_PARTNER",  # Mock OTA partner
                    "booking_reference": None
                }
                cart["booking_components"].append(component)
            
            return cart
            
        except Exception as e:
            logger.error(f"Cart creation error: {e}")
            raise Exception(f"Failed to create checkout cart: {str(e)}")