"""
Slot Agent - Extracts canonical destination and primary intent from user message
"""
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class SlotAgent:
    """
    Extracts canonical destination and primary intent from user message.
    Normalizes place names and attempts canonical_place_id lookup.
    If ambiguous, returns a clarification question.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.known_destinations = {
            'rishikesh': {'canonical_place_id': 'rishikesh_uttarakhand', 'full_name': 'Rishikesh, Uttarakhand', 'country': 'India'},
            'manali': {'canonical_place_id': 'manali_himachal', 'full_name': 'Manali, Himachal Pradesh', 'country': 'India'},
            'andaman': {'canonical_place_id': 'andaman_islands', 'full_name': 'Andaman Islands', 'country': 'India'},
            'andaman islands': {'canonical_place_id': 'andaman_islands', 'full_name': 'Andaman Islands', 'country': 'India'},
            'havelock': {'canonical_place_id': 'andaman_islands', 'full_name': 'Andaman Islands', 'country': 'India'},
            'kerala': {'canonical_place_id': 'kerala_backwaters', 'full_name': 'Kerala, India', 'country': 'India'},
            'rajasthan': {'canonical_place_id': 'rajasthan_india', 'full_name': 'Rajasthan, India', 'country': 'India'},
            'pondicherry': {'canonical_place_id': 'pondicherry_india', 'full_name': 'Pondicherry, India', 'country': 'India'},
            'puducherry': {'canonical_place_id': 'pondicherry_india', 'full_name': 'Pondicherry, India', 'country': 'India'},
            'goa': {'canonical_place_id': 'goa_india', 'full_name': 'Goa, India', 'country': 'India'},
            'kashmir': {'canonical_place_id': 'kashmir_india', 'full_name': 'Kashmir, India', 'country': 'India'},
            'ladakh': {'canonical_place_id': 'ladakh_india', 'full_name': 'Ladakh, India', 'country': 'India'},
            'himachal': {'canonical_place_id': 'manali_himachal', 'full_name': 'Manali, Himachal Pradesh', 'country': 'India'},
            'uttarakhand': {'canonical_place_id': 'rishikesh_uttarakhand', 'full_name': 'Rishikesh, Uttarakhand', 'country': 'India'}
        }
        
        # Intent keywords mapping
        self.intent_patterns = {
            'plan': ['plan', 'generate', 'itinerary', 'trip', 'schedule', 'create itinerary', 'make plan'],
            'accommodation': ['hotel', 'stay', 'accommodation', 'book', 'reserve', 'resort', 'lodge'],
            'find': ['find', 'recommend', 'suggest', 'show', 'tell me about', 'what about', 'explore', 'recommendations', 'popular destinations', 'give me'],
            'confirmation': ['yes', 'okay', 'ok', 'sure', 'proceed', 'continue', 'that works', 'sounds good', 'perfect'],
            'general': ['hello', 'hi', 'help', 'what can you do', 'hey', 'good morning', 'good evening']
        }
    
    async def extract_intent_and_destination(self, message: str) -> Dict[str, Any]:
        """
        Extract canonical destination and primary intent from user message.
        
        Returns: {
            "destination_name": str|None,
            "canonical_place_id": str|None, 
            "intent": str,  # 'plan', 'accommodation', 'find', 'general'
            "confidence": float,  # 0-1 confidence score
            "clarify": str|None  # Clarification question if ambiguous
        }
        """
        try:
            message_lower = message.lower().strip()
            
            # Step 1: Detect primary intent
            intent = self._detect_intent(message_lower)
            
            # Step 2: Extract destination
            destination_result = await self._extract_destination(message_lower)
            
            # Step 3: Check for ambiguity and need for clarification
            clarify = None
            confidence = 0.9
            
            if destination_result['needs_clarification']:
                clarify = destination_result['clarification_question']
                confidence = 0.3
            elif destination_result['destination_name'] is None and intent in ['accommodation']:
                # Only ask for clarification for accommodation queries, not for general plan/find intent
                clarify = "Which destination would you like to explore?"
                confidence = 0.5
            elif destination_result['destination_name'] is None and intent == 'plan':
                # For general planning ("plan a trip"), let the planner flow handle destination selection
                confidence = 0.8
            elif intent == 'general' and destination_result['destination_name'] is None:
                confidence = 0.8  # General queries don't need destinations
            
            return {
                "destination_name": destination_result['destination_name'],
                "canonical_place_id": destination_result['canonical_place_id'],
                "intent": intent,
                "confidence": confidence,
                "clarify": clarify
            }
            
        except Exception as e:
            print(f"❌ SlotAgent error: {e}")
            return {
                "destination_name": None,
                "canonical_place_id": None,
                "intent": "general",
                "confidence": 0.1,
                "clarify": "I'm having trouble understanding. Could you please rephrase your request?"
            }
    
    def _detect_intent(self, message_lower: str) -> str:
        """Detect primary intent from message"""
        
        # Check for explicit intent keywords
        for intent, keywords in self.intent_patterns.items():
            for keyword in keywords:
                if keyword in message_lower:
                    if intent == 'plan' and any(word in message_lower for word in ['plan', 'itinerary', 'generate', 'create']):
                        return 'plan'
                    elif intent == 'accommodation' and any(word in message_lower for word in ['hotel', 'stay', 'book', 'accommodation']):
                        return 'accommodation'
                    elif intent == 'find' and any(word in message_lower for word in ['tell me about', 'recommend', 'suggest', 'find']):
                        return 'find'
                    elif intent == 'general':
                        return 'general'
        
        # Contextual intent detection
        if any(word in message_lower for word in ['plan', 'trip', 'itinerary', 'generate', 'create plan']):
            return 'plan'
        elif any(word in message_lower for word in ['hotel', 'accommodation', 'stay', 'book', 'reserve']):
            return 'accommodation'
        elif any(word in message_lower for word in ['recommend', 'recommendations', 'suggest', 'show me', 'popular', 'give me', 'tell me about', 'about', 'what', 'find', 'destinations', 'beach destinations', 'mountain destinations']):
            return 'find'
        else:
            return 'general'
    
    async def _extract_destination(self, message_lower: str) -> Dict[str, Any]:
        """Extract and normalize destination from message"""
        
        # Step 1: Direct matching for known destinations
        for key, data in self.known_destinations.items():
            if key in message_lower:
                return {
                    "destination_name": data['full_name'],
                    "canonical_place_id": data['canonical_place_id'],
                    "needs_clarification": False,
                    "clarification_question": None
                }
        
        # Step 2: Handle ambiguous cases
        ambiguous_cases = {
            'paris': "Do you mean Paris, France or Paris, Texas?",
            'spring': "Do you mean Spring, Texas or spring season travel?",
            'london': "Do you mean London, UK or London, Ontario?"
        }
        
        for ambiguous_place, question in ambiguous_cases.items():
            if ambiguous_place in message_lower:
                return {
                    "destination_name": None,
                    "canonical_place_id": None,
                    "needs_clarification": True,
                    "clarification_question": question
                }
        
        # Step 3: Skip LLM for general recommendation queries and general planning  
        if any(word in message_lower for word in ['recommend', 'recommendations', 'suggest', 'popular', 'give me', 'plan a trip', 'plan trip']):
            return {
                "destination_name": None,
                "canonical_place_id": None,
                "needs_clarification": False,
                "clarification_question": None
            }
        
        # Step 4: Use LLM for complex extraction (only if not a general query)
        llm_result = await self._llm_extract_destination(message_lower)
        if llm_result:
            return llm_result
        
        # Step 5: No destination found
        return {
            "destination_name": None,
            "canonical_place_id": None,
            "needs_clarification": False,
            "clarification_question": None
        }
    
    async def _llm_extract_destination(self, message: str) -> Optional[Dict[str, Any]]:
        """Use LLM for complex destination extraction"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Create LLM client for destination extraction
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"slot_destination_{hash(message) % 1000}",
                system_message="You are a travel destination expert. Extract destination information from user messages with focus on Indian destinations."
            ).with_model("openai", "gpt-4o-mini")
            
            # Enhanced prompt for destination extraction
            prompt = f"""
Extract destination from this travel message: "{message}"

Known Indian destinations: Rishikesh, Manali, Andaman Islands, Kerala, Rajasthan, Pondicherry, Goa, Kashmir, Ladakh

Output JSON only:
{{
  "destination_name": "Full destination name or null",
  "canonical_place_id": "normalized_id or null", 
  "needs_clarification": true/false,
  "clarification_question": "Question if ambiguous or null"
}}

Rules:
- If clear Indian destination found, provide full name (e.g., "Kerala, India")
- If ambiguous destination, set needs_clarification=true with question
- If no destination mentioned, return nulls
- Prefer Indian destinations when possible
"""
            
            user_message = UserMessage(text=prompt)
            response = await llm_client.send_message(user_message)
            
            # Handle response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            result = json.loads(content)
            print(f"✅ LLM destination extraction: {result}")
            return result
            
        except Exception as e:
            print(f"❌ LLM destination extraction error: {e}")
            return None
    
    def normalize_place_name(self, place_name: str) -> Dict[str, Any]:
        """
        Normalize place name to canonical format
        Returns: {"canonical_place_id": str, "full_name": str, "country": str}
        """
        if not place_name:
            return {"canonical_place_id": None, "full_name": None, "country": None}
        
        place_lower = place_name.lower()
        
        # Check known destinations
        for key, data in self.known_destinations.items():
            if key in place_lower or place_lower in data['full_name'].lower():
                return {
                    "canonical_place_id": data['canonical_place_id'],
                    "full_name": data['full_name'],
                    "country": data['country']
                }
        
        # Default normalization
        return {
            "canonical_place_id": place_name.lower().replace(' ', '_').replace(',', ''),
            "full_name": place_name.title(),
            "country": "Unknown"
        }


# Keep existing agents for backward compatibility
class DestinationAgent:
    """Handles destination extraction and validation"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.known_destinations = {
            'rishikesh': {'canonical_place_id': 'rishikesh_india', 'full_name': 'Rishikesh, Uttarakhand'},
            'manali': {'canonical_place_id': 'manali_india', 'full_name': 'Manali, Himachal Pradesh'},
            'andaman': {'canonical_place_id': 'andaman_islands', 'full_name': 'Andaman Islands'},
            'andaman islands': {'canonical_place_id': 'andaman_islands', 'full_name': 'Andaman Islands'},
            'kerala': {'canonical_place_id': 'kerala_india', 'full_name': 'Kerala, India'},
            'rajasthan': {'canonical_place_id': 'rajasthan_india', 'full_name': 'Rajasthan, India'},
            'pondicherry': {'canonical_place_id': 'pondicherry_india', 'full_name': 'Pondicherry, India'},
            'puducherry': {'canonical_place_id': 'pondicherry_india', 'full_name': 'Pondicherry, India'},
            'goa': {'canonical_place_id': 'goa_india', 'full_name': 'Goa, India'},
            'kashmir': {'canonical_place_id': 'kashmir_india', 'full_name': 'Kashmir, India'},
            'ladakh': {'canonical_place_id': 'ladakh_india', 'full_name': 'Ladakh, India'},
            'himachal': {'canonical_place_id': 'manali_india', 'full_name': 'Manali, Himachal Pradesh'},
            'uttarakhand': {'canonical_place_id': 'rishikesh_india', 'full_name': 'Rishikesh, Uttarakhand'}
        }
    
    async def extract_destination(self, message: str) -> Dict[str, Any]:
        """
        Extract a canonical destination from the user's message
        Returns: {"destination_name": str, "canonical_place_id": str|None, "intent": str, "clarify": str|None}
        """
        message_lower = message.lower()
        
        # Direct matching for known destinations
        for key, data in self.known_destinations.items():
            if key in message_lower:
                return {
                    "destination_name": data['full_name'],
                    "canonical_place_id": data['canonical_place_id'],
                    "intent": "set",
                    "clarify": None
                }
        
        # Handle ambiguous cases
        if 'paris' in message_lower:
            return {
                "destination_name": None,
                "canonical_place_id": None,
                "intent": "confirm",
                "clarify": "Do you mean Paris, France or Paris, Texas?"
            }
        
        if 'spring' in message_lower:
            return {
                "destination_name": None,
                "canonical_place_id": None,
                "intent": "confirm", 
                "clarify": "Do you mean Spring, Texas or spring season in a location?"
            }
        
        # Use LLM for complex destination extraction
        prompt = f"""
        Task: Extract a canonical "destination" from the user's message.
        User message: "{message}"
        
        Output JSON only: {{"destination_name": string, "canonical_place_id": string|null, "intent": "set"|"edit"|"confirm", "clarify": string|null}}
        
        Rules:
        - If clear destination provided, set destination_name and intent="set"
        - If ambiguous, set clarify with short question
        - Focus on Indian destinations when possible
        """
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import os
            
            # Create a new LLM client
            llm_client = LlmChat(
                api_key=os.environ.get('EMERGENT_LLM_KEY'),
                session_id=f"destination_{hash(message) % 1000}",
                system_message="You are a travel destination expert. Extract destination information from user messages."
            ).with_model("openai", "gpt-4o-mini")
            
            user_message = UserMessage(text=prompt)
            response = await llm_client.send_message(user_message)
            
            # Handle different response types
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
                
            result = json.loads(content)
            return result
        except Exception as e:
            print(f"Destination extraction LLM error: {e}")
            return {
                "destination_name": None,
                "canonical_place_id": None,
                "intent": "confirm",
                "clarify": "Could you please specify which destination you'd like to visit?"
            }

class DatesAgent:
    """Handles date parsing and validation"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def extract_dates(self, message: str) -> Dict[str, Any]:
        """
        Parse date(s) from user message and return ISO dates
        Returns: {"start_date": "YYYY-MM-DD"|None, "end_date": "YYYY-MM-DD"|None, "date_type": str, "clarify": str|None}
        """
        message_lower = message.lower()
        
        # Quick patterns for common date formats
        if 'this weekend' in message_lower:
            today = datetime.now()
            days_ahead = 5 - today.weekday()  # Saturday
            if days_ahead <= 0:
                days_ahead += 7
            start_date = today + timedelta(days=days_ahead)
            end_date = start_date + timedelta(days=1)
            return {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "date_type": "fixed",
                "clarify": None
            }
        
        if 'next month' in message_lower:
            today = datetime.now()
            next_month = today.replace(month=today.month + 1 if today.month < 12 else 1,
                                     year=today.year if today.month < 12 else today.year + 1,
                                     day=1)
            return {
                "start_date": None,
                "end_date": None,
                "date_type": "flexible",
                "clarify": f"When in {next_month.strftime('%B %Y')} would you prefer to travel?"
            }
        
        # Look for specific date patterns
        date_patterns = [
            r'(december|december|dec)\s+(\d{1,2})[- ]?[-–—]\s?(\d{1,2})',  # December 15-20
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})[- ]?[-–—]\s?(\d{1,2})',  # Month DD-DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',  # Month DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if matches:
                try:
                    match = matches[0]
                    if len(match) == 3 and isinstance(match[1], str) and isinstance(match[2], str):
                        # Handle month range like "December 15-20"
                        month_name = match[0].lower()
                        start_day = int(match[1])
                        end_day = int(match[2])
                        
                        # Map month names to numbers
                        months = {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4,
                            'may': 5, 'june': 6, 'july': 7, 'august': 8,
                            'september': 9, 'october': 10, 'november': 11, 'december': 12,
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        if month_name in months:
                            current_year = datetime.now().year
                            month_num = months[month_name]
                            
                            # If the month has passed this year, assume next year
                            if month_num < datetime.now().month:
                                current_year += 1
                            
                            start_date = datetime(current_year, month_num, start_day)
                            end_date = datetime(current_year, month_num, end_day)
                            
                            return {
                                "start_date": start_date.strftime("%Y-%m-%d"),
                                "end_date": end_date.strftime("%Y-%m-%d"),
                                "date_type": "fixed",
                                "clarify": None
                            }
                    
                    # For other patterns, use basic logic
                    today = datetime.now()
                    return {
                        "start_date": today.strftime("%Y-%m-%d"),
                        "end_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                        "date_type": "fixed",
                        "clarify": None
                    }
                except Exception as e:
                    print(f"Date parsing error: {e}")
                    pass
        
        # Default case - ask for clarification
        return {
            "start_date": None,
            "end_date": None,
            "date_type": "unknown",
            "clarify": "When would you like to travel? Please share your preferred dates."
        }

class TravelersAgent:
    """Handles traveler count extraction"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def extract_travelers(self, message: str) -> Dict[str, Any]:
        """
        Extract traveler counts and types
        Returns: {"adults": int, "children": int, "infants": int, "rooms": int, "clarify": str|None}
        """
        message_lower = message.lower()
        
        adults = 2  # Default
        children = 0
        infants = 0
        
        # Pattern matching for numbers
        adult_patterns = [
            r'(\d+)\s+adults?',
            r'(\d+)\s+people',
            r'(\d+)\s+travelers?',
            r'group of (\d+)',
            r'(\d+)\s+of us'
        ]
        
        child_patterns = [
            r'(\d+)\s+child(?:ren)?',
            r'(\d+)\s+kids?',
            r'(\d+)\s+minors?'
        ]
        
        # Extract adults
        for pattern in adult_patterns:
            match = re.search(pattern, message_lower)
            if match:
                adults = int(match.group(1))
                break
        
        # Extract children
        for pattern in child_patterns:
            match = re.search(pattern, message_lower)
            if match:
                children = int(match.group(1))
                break
        
        # Special cases
        if 'solo' in message_lower or 'alone' in message_lower:
            adults = 1
        elif 'couple' in message_lower:
            adults = 2
        elif 'family' in message_lower and children == 0:
            children = 2  # Assume 2 children if family mentioned but no specific number
        
        # Calculate rooms
        total_people = adults + children
        rooms = max(1, (total_people + 1) // 2)  # Rough estimate
        
        # Check if clarification needed
        if 'travel' in message_lower and adults == 2 and children == 0:
            return {
                "adults": adults,
                "children": children,
                "infants": infants,
                "rooms": rooms,
                "clarify": f"{adults} adults and {children} children — would you like {rooms} room or different arrangement?"
            }
        
        return {
            "adults": adults,
            "children": children,
            "infants": infants,
            "rooms": rooms,
            "clarify": None
        }

class BudgetAgent:
    """Handles budget extraction and normalization"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def extract_budget(self, message: str) -> Dict[str, Any]:
        """
        Parse budget input and normalize to per-night or total budget
        Returns: {"currency": str, "budget_total": float|None, "budget_per_night": float|None, "budget_type": str, "clarify": str|None}
        """
        message_lower = message.lower()
        
        # Currency detection
        currency = "INR"  # Default for Indian destinations
        if '$' in message or 'usd' in message_lower or 'dollar' in message_lower:
            currency = "USD"
        elif '€' in message or 'eur' in message_lower or 'euro' in message_lower:
            currency = "EUR"
        elif '₹' in message or 'inr' in message_lower or 'rupee' in message_lower:
            currency = "INR"
        
        # Budget range patterns
        budget_patterns = [
            r'[₹$€]?(\d+(?:,\d{3})*(?:\.\d{2})?)[^\d]*per night',
            r'[₹$€]?(\d+(?:,\d{3})*(?:\.\d{2})?)[^\d]*(?:per|/) night',
            r'[₹$€]?(\d+(?:,\d{3})*(?:\.\d{2})?)[^\d]*night',
            r'budget[:\s]+[₹$€]?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'[₹$€](\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        budget_per_night = None
        budget_total = None
        
        # Per night budget
        for pattern in budget_patterns[:3]:
            match = re.search(pattern, message_lower)
            if match:
                budget_per_night = float(match.group(1).replace(',', ''))
                break
        
        # Total budget
        if not budget_per_night:
            for pattern in budget_patterns[3:]:
                match = re.search(pattern, message_lower)
                if match:
                    amount = float(match.group(1).replace(',', ''))
                    if 'total' in message_lower or 'entire' in message_lower:
                        budget_total = amount
                    else:
                        budget_per_night = amount
                    break
        
        # Budget categories
        if 'budget' in message_lower or 'cheap' in message_lower or 'affordable' in message_lower:
            if currency == "INR":
                budget_per_night = budget_per_night or 2000  # Budget range in INR
            else:
                budget_per_night = budget_per_night or 50  # Budget range in USD
        
        elif 'mid-range' in message_lower or 'moderate' in message_lower:
            if currency == "INR":
                budget_per_night = budget_per_night or 5000  # Mid-range in INR
            else:
                budget_per_night = budget_per_night or 120  # Mid-range in USD
        
        elif 'luxury' in message_lower or 'premium' in message_lower or 'high-end' in message_lower:
            if currency == "INR":
                budget_per_night = budget_per_night or 10000  # Luxury in INR
            else:
                budget_per_night = budget_per_night or 250  # Luxury in USD
        
        # Determine budget type
        budget_type = "per_night" if budget_per_night else ("total" if budget_total else "unknown")
        
        return {
            "currency": currency,
            "budget_total": budget_total,
            "budget_per_night": budget_per_night,
            "budget_type": budget_type,
            "clarify": None if budget_per_night or budget_total else "What's your preferred budget range per night?"
        }