"""
External Booking Agent - Handles integration with third-party sightseeing providers 
via browser automation or API calls, normalized for swapping and pricing
"""

import logging
import os
from typing import Dict, List, Any, Optional
import httpx
import asyncio
from datetime import datetime, timezone
from models.schemas import ExternalBookingResponse, Activity
from utils.event_bus import EventBus, EventTypes
from utils.context_store import ContextStore
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class ExternalBookingAgent:
    """Agent responsible for external booking integrations and provider management"""
    
    def __init__(self, context_store: ContextStore, event_bus: EventBus):
        self.context_store = context_store
        self.event_bus = event_bus
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Provider configurations
        self.providers = {
            "viator": {
                "base_url": "https://api.viator.com/partner",
                "api_key": None,  # Would be configured in production
                "enabled": False
            },
            "getyourguide": {
                "base_url": "https://api.getyourguide.com/v1",
                "api_key": None,
                "enabled": False
            },
            "klook": {
                "base_url": "https://api.klook.com/v1",
                "api_key": None,
                "enabled": False
            },
            "local_partners": {
                "enabled": True,
                "providers": ["goa_adventures", "kerala_backwaters", "rajasthan_tours"]
            }
        }
        
        # Subscribe to booking events
        self.event_bus.subscribe(EventTypes.BOOKING_REQUESTED, self._handle_booking_request)
    
    def _get_llm_client(self, session_id: str) -> LlmChat:
        """Get LLM client for session"""
        return LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message="You are a travel booking assistant that generates realistic local travel partners and provider information."
        ).with_model("openai", "gpt-4o-mini")
    
    async def _handle_booking_request(self, event):
        """Handle booking request event"""
        try:
            session_id = event.session_id
            booking_data = event.data
            
            logger.info(f"🔗 Handling booking request for session {session_id}")
            
            result = await self.handle_booking(session_id, booking_data)
            
            await self.event_bus.emit(EventTypes.BOOKING_COMPLETED, {
                "booking_result": result,
                "activity_id": booking_data.get("activity_id")
            }, session_id)
            
        except Exception as e:
            logger.error(f"Booking request handling error: {e}")

    async def handle_booking(self, session_id: str, booking_details: Dict[str, Any]) -> ExternalBookingResponse:
        """Handle external booking process"""
        try:
            activity_id = booking_details.get("activity_id")
            activity_name = booking_details.get("activity_name", "Unknown Activity")
            provider_preference = booking_details.get("provider", "auto")
            travelers = booking_details.get("travelers", 2)
            travel_date = booking_details.get("travel_date", "")
            
            logger.info(f"🔗 Processing booking for {activity_name} (ID: {activity_id})")
            
            # Get available providers for this activity
            available_providers = await self._get_available_providers(activity_id, booking_details)
            
            if not available_providers:
                return ExternalBookingResponse(
                    booking_status="not_available",
                    booking_reference=None,
                    booking_url=None,
                    additional_info={"error": "No providers available for this activity"}
                )
            
            # Select best provider
            selected_provider = await self._select_best_provider(available_providers, booking_details)
            
            # Attempt booking
            booking_result = await self._attempt_booking(selected_provider, booking_details)
            
            # Store booking record
            self.context_store.add_booking(session_id, {
                "activity_id": activity_id,
                "activity_name": activity_name,
                "provider": selected_provider["name"],
                "booking_status": booking_result["status"],
                "booking_reference": booking_result.get("reference"),
                "booking_url": booking_result.get("url"),
                "travelers": travelers,
                "travel_date": travel_date,
                "cost": selected_provider.get("price", 0)
            })
            
            return ExternalBookingResponse(
                booking_status=booking_result["status"],
                booking_reference=booking_result.get("reference"),
                booking_url=booking_result.get("url"),
                additional_info=booking_result.get("additional_info", {})
            )
            
        except Exception as e:
            logger.error(f"Booking handling error: {e}")
            return ExternalBookingResponse(
                booking_status="error",
                booking_reference=None,
                booking_url=None,
                additional_info={"error": str(e)}
            )

    async def _get_available_providers(self, activity_id: str, booking_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available providers for an activity"""
        try:
            destination = booking_details.get("destination", "").lower()
            activity_type = booking_details.get("activity_type", "")
            
            providers = []
            
            # Check each provider
            for provider_name, config in self.providers.items():
                if not config.get("enabled", False):
                    continue
                
                if provider_name == "local_partners":
                    local_providers = await self._check_local_partners(destination, activity_type, booking_details)
                    providers.extend(local_providers)
                else:
                    provider_availability = await self._check_external_provider(provider_name, booking_details)
                    if provider_availability:
                        providers.append(provider_availability)
            
            return providers
            
        except Exception as e:
            logger.error(f"Provider check error: {e}")
            return []

    async def _check_local_partners(self, destination: str, activity_type: str, booking_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check local partner availability using LLM"""
        try:
            context = f"""
            Generate realistic local travel partners for {destination} that could handle {activity_type} activities.
            
            Destination: {destination}
            Activity Type: {activity_type}
            Booking Details: {booking_details}
            
            Generate 2-3 local partners with realistic details for this destination.
            Each partner should have:
            - name (realistic local business name)
            - contact (realistic Indian phone number format)
            - email (realistic business email)
            - 3-4 specialties relevant to the destination
            - rating (4.0-5.0)
            - response_time
            
            Respond in JSON array format:
            [
                {{
                    "name": "Business Name",
                    "contact": "+91-XXX-XXXX-XXXX",
                    "email": "contact@business.com",
                    "specialties": ["specialty1", "specialty2", "specialty3"],
                    "rating": 4.5,
                    "response_time": "immediate|1-2 hours|2-4 hours"
                }}
            ]
            """
            
            user_msg = UserMessage(text=context)
            llm_client = self._get_llm_client("temp_session")  # Use temp session for partner analysis
            response = await llm_client.send_message(user_msg)
            
            # Parse JSON response
            import json
            try:
                partners_data = json.loads(response)  # response is a string
                
                providers = []
                for partner in partners_data:
                    providers.append({
                        "name": f"Local Partner: {partner['name']}",
                        "type": "local_partner",
                        "contact_info": {
                            "phone": partner["contact"],
                            "email": partner["email"]
                        },
                        "rating": partner["rating"],
                        "response_time": partner["response_time"],
                        "booking_method": "direct_contact",
                        "price": await self._estimate_local_partner_price(activity_type, booking_details),
                        "availability": "high",
                        "specialties": partner["specialties"]
                    })
                
                return providers
                
            except json.JSONDecodeError:
                logger.error("Failed to parse local partners JSON, using fallback")
                return self._get_fallback_local_partners(destination)
            
        except Exception as e:
            logger.error(f"Local partner check error: {e}")
            return self._get_fallback_local_partners(destination)

    def _get_fallback_local_partners(self, destination: str) -> List[Dict[str, Any]]:
        """Fallback local partners if LLM fails"""
        return [
            {
                "name": f"Local Partner: {destination} Tours",
                "type": "local_partner",
                "contact_info": {
                    "phone": "+91-XXX-XXXX-XXXX",
                    "email": f"info@{destination.lower()}-tours.com"
                },
                "rating": 4.5,
                "response_time": "2-4 hours",
                "booking_method": "direct_contact",
                "price": 5000,
                "availability": "high",
                "specialties": ["sightseeing", "cultural", "adventure"]
            }
        ]

    async def _check_external_provider(self, provider_name: str, booking_details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check external provider availability"""
        try:
            config = self.providers.get(provider_name, {})
            
            if not config.get("api_key"):
                # Simulate provider availability without actual API calls
                return await self._simulate_provider_availability(provider_name, booking_details)
            
            # In production, would make actual API calls here
            # Example for Viator:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(
            #         f"{config['base_url']}/products/search",
            #         headers={"Authorization": f"Bearer {config['api_key']}"},
            #         params={"destination": booking_details.get("destination")}
            #     )
            #     return self._parse_provider_response(provider_name, response.json())
            
            return None
            
        except Exception as e:
            logger.error(f"External provider check error for {provider_name}: {e}")
            return None

    async def _simulate_provider_availability(self, provider_name: str, booking_details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Simulate provider availability for demo purposes"""
        try:
            # Mock availability data
            mock_data = {
                "viator": {
                    "available": True,
                    "rating": 4.4,
                    "response_time": "instant",
                    "booking_method": "api",
                    "commission": 0.12
                },
                "getyourguide": {
                    "available": True,
                    "rating": 4.3,
                    "response_time": "instant",
                    "booking_method": "api",
                    "commission": 0.15
                },
                "klook": {
                    "available": True,
                    "rating": 4.2,
                    "response_time": "instant",
                    "booking_method": "api",
                    "commission": 0.10
                }
            }
            
            provider_data = mock_data.get(provider_name)
            if not provider_data or not provider_data["available"]:
                return None
            
            return {
                "name": provider_name.title(),
                "type": "external_provider",
                "rating": provider_data["rating"],
                "response_time": provider_data["response_time"],
                "booking_method": provider_data["booking_method"],
                "price": await self._estimate_external_provider_price(provider_name, booking_details),
                "availability": "high",
                "commission": provider_data["commission"]
            }
            
        except Exception as e:
            logger.error(f"Provider simulation error: {e}")
            return None

    async def _select_best_provider(self, providers: List[Dict[str, Any]], booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best provider based on criteria"""
        try:
            if not providers:
                raise ValueError("No providers available")
            
            # Scoring criteria
            def score_provider(provider):
                score = 0
                
                # Rating weight (40%)
                score += provider.get("rating", 3.0) * 0.4
                
                # Price weight (30%) - lower price is better
                price = provider.get("price", 10000)
                max_price = max(p.get("price", 10000) for p in providers)
                if max_price > 0:
                    price_score = (max_price - price) / max_price * 5  # Convert to 0-5 scale
                    score += price_score * 0.3
                
                # Availability weight (20%)
                availability_scores = {"high": 5, "medium": 3, "low": 1}
                score += availability_scores.get(provider.get("availability", "medium"), 3) * 0.2
                
                # Response time weight (10%)
                response_scores = {"immediate": 5, "instant": 5, "1-2 hours": 4, "2-4 hours": 3, "4+ hours": 2}
                score += response_scores.get(provider.get("response_time", "2-4 hours"), 3) * 0.1
                
                return score
            
            # Score all providers
            scored_providers = [(provider, score_provider(provider)) for provider in providers]
            
            # Sort by score (highest first)
            scored_providers.sort(key=lambda x: x[1], reverse=True)
            
            best_provider = scored_providers[0][0]
            logger.info(f"Selected provider: {best_provider['name']} (score: {scored_providers[0][1]:.2f})")
            
            return best_provider
            
        except Exception as e:
            logger.error(f"Provider selection error: {e}")
            return providers[0] if providers else {}

    async def _attempt_booking(self, provider: Dict[str, Any], booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to make a booking with the selected provider"""
        try:
            provider_name = provider.get("name", "Unknown")
            booking_method = provider.get("booking_method", "direct_contact")
            
            if booking_method == "api":
                return await self._api_booking(provider, booking_details)
            elif booking_method == "direct_contact":
                return await self._direct_contact_booking(provider, booking_details)
            else:
                return {"status": "pending_manual", "message": "Manual booking required"}
                
        except Exception as e:
            logger.error(f"Booking attempt error: {e}")
            return {"status": "error", "message": str(e)}

    async def _api_booking(self, provider: Dict[str, Any], booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API-based bookings"""
        try:
            # Mock API booking - in production would make actual API calls
            
            # Simulate booking process
            await asyncio.sleep(0.5)  # Simulate API call delay
            
            # Generate mock booking reference
            import uuid
            booking_ref = f"{provider['name'].upper()[:3]}-{str(uuid.uuid4())[:8].upper()}"
            
            return {
                "status": "confirmed",
                "reference": booking_ref,
                "url": f"https://booking.{provider['name'].lower()}.com/confirm/{booking_ref}",
                "message": f"Booking confirmed with {provider['name']}",
                "additional_info": {
                    "confirmation_email": "sent",
                    "cancellation_policy": "Free cancellation up to 24 hours before the activity",
                    "contact_info": f"support@{provider['name'].lower()}.com"
                }
            }
            
        except Exception as e:
            logger.error(f"API booking error: {e}")
            return {"status": "error", "message": str(e)}

    async def _direct_contact_booking(self, provider: Dict[str, Any], booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct contact bookings"""
        try:
            contact_info = provider.get("contact_info", {})
            
            # Generate inquiry reference
            import uuid
            inquiry_ref = f"INQ-{str(uuid.uuid4())[:8].upper()}"
            
            # Simulate booking inquiry process
            booking_url = f"mailto:{contact_info.get('email', 'info@provider.com')}?subject=Booking Inquiry - {inquiry_ref}&body=Hello, I would like to book {booking_details.get('activity_name', 'an activity')} for {booking_details.get('travelers', 2)} people on {booking_details.get('travel_date', 'upcoming date')}. Reference: {inquiry_ref}"
            
            return {
                "status": "inquiry_sent",
                "reference": inquiry_ref,
                "url": booking_url,
                "message": f"Booking inquiry sent to {provider['name']}",
                "additional_info": {
                    "contact_phone": contact_info.get("phone", "Not available"),
                    "contact_email": contact_info.get("email", "Not available"),
                    "expected_response": provider.get("response_time", "2-4 hours"),
                    "next_steps": "The provider will contact you directly to confirm the booking"
                }
            }
            
        except Exception as e:
            logger.error(f"Direct contact booking error: {e}")
            return {"status": "error", "message": str(e)}

    async def _estimate_local_partner_price(self, activity_type: str, booking_details: Dict[str, Any]) -> float:
        """Estimate price for local partner activities"""
        try:
            base_prices = {
                "water_sports": 3500,
                "adventure": 4000,
                "sightseeing": 2500,
                "cultural": 2000,
                "heritage": 2500,
                "dining": 1500,
                "nature": 3000,
                "backwater_cruise": 5000,
                "luxury": 8000
            }
            
            travelers = booking_details.get("travelers", 2)
            base_price = base_prices.get(activity_type, 3000)
            
            # Apply group pricing
            if travelers > 4:
                base_price *= 0.9  # 10% group discount
            
            return base_price * travelers
            
        except Exception as e:
            logger.error(f"Local partner price estimation error: {e}")
            return 3000

    async def _estimate_external_provider_price(self, provider_name: str, booking_details: Dict[str, Any]) -> float:
        """Estimate price for external provider activities"""
        try:
            # Mock pricing - in production would get from actual APIs
            base_multipliers = {
                "viator": 1.2,      # 20% premium for international platform
                "getyourguide": 1.15, # 15% premium
                "klook": 1.1        # 10% premium
            }
            
            multiplier = base_multipliers.get(provider_name, 1.0)
            base_price = await self._estimate_local_partner_price(
                booking_details.get("activity_type", "sightseeing"), 
                booking_details
            )
            
            return base_price * multiplier
            
        except Exception as e:
            logger.error(f"External provider price estimation error: {e}")
            return 5000

    async def get_booking_status(self, session_id: str, booking_reference: str) -> Dict[str, Any]:
        """Get status of a booking"""
        try:
            bookings = self.context_store.get_bookings(session_id)
            
            for booking in bookings:
                if booking.get("booking_reference") == booking_reference:
                    # In production, would check actual status with provider
                    return {
                        "booking_reference": booking_reference,
                        "status": booking.get("booking_status", "unknown"),
                        "activity_name": booking.get("activity_name", "Unknown"),
                        "provider": booking.get("provider", "Unknown"),
                        "last_updated": booking.get("timestamp", ""),
                        "details": booking
                    }
            
            return {"error": f"Booking {booking_reference} not found"}
            
        except Exception as e:
            logger.error(f"Booking status check error: {e}")
            return {"error": str(e)}

    async def cancel_booking(self, session_id: str, booking_reference: str) -> Dict[str, Any]:
        """Cancel a booking"""
        try:
            bookings = self.context_store.get_bookings(session_id)
            
            for booking in bookings:
                if booking.get("booking_reference") == booking_reference:
                    # In production, would make actual cancellation API call
                    
                    # Update booking status
                    booking["booking_status"] = "cancelled"
                    booking["cancelled_at"] = datetime.now(timezone.utc).isoformat()
                    
                    return {
                        "status": "cancelled",
                        "booking_reference": booking_reference,
                        "cancellation_fee": 0,  # Mock - would calculate actual fee
                        "refund_amount": booking.get("cost", 0),
                        "refund_timeline": "3-5 business days"
                    }
            
            return {"error": f"Booking {booking_reference} not found"}
            
        except Exception as e:
            logger.error(f"Booking cancellation error: {e}")
            return {"error": str(e)}

    def get_provider_statistics(self) -> Dict[str, Any]:
        """Get provider performance statistics"""
        try:
            # Mock statistics - in production would aggregate from actual booking data
            return {
                "total_providers": len([p for p in self.providers.values() if p.get("enabled", False)]),
                "provider_performance": {
                    "local_partners": {
                        "success_rate": 0.95,
                        "average_response_time": "2 hours",
                        "customer_satisfaction": 4.6
                    },
                    "viator": {
                        "success_rate": 0.98,
                        "average_response_time": "instant",
                        "customer_satisfaction": 4.4
                    },
                    "getyourguide": {
                        "success_rate": 0.97,
                        "average_response_time": "instant", 
                        "customer_satisfaction": 4.3
                    }
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Provider statistics error: {e}")
            return {"error": str(e)}