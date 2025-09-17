"""
PricingAgent - Dynamic pricing engine with market intelligence and personalization
Handles dynamic pricing, upselling strategies and personalized pricing based on user persona
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class PricingAgent:
    """Dynamic pricing engine with market intelligence and personalization"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
        # Base pricing configurations
        self.base_pricing = {
            "accommodation": {
                "budget": {"min": 2000, "max": 5000, "currency": "INR"},
                "mid_range": {"min": 5000, "max": 12000, "currency": "INR"},
                "luxury": {"min": 12000, "max": 50000, "currency": "INR"},
                "premium": {"min": 50000, "max": 200000, "currency": "INR"}
            },
            "activities": {
                "adventure": {"min": 2000, "max": 15000, "currency": "INR"},
                "cultural": {"min": 500, "max": 8000, "currency": "INR"},
                "luxury_experiences": {"min": 10000, "max": 100000, "currency": "INR"},
                "food_experiences": {"min": 1000, "max": 25000, "currency": "INR"}
            },
            "transportation": {
                "budget": {"min": 500, "max": 3000, "currency": "INR"},
                "comfortable": {"min": 3000, "max": 10000, "currency": "INR"},
                "premium": {"min": 10000, "max": 50000, "currency": "INR"}
            }
        }
        
        # Seasonal multipliers
        self.seasonal_multipliers = {
            "peak_season": 1.4,      # Oct-Mar for most destinations
            "shoulder_season": 1.1,   # Apr-May, Sep
            "off_season": 0.8,       # Jun-Aug (monsoon)
            "festival_season": 1.6,   # During major festivals
            "wedding_season": 1.3     # Nov-Feb
        }
        
        # Persona-based pricing strategies
        self.persona_pricing_strategies = {
            "luxury_connoisseur": {
                "price_sensitivity": 0.2,
                "upsell_probability": 0.9,
                "premium_preference": 1.5,
                "discount_effectiveness": 0.3
            },
            "adventure_seeker": {
                "price_sensitivity": 0.6,
                "upsell_probability": 0.7,
                "premium_preference": 0.8,
                "discount_effectiveness": 0.6
            },
            "cultural_explorer": {
                "price_sensitivity": 0.5,
                "upsell_probability": 0.8,
                "premium_preference": 1.0,
                "discount_effectiveness": 0.5
            },
            "budget_backpacker": {
                "price_sensitivity": 0.9,
                "upsell_probability": 0.3,
                "premium_preference": 0.4,
                "discount_effectiveness": 0.9
            },
            "eco_conscious_traveler": {
                "price_sensitivity": 0.4,
                "upsell_probability": 0.8,
                "premium_preference": 1.2,
                "discount_effectiveness": 0.4
            }
        }
    
    async def calculate_dynamic_pricing(self, service_type: str, service_details: dict, user_profile: dict, booking_context: dict) -> dict:
        """Calculate dynamic pricing based on multiple factors"""
        
        base_price = self._get_base_price(service_type, service_details)
        
        # Apply various pricing factors
        seasonal_adjustment = self._calculate_seasonal_adjustment(booking_context.get("travel_dates"))
        demand_adjustment = await self._calculate_demand_adjustment(service_details, booking_context)
        persona_adjustment = self._calculate_persona_adjustment(user_profile)
        urgency_adjustment = self._calculate_urgency_adjustment(booking_context)
        
        # Calculate final price
        final_price = base_price * seasonal_adjustment * demand_adjustment * persona_adjustment * urgency_adjustment
        
        # Generate pricing explanation
        pricing_explanation = await self._generate_pricing_explanation(
            base_price, final_price, 
            {
                "seasonal": seasonal_adjustment,
                "demand": demand_adjustment,
                "persona": persona_adjustment,
                "urgency": urgency_adjustment
            }
        )
        
        return {
            "service_type": service_type,
            "base_price": base_price,
            "final_price": round(final_price),
            "currency": "INR",
            "pricing_factors": {
                "seasonal_adjustment": seasonal_adjustment,
                "demand_adjustment": demand_adjustment,
                "persona_adjustment": persona_adjustment,
                "urgency_adjustment": urgency_adjustment
            },
            "pricing_explanation": pricing_explanation,
            "discount_opportunities": self._identify_discount_opportunities(user_profile, final_price),
            "upsell_opportunities": await self._identify_upsell_opportunities(service_type, service_details, user_profile)
        }
    
    def _get_base_price(self, service_type: str, service_details: dict) -> float:
        """Get base price for service"""
        
        if service_type == "accommodation":
            category = service_details.get("category", "mid_range")
            price_range = self.base_pricing["accommodation"].get(category, self.base_pricing["accommodation"]["mid_range"])
            return (price_range["min"] + price_range["max"]) / 2
        
        elif service_type == "activity":
            activity_type = service_details.get("activity_type", "cultural")
            price_range = self.base_pricing["activities"].get(activity_type, self.base_pricing["activities"]["cultural"])
            return (price_range["min"] + price_range["max"]) / 2
        
        elif service_type == "transportation":
            transport_class = service_details.get("class", "comfortable")
            price_range = self.base_pricing["transportation"].get(transport_class, self.base_pricing["transportation"]["comfortable"])
            return (price_range["min"] + price_range["max"]) / 2
        
        else:
            return 5000  # Default fallback price
    
    def _calculate_seasonal_adjustment(self, travel_dates: dict) -> float:
        """Calculate seasonal pricing adjustment"""
        
        if not travel_dates or not travel_dates.get("start_date"):
            return 1.0
        
        try:
            start_date = datetime.fromisoformat(travel_dates["start_date"].replace("Z", "+00:00"))
            month = start_date.month
            
            # Peak season (Oct-Mar)
            if month in [10, 11, 12, 1, 2, 3]:
                return self.seasonal_multipliers["peak_season"]
            # Shoulder season (Apr-May, Sep)
            elif month in [4, 5, 9]:
                return self.seasonal_multipliers["shoulder_season"]
            # Off season (Jun-Aug)
            else:
                return self.seasonal_multipliers["off_season"]
                
        except Exception:
            return 1.0
    
    async def _calculate_demand_adjustment(self, service_details: dict, booking_context: dict) -> float:
        """Calculate demand-based pricing adjustment using market intelligence"""
        
        try:
            # Use LLM to analyze market demand
            context = f"""
            Analyze current market demand for this travel service and provide a demand multiplier between 0.7 and 1.5:
            
            Service: {service_details.get('name', 'Travel service')}
            Location: {service_details.get('location', 'Unknown')}
            Booking Context: {json.dumps(booking_context, indent=2)}
            
            Consider factors:
            1. Popular events or festivals in the area
            2. Weather conditions and seasonality
            3. Local holidays and vacation periods
            4. Market trends and booking patterns
            
            Return only a number between 0.7 and 1.5 representing the demand multiplier.
            Examples: 1.3 (high demand), 1.0 (normal demand), 0.8 (low demand)
            """
            
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=10.0
            )
            
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract number from response
            import re
            numbers = re.findall(r'\d+\.?\d*', content)
            if numbers:
                multiplier = float(numbers[0])
                return max(0.7, min(1.5, multiplier))
            
        except Exception as e:
            print(f"Demand calculation failed: {e}")
        
        return 1.0  # Default to no adjustment
    
    def _calculate_persona_adjustment(self, user_profile: dict) -> float:
        """Calculate persona-based pricing adjustment"""
        
        persona_classification = user_profile.get("persona_classification", {})
        primary_persona = persona_classification.get("primary_persona", "cultural_explorer")
        
        strategy = self.persona_pricing_strategies.get(primary_persona, self.persona_pricing_strategies["cultural_explorer"])
        
        # Adjust based on persona preferences
        if primary_persona == "luxury_connoisseur":
            return 1.2  # Show premium options
        elif primary_persona == "budget_backpacker":
            return 0.8  # Show budget-friendly options
        else:
            return 1.0  # No adjustment for balanced personas
    
    def _calculate_urgency_adjustment(self, booking_context: dict) -> float:
        """Calculate urgency-based pricing adjustment"""
        
        travel_dates = booking_context.get("travel_dates", {})
        if not travel_dates.get("start_date"):
            return 1.0
        
        try:
            start_date = datetime.fromisoformat(travel_dates["start_date"].replace("Z", "+00:00"))
            days_until_travel = (start_date - datetime.now()).days
            
            if days_until_travel < 7:
                return 1.3  # Last-minute booking premium
            elif days_until_travel < 30:
                return 1.1  # Short notice premium
            elif days_until_travel > 180:
                return 0.9  # Early booking discount
            else:
                return 1.0  # Normal pricing
                
        except Exception:
            return 1.0
    
    async def _generate_pricing_explanation(self, base_price: float, final_price: float, factors: dict) -> str:
        """Generate user-friendly pricing explanation"""
        
        try:
            context = f"""
            Create a friendly, transparent explanation for this pricing:
            
            Base Price: ₹{base_price:,.0f}
            Final Price: ₹{final_price:,.0f}
            
            Pricing Factors:
            - Seasonal: {factors['seasonal']:.2f}x
            - Market Demand: {factors['demand']:.2f}x  
            - Personalization: {factors['persona']:.2f}x
            - Booking Urgency: {factors['urgency']:.2f}x
            
            Create a 1-2 sentence explanation that:
            1. Is transparent about pricing factors
            2. Sounds friendly and helpful
            3. Emphasizes value rather than just cost
            4. Mentions any discounts or premium factors
            
            Example: "This price reflects peak season demand and includes premium experiences tailored to your preferences. You're getting excellent value with our curated selection!"
            """
            
            from emergentintegrations.llm.chat import UserMessage
            user_message = UserMessage(text=context)
            response = await asyncio.wait_for(
                self.llm_client.send_message(user_message),
                timeout=10.0
            )
            
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            print(f"Pricing explanation generation failed: {e}")
            
            # Fallback explanation
            if final_price > base_price:
                return f"This price includes premium features and peak season availability, ensuring you get the best experience."
            elif final_price < base_price:
                return f"Great news! You're getting a fantastic deal with our current promotional pricing."
            else:
                return f"This is our standard competitive price for this high-quality experience."
    
    def _identify_discount_opportunities(self, user_profile: dict, price: float) -> List[dict]:
        """Identify potential discount opportunities"""
        
        opportunities = []
        persona_classification = user_profile.get("persona_classification", {})
        primary_persona = persona_classification.get("primary_persona", "cultural_explorer")
        
        strategy = self.persona_pricing_strategies.get(primary_persona, {})
        discount_effectiveness = strategy.get("discount_effectiveness", 0.5)
        
        if discount_effectiveness > 0.7:  # Highly price-sensitive personas
            opportunities.extend([
                {
                    "type": "early_bird",
                    "description": "Book 60 days in advance and save 15%",
                    "discount_percentage": 15,
                    "applicable": price > 10000
                },
                {
                    "type": "package_deal",
                    "description": "Bundle with accommodation for additional 10% off",
                    "discount_percentage": 10,
                    "applicable": True
                }
            ])
        
        if primary_persona == "eco_conscious_traveler":
            opportunities.append({
                "type": "sustainability_bonus",
                "description": "5% discount for choosing eco-certified options",
                "discount_percentage": 5,
                "applicable": True
            })
        
        return opportunities
    
    async def _identify_upsell_opportunities(self, service_type: str, service_details: dict, user_profile: dict) -> List[dict]:
        """Identify personalized upsell opportunities"""
        
        opportunities = []
        persona_classification = user_profile.get("persona_classification", {})
        primary_persona = persona_classification.get("primary_persona", "cultural_explorer")
        
        strategy = self.persona_pricing_strategies.get(primary_persona, {})
        upsell_probability = strategy.get("upsell_probability", 0.5)
        
        if upsell_probability > 0.6:  # High upsell potential
            
            if service_type == "accommodation":
                opportunities.extend([
                    {
                        "type": "room_upgrade",
                        "title": "Premium Room Upgrade",
                        "description": "Upgrade to a suite with panoramic views",
                        "additional_cost": 5000,
                        "value_proposition": "30% more space + complimentary breakfast"
                    },
                    {
                        "type": "spa_package",
                        "title": "Wellness Package Add-on",
                        "description": "Rejuvenating spa treatments and yoga sessions",
                        "additional_cost": 8000,
                        "value_proposition": "Complete relaxation experience"
                    }
                ])
            
            elif service_type == "activity":
                if primary_persona == "adventure_seeker":
                    opportunities.append({
                        "type": "premium_equipment",
                        "title": "Premium Equipment Package",
                        "description": "Top-tier safety gear and professional photography",
                        "additional_cost": 3000,
                        "value_proposition": "Enhanced safety + professional memories"
                    })
                
                elif primary_persona == "luxury_connoisseur":
                    opportunities.append({
                        "type": "private_guide",
                        "title": "Private Expert Guide",
                        "description": "Exclusive access with certified local expert",
                        "additional_cost": 12000,
                        "value_proposition": "Personalized experience + insider knowledge"
                    })
        
        return opportunities
    
    async def generate_checkout_pricing_summary(self, items: List[dict], user_profile: dict) -> dict:
        """Generate comprehensive pricing summary for checkout"""
        
        total_base_price = 0
        total_final_price = 0
        all_discounts = []
        all_upsells = []
        
        # Calculate pricing for each item
        for item in items:
            pricing = await self.calculate_dynamic_pricing(
                item["service_type"], 
                item["details"], 
                user_profile, 
                item.get("booking_context", {})
            )
            
            total_base_price += pricing["base_price"]
            total_final_price += pricing["final_price"]
            all_discounts.extend(pricing["discount_opportunities"])
            all_upsells.extend(pricing["upsell_opportunities"])
        
        # Calculate bundle discounts
        bundle_discount = 0
        if len(items) > 2:
            bundle_discount = total_final_price * 0.05  # 5% bundle discount
            total_final_price -= bundle_discount
        
        return {
            "total_base_price": round(total_base_price),
            "total_final_price": round(total_final_price),
            "currency": "INR",
            "savings": round(total_base_price - total_final_price),
            "bundle_discount": round(bundle_discount),
            "payment_options": self._generate_payment_options(total_final_price, user_profile),
            "discount_opportunities": all_discounts[:3],  # Top 3 opportunities
            "upsell_opportunities": all_upsells[:2],      # Top 2 upsells
            "price_breakdown": await self._generate_price_breakdown(items, user_profile)
        }
    
    def _generate_payment_options(self, total_price: float, user_profile: dict) -> List[dict]:
        """Generate personalized payment options"""
        
        persona_classification = user_profile.get("persona_classification", {})
        primary_persona = persona_classification.get("primary_persona", "cultural_explorer")
        
        options = [
            {
                "type": "full_payment",
                "title": "Pay in Full",
                "amount": round(total_price),
                "benefits": ["No additional fees", "Immediate confirmation"],
                "recommended": total_price < 50000
            }
        ]
        
        # Add installment options for larger amounts
        if total_price > 20000:
            options.append({
                "type": "installments",
                "title": "Pay in 3 Installments",
                "initial_payment": round(total_price * 0.4),
                "remaining_payments": round(total_price * 0.3),
                "benefits": ["Easier budgeting", "Lock in current prices"],
                "recommended": primary_persona in ["budget_backpacker", "cultural_explorer"]
            })
        
        # Add travel insurance option
        insurance_cost = round(total_price * 0.03)  # 3% of trip cost
        options.append({
            "type": "insurance_addon",
            "title": "Travel Protection",
            "amount": insurance_cost,
            "benefits": ["Trip cancellation coverage", "Medical emergency protection"],
            "recommended": True
        })
        
        return options
    
    async def _generate_price_breakdown(self, items: List[dict], user_profile: dict) -> List[dict]:
        """Generate detailed price breakdown"""
        
        breakdown = []
        
        for item in items:
            pricing = await self.calculate_dynamic_pricing(
                item["service_type"], 
                item["details"], 
                user_profile, 
                item.get("booking_context", {})
            )
            
            breakdown.append({
                "item_name": item["details"].get("name", f"{item['service_type'].title()} Service"),
                "base_price": pricing["base_price"],
                "final_price": pricing["final_price"],
                "savings": round(pricing["base_price"] - pricing["final_price"]) if pricing["base_price"] > pricing["final_price"] else 0,
                "explanation": pricing["pricing_explanation"]
            })
        
        return breakdown