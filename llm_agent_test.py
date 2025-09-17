import requests
import sys
import json
from datetime import datetime
import time

class LLMAgentTester:
    def __init__(self, base_url="https://ai-trip-planner-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"llm_test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}...")

            return success, response.json() if success and response.content else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_chat_api_with_specific_messages(self):
        """Test the /api/chat endpoint with specific messages from review request"""
        print(f"\n🎯 Testing Chat API with Review Request Messages...")
        
        test_messages = [
            {
                "message": "tell me about kerala",
                "expected_cards": "destination",
                "description": "Should generate destination cards"
            },
            {
                "message": "plan a trip to manali", 
                "expected_cards": "mixed",
                "description": "Should trigger trip planning flow"
            },
            {
                "message": "i want accommodations in goa",
                "expected_cards": "hotel",
                "description": "Should generate hotel cards only"
            }
        ]
        
        chat_tests_passed = 0
        for i, test_case in enumerate(test_messages):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_chat_{i}",
                "user_profile": {},
                "trip_details": {}
            }
            
            success, response = self.run_test(f"Chat Message {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                # Analyze response structure
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                print(f"      Chat text length: {len(chat_text)} characters")
                print(f"      UI actions generated: {len(ui_actions)}")
                
                # Analyze card types
                destination_cards = [a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'destination']
                hotel_cards = [a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'hotel']
                question_chips = [a for a in ui_actions if a.get('type') == 'question_chip']
                
                print(f"      Destination cards: {len(destination_cards)}")
                print(f"      Hotel cards: {len(hotel_cards)}")
                print(f"      Question chips: {len(question_chips)}")
                
                # Verify expected card types
                test_passed = False
                if test_case["expected_cards"] == "destination" and len(destination_cards) > 0:
                    test_passed = True
                    print(f"      ✅ Correctly generated destination cards")
                elif test_case["expected_cards"] == "hotel" and len(hotel_cards) > 0 and len(destination_cards) == 0:
                    test_passed = True
                    print(f"      ✅ Correctly generated ONLY hotel cards")
                elif test_case["expected_cards"] == "mixed" and (len(destination_cards) > 0 or len(hotel_cards) > 0):
                    test_passed = True
                    print(f"      ✅ Generated appropriate cards for trip planning")
                
                if test_passed:
                    chat_tests_passed += 1
                else:
                    print(f"      ❌ Card generation doesn't match expected type: {test_case['expected_cards']}")
                    
                # Check for intelligent response content
                if len(chat_text) > 50 and any(keyword in chat_text.lower() for keyword in test_case["message"].lower().split()):
                    print(f"      ✅ Response appears contextual and intelligent")
                else:
                    print(f"      ⚠️  Response may not be contextual enough")
        
        print(f"\n🎯 Chat API Tests: {chat_tests_passed}/{len(test_messages)} passed")
        return chat_tests_passed == len(test_messages)

    def test_multi_agent_system(self):
        """Test Multi-Agent System components"""
        print(f"\n🤖 Testing Multi-Agent System Components...")
        
        # Test ConversationManager routing
        print(f"\n   Testing ConversationManager routing...")
        
        routing_tests = [
            {
                "message": "I want to visit Kerala for backwaters",
                "expected_agents": ["ConversationManager", "SlotAgent"],
                "description": "Destination extraction test"
            },
            {
                "message": "Plan a 5-day trip to Manali with budget of 20000",
                "expected_agents": ["ConversationManager", "PlannerAgent"],
                "description": "Trip planning with details"
            },
            {
                "message": "Show me luxury hotels in Andaman",
                "expected_agents": ["ConversationManager", "AccommodationAgent"],
                "description": "Accommodation request"
            }
        ]
        
        agent_tests_passed = 0
        for i, test_case in enumerate(routing_tests):
            print(f"\n      Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_agent_{i}",
                "user_profile": {},
                "trip_details": {}
            }
            
            success, response = self.run_test(f"Agent Routing {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Check if response indicates intelligent agent processing
                intelligent_indicators = [
                    len(chat_text) > 100,  # Substantial response
                    len(ui_actions) > 0,   # Generated UI actions
                    any(keyword in chat_text.lower() for keyword in test_case["message"].lower().split()[:3])  # Contextual
                ]
                
                if sum(intelligent_indicators) >= 2:
                    agent_tests_passed += 1
                    print(f"         ✅ Agent system appears to be working intelligently")
                    print(f"         Response length: {len(chat_text)}")
                    print(f"         UI actions: {len(ui_actions)}")
                else:
                    print(f"         ❌ Agent system may not be working properly")
                    print(f"         Response: {chat_text[:100]}...")
        
        print(f"\n🤖 Multi-Agent System: {agent_tests_passed}/{len(routing_tests)} tests passed")
        return agent_tests_passed >= 2  # Pass if at least 2/3 work

    def test_slot_agents_extraction(self):
        """Test SlotAgents for extracting destinations, dates, budget, travelers"""
        print(f"\n🎰 Testing Slot Agents Extraction...")
        
        slot_tests = [
            {
                "message": "I want to visit Rishikesh next month with my family of 4 people, budget around 50000",
                "expected_slots": {
                    "destination": "rishikesh",
                    "travelers": "4",
                    "budget": "50000"
                },
                "description": "Complete slot extraction"
            },
            {
                "message": "Plan a trip to Goa from December 15 to December 20",
                "expected_slots": {
                    "destination": "goa",
                    "dates": "december"
                },
                "description": "Destination and dates extraction"
            },
            {
                "message": "Show me budget accommodations in Kerala for 2 adults",
                "expected_slots": {
                    "destination": "kerala",
                    "travelers": "2",
                    "budget": "budget"
                },
                "description": "Destination, travelers, and budget preference"
            }
        ]
        
        slot_tests_passed = 0
        for i, test_case in enumerate(slot_tests):
            print(f"\n   Testing: {test_case['description']}")
            
            # Create trip_details to simulate slot filling
            trip_details = {
                "destination": None,
                "dates": {"start_date": None, "end_date": None},
                "travelers": {"adults": 2, "children": 0},
                "budget": {"per_night": None}
            }
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_slot_{i}",
                "user_profile": {},
                "trip_details": trip_details
            }
            
            success, response = self.run_test(f"Slot Extraction {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '').lower()
                
                # Check if response acknowledges the extracted information
                slot_matches = 0
                for slot_key, expected_value in test_case["expected_slots"].items():
                    if expected_value.lower() in chat_text:
                        slot_matches += 1
                        print(f"      ✅ {slot_key}: '{expected_value}' acknowledged in response")
                    else:
                        print(f"      ⚠️  {slot_key}: '{expected_value}' not clearly acknowledged")
                
                if slot_matches >= len(test_case["expected_slots"]) // 2:  # At least half the slots
                    slot_tests_passed += 1
                    print(f"      ✅ Slot extraction appears to be working")
                else:
                    print(f"      ❌ Slot extraction may not be working properly")
        
        print(f"\n🎰 Slot Agents: {slot_tests_passed}/{len(slot_tests)} tests passed")
        return slot_tests_passed >= 2

    def test_planner_agent_itineraries(self):
        """Test PlannerAgent for generating real itineraries (not mocked data)"""
        print(f"\n📅 Testing PlannerAgent Itinerary Generation...")
        
        itinerary_tests = [
            {
                "message": "Create a 3-day itinerary for Manali with adventure activities",
                "trip_details": {
                    "destination": "Manali",
                    "dates": {"start_date": "2024-12-15", "end_date": "2024-12-18"},
                    "travelers": {"adults": 2, "children": 0},
                    "budget": {"per_night": 5000}
                },
                "expected_elements": ["day 1", "day 2", "day 3", "manali", "adventure"],
                "description": "3-day Manali adventure itinerary"
            },
            {
                "message": "Plan a 5-day Kerala backwaters experience",
                "trip_details": {
                    "destination": "Kerala",
                    "dates": {"start_date": "2024-12-20", "end_date": "2024-12-25"},
                    "travelers": {"adults": 2, "children": 1},
                    "budget": {"per_night": 8000}
                },
                "expected_elements": ["day", "kerala", "backwaters", "houseboat", "alleppey"],
                "description": "5-day Kerala backwaters itinerary"
            }
        ]
        
        planner_tests_passed = 0
        for i, test_case in enumerate(itinerary_tests):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_planner_{i}",
                "user_profile": {},
                "trip_details": test_case["trip_details"]
            }
            
            success, response = self.run_test(f"Planner Agent {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '').lower()
                
                # Check for itinerary elements
                element_matches = 0
                for element in test_case["expected_elements"]:
                    if element.lower() in chat_text:
                        element_matches += 1
                        print(f"      ✅ Found itinerary element: '{element}'")
                    else:
                        print(f"      ⚠️  Missing element: '{element}'")
                
                # Check for detailed itinerary structure
                has_detailed_structure = any(indicator in chat_text for indicator in [
                    "day 1", "day 2", "morning", "afternoon", "evening", "₹", "price", "activity"
                ])
                
                # Check response length (detailed itineraries should be substantial)
                is_substantial = len(chat_text) > 300
                
                if element_matches >= 3 and has_detailed_structure and is_substantial:
                    planner_tests_passed += 1
                    print(f"      ✅ Generated detailed itinerary ({len(chat_text)} chars)")
                    print(f"      ✅ Contains structured daily plans")
                else:
                    print(f"      ❌ Itinerary may be too basic or mocked")
                    print(f"         Elements found: {element_matches}/{len(test_case['expected_elements'])}")
                    print(f"         Has structure: {has_detailed_structure}")
                    print(f"         Length: {len(chat_text)} chars")
        
        print(f"\n📅 PlannerAgent: {planner_tests_passed}/{len(itinerary_tests)} tests passed")
        return planner_tests_passed >= 1

    def test_accommodation_agent(self):
        """Test AccommodationAgent for generating hotel recommendations"""
        print(f"\n🏨 Testing AccommodationAgent Hotel Recommendations...")
        
        accommodation_tests = [
            {
                "message": "Find me luxury hotels in Andaman Islands",
                "expected_hotels": ["taj", "barefoot", "luxury", "havelock"],
                "description": "Luxury Andaman hotels"
            },
            {
                "message": "Show budget accommodations in Rishikesh",
                "expected_hotels": ["camp", "budget", "rishikesh", "ganga"],
                "description": "Budget Rishikesh accommodations"
            },
            {
                "message": "I need family-friendly hotels in Kerala",
                "expected_hotels": ["kerala", "family", "kumarakom", "backwater"],
                "description": "Family Kerala hotels"
            }
        ]
        
        accommodation_tests_passed = 0
        for i, test_case in enumerate(accommodation_tests):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_accommodation_{i}",
                "user_profile": {},
                "trip_details": {}
            }
            
            success, response = self.run_test(f"Accommodation Agent {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '').lower()
                ui_actions = response.get('ui_actions', [])
                
                # Check for hotel cards
                hotel_cards = [a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'hotel']
                
                # Check for expected hotel keywords in response
                hotel_matches = sum(1 for hotel in test_case["expected_hotels"] if hotel.lower() in chat_text)
                
                # Verify hotel card details
                valid_hotel_cards = 0
                for hotel_card in hotel_cards:
                    payload = hotel_card.get('payload', {})
                    required_fields = ['title', 'rating', 'price_estimate', 'amenities']
                    if all(field in payload for field in required_fields):
                        valid_hotel_cards += 1
                        print(f"      ✅ Valid hotel card: {payload.get('title', 'N/A')}")
                        print(f"         Rating: {payload.get('rating', 'N/A')}")
                        price_range = payload.get('price_estimate', {})
                        if price_range:
                            print(f"         Price: ₹{price_range.get('min', 'N/A')}-{price_range.get('max', 'N/A')}/night")
                
                if hotel_matches >= 2 and valid_hotel_cards > 0:
                    accommodation_tests_passed += 1
                    print(f"      ✅ AccommodationAgent working correctly")
                    print(f"         Hotel keywords found: {hotel_matches}/{len(test_case['expected_hotels'])}")
                    print(f"         Valid hotel cards: {valid_hotel_cards}")
                else:
                    print(f"      ❌ AccommodationAgent may not be working properly")
                    print(f"         Hotel keywords: {hotel_matches}/{len(test_case['expected_hotels'])}")
                    print(f"         Hotel cards: {len(hotel_cards)} ({valid_hotel_cards} valid)")
        
        print(f"\n🏨 AccommodationAgent: {accommodation_tests_passed}/{len(accommodation_tests)} tests passed")
        return accommodation_tests_passed >= 2

    def test_ui_actions_generation(self):
        """Test UI actions generation for different categories"""
        print(f"\n🎨 Testing UI Actions Generation...")
        
        ui_tests = [
            {
                "message": "tell me about kerala",
                "expected_actions": {
                    "card_add": {"category": "destination", "min_count": 1},
                    "question_chip": {"min_count": 1}
                },
                "description": "Destination cards and question chips"
            },
            {
                "message": "show me hotels in manali",
                "expected_actions": {
                    "card_add": {"category": "hotel", "min_count": 1},
                    "question_chip": {"min_count": 1}
                },
                "description": "Hotel cards and question chips"
            },
            {
                "message": "plan a trip to rishikesh",
                "expected_actions": {
                    "prompt": {"min_count": 1}
                },
                "description": "Prompt actions for trip planning"
            }
        ]
        
        ui_tests_passed = 0
        for i, test_case in enumerate(ui_tests):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_ui_{i}",
                "user_profile": {},
                "trip_details": {}
            }
            
            success, response = self.run_test(f"UI Actions {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                
                test_passed = True
                for action_type, requirements in test_case["expected_actions"].items():
                    if action_type == "card_add":
                        cards = [a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == requirements['category']]
                        if len(cards) >= requirements['min_count']:
                            print(f"      ✅ {action_type} ({requirements['category']}): {len(cards)} generated")
                        else:
                            print(f"      ❌ {action_type} ({requirements['category']}): {len(cards)} < {requirements['min_count']}")
                            test_passed = False
                    else:
                        actions = [a for a in ui_actions if a.get('type') == action_type]
                        if len(actions) >= requirements['min_count']:
                            print(f"      ✅ {action_type}: {len(actions)} generated")
                        else:
                            print(f"      ❌ {action_type}: {len(actions)} < {requirements['min_count']}")
                            test_passed = False
                
                if test_passed:
                    ui_tests_passed += 1
        
        print(f"\n🎨 UI Actions Generation: {ui_tests_passed}/{len(ui_tests)} tests passed")
        return ui_tests_passed >= 2

    def test_trip_planning_flow(self):
        """Test complete trip planning process"""
        print(f"\n🗺️  Testing Complete Trip Planning Flow...")
        
        session_id = f"{self.session_id}_trip_flow"
        
        # Step 1: Initial trip request
        print(f"\n   Step 1: Initial trip planning request...")
        chat_data_1 = {
            "message": "I want to plan a trip to Manali",
            "session_id": session_id,
            "user_profile": {},
            "trip_details": {}
        }
        
        success_1, response_1 = self.run_test("Trip Planning Step 1", "POST", "chat", 200, data=chat_data_1)
        
        if not success_1:
            print("   ❌ Initial trip request failed")
            return False
        
        # Step 2: Provide more details
        print(f"\n   Step 2: Providing trip details...")
        chat_data_2 = {
            "message": "I want to go for 5 days with my partner, budget around 30000",
            "session_id": session_id,
            "user_profile": {},
            "trip_details": {
                "destination": "Manali",
                "dates": {"start_date": "2024-12-15", "end_date": "2024-12-20"},
                "travelers": {"adults": 2, "children": 0},
                "budget": {"per_night": 3000}
            }
        }
        
        success_2, response_2 = self.run_test("Trip Planning Step 2", "POST", "chat", 200, data=chat_data_2)
        
        if not success_2:
            print("   ❌ Trip details step failed")
            return False
        
        # Step 3: Request complete itinerary
        print(f"\n   Step 3: Requesting complete itinerary...")
        chat_data_3 = {
            "message": "Create a complete itinerary with activities and accommodations",
            "session_id": session_id,
            "user_profile": {},
            "trip_details": {
                "destination": "Manali",
                "dates": {"start_date": "2024-12-15", "end_date": "2024-12-20"},
                "travelers": {"adults": 2, "children": 0},
                "budget": {"per_night": 3000}
            }
        }
        
        success_3, response_3 = self.run_test("Trip Planning Step 3", "POST", "chat", 200, data=chat_data_3)
        
        if success_3:
            chat_text = response_3.get('chat_text', '').lower()
            ui_actions = response_3.get('ui_actions', [])
            
            # Check for complete itinerary elements
            itinerary_elements = [
                "day 1" in chat_text or "day 2" in chat_text,
                "manali" in chat_text,
                "₹" in chat_text or "price" in chat_text,
                "activity" in chat_text or "hotel" in chat_text,
                len(chat_text) > 500  # Substantial response
            ]
            
            elements_found = sum(itinerary_elements)
            
            if elements_found >= 4:
                print(f"   ✅ Complete trip planning flow working")
                print(f"      Itinerary elements found: {elements_found}/5")
                print(f"      Response length: {len(chat_text)} characters")
                print(f"      UI actions: {len(ui_actions)}")
                return True
            else:
                print(f"   ❌ Trip planning flow incomplete")
                print(f"      Itinerary elements: {elements_found}/5")
                return False
        else:
            print("   ❌ Final itinerary step failed")
            return False

    def test_error_handling(self):
        """Test error scenarios and edge cases"""
        print(f"\n⚠️  Testing Error Handling...")
        
        error_tests = [
            {
                "data": {"message": "", "session_id": self.session_id},
                "description": "Empty message"
            },
            {
                "data": {"message": "x" * 10000, "session_id": self.session_id},
                "description": "Very long message"
            },
            {
                "data": {"message": "plan trip", "session_id": None},
                "description": "No session ID"
            },
            {
                "data": {"message": "🎉🎊🎈 plan trip with emojis 🌟✨", "session_id": self.session_id},
                "description": "Message with emojis"
            }
        ]
        
        error_tests_passed = 0
        for i, test_case in enumerate(error_tests):
            print(f"\n   Testing: {test_case['description']}")
            
            success, response = self.run_test(f"Error Test {i+1}", "POST", "chat", 200, data=test_case["data"])
            
            if success:
                chat_text = response.get('chat_text', '')
                if len(chat_text) > 0:  # Should still provide some response
                    error_tests_passed += 1
                    print(f"      ✅ Handled gracefully with response")
                else:
                    print(f"      ⚠️  No response text provided")
            else:
                print(f"      ❌ Failed to handle error case")
        
        print(f"\n⚠️  Error Handling: {error_tests_passed}/{len(error_tests)} tests passed")
        return error_tests_passed >= 3

    def test_indian_destinations_contextual_responses(self):
        """Test contextual and intelligent responses for Indian destinations"""
        print(f"\n🇮🇳 Testing Indian Destinations Contextual Responses...")
        
        indian_destinations = [
            {
                "message": "tell me about kerala backwaters",
                "expected_keywords": ["kerala", "backwater", "houseboat", "alleppey", "kumarakom"],
                "description": "Kerala backwaters query"
            },
            {
                "message": "plan adventure activities in manali",
                "expected_keywords": ["manali", "paragliding", "rafting", "solang", "adventure"],
                "description": "Manali adventure query"
            },
            {
                "message": "show me rishikesh spiritual experiences",
                "expected_keywords": ["rishikesh", "yoga", "ganga", "spiritual", "ashram"],
                "description": "Rishikesh spiritual query"
            },
            {
                "message": "goa beach resorts and nightlife",
                "expected_keywords": ["goa", "beach", "resort", "nightlife", "baga"],
                "description": "Goa beach and nightlife query"
            },
            {
                "message": "rajasthan desert safari and palaces",
                "expected_keywords": ["rajasthan", "desert", "safari", "palace", "jaisalmer"],
                "description": "Rajasthan desert and heritage query"
            }
        ]
        
        contextual_tests_passed = 0
        for i, test_case in enumerate(indian_destinations):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["message"],
                "session_id": f"{self.session_id}_indian_{i}",
                "user_profile": {},
                "trip_details": {}
            }
            
            success, response = self.run_test(f"Indian Destination {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '').lower()
                ui_actions = response.get('ui_actions', [])
                
                # Check for contextual keywords
                keyword_matches = sum(1 for keyword in test_case["expected_keywords"] if keyword.lower() in chat_text)
                
                # Check for substantial and intelligent response
                is_intelligent = (
                    len(chat_text) > 200 and  # Substantial response
                    keyword_matches >= 3 and  # Contextual keywords
                    len(ui_actions) > 0  # Generated UI actions
                )
                
                if is_intelligent:
                    contextual_tests_passed += 1
                    print(f"      ✅ Intelligent contextual response")
                    print(f"         Keywords found: {keyword_matches}/{len(test_case['expected_keywords'])}")
                    print(f"         Response length: {len(chat_text)} chars")
                    print(f"         UI actions: {len(ui_actions)}")
                else:
                    print(f"      ❌ Response not sufficiently contextual/intelligent")
                    print(f"         Keywords: {keyword_matches}/{len(test_case['expected_keywords'])}")
                    print(f"         Length: {len(chat_text)} chars")
                    print(f"         UI actions: {len(ui_actions)}")
        
        print(f"\n🇮🇳 Indian Destinations: {contextual_tests_passed}/{len(indian_destinations)} tests passed")
        return contextual_tests_passed >= 4

def main():
    print("🚀 Starting LLM Agent Integration Testing...")
    print("=" * 60)
    
    tester = LLMAgentTester()
    
    # Run all LLM agent tests
    test_results = []
    
    print("\n🎯 REVIEW REQUEST SPECIFIC TESTS")
    print("=" * 40)
    
    # 1. Chat API Endpoint Testing
    chat_api_success = tester.test_chat_api_with_specific_messages()
    test_results.append(chat_api_success)
    
    # 2. Multi-Agent System Testing
    multi_agent_success = tester.test_multi_agent_system()
    test_results.append(multi_agent_success)
    
    # 3. Slot Agents Testing
    slot_agents_success = tester.test_slot_agents_extraction()
    test_results.append(slot_agents_success)
    
    # 4. PlannerAgent Testing
    planner_success = tester.test_planner_agent_itineraries()
    test_results.append(planner_success)
    
    # 5. AccommodationAgent Testing
    accommodation_success = tester.test_accommodation_agent()
    test_results.append(accommodation_success)
    
    # 6. UI Actions Generation Testing
    ui_actions_success = tester.test_ui_actions_generation()
    test_results.append(ui_actions_success)
    
    # 7. Trip Planning Flow Testing
    trip_flow_success = tester.test_trip_planning_flow()
    test_results.append(trip_flow_success)
    
    # 8. Error Handling Testing
    error_handling_success = tester.test_error_handling()
    test_results.append(error_handling_success)
    
    # 9. Indian Destinations Contextual Testing
    indian_destinations_success = tester.test_indian_destinations_contextual_responses()
    test_results.append(indian_destinations_success)
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 LLM AGENT INTEGRATION RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Detailed results analysis
    test_names = [
        "Chat API with Specific Messages",
        "Multi-Agent System",
        "Slot Agents Extraction", 
        "PlannerAgent Itineraries",
        "AccommodationAgent",
        "UI Actions Generation",
        "Trip Planning Flow",
        "Error Handling",
        "Indian Destinations Contextual"
    ]
    
    print(f"\n🎯 DETAILED TEST RESULTS:")
    for i, (test_name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed_tests = sum(test_results)
    print(f"\nOverall LLM Agent Tests: {passed_tests}/{len(test_results)} passed")
    
    # Assessment
    if passed_tests >= 7:
        print("🎉 Excellent! LLM agents are working intelligently!")
        return 0
    elif passed_tests >= 5:
        print("✅ Good! Most LLM agent functionality is working")
        return 0
    elif passed_tests >= 3:
        print("⚠️  Warning! Some LLM agent issues detected")
        return 1
    else:
        print("❌ Critical! LLM agents are not working properly")
        return 1

if __name__ == "__main__":
    sys.exit(main())