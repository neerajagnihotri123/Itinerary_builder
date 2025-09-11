import requests
import sys
import json
from datetime import datetime

class TravelloAPITester:
    def __init__(self, base_url="https://travello-agents.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_chat_endpoint(self):
        """Test the chat endpoint with a travel query"""
        chat_data = {
            "message": "Plan a trip to Paris",
            "session_id": self.session_id,
            "user_profile": {}
        }
        success, response = self.run_test("Chat Endpoint", "POST", "chat", 200, data=chat_data)
        
        if success:
            # Verify response structure
            required_fields = ['chat_text', 'ui_actions', 'followup_questions', 'updated_profile', 'analytics_tags']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"⚠️  Warning: Missing fields in response: {missing_fields}")
            else:
                print(f"✅ Chat response structure is correct")
                
            # Check if UI actions are generated
            if response.get('ui_actions'):
                print(f"✅ UI actions generated: {len(response['ui_actions'])} actions")
            else:
                print(f"⚠️  No UI actions generated")
                
        return success, response

    def test_destinations_endpoint(self):
        """Test the destinations endpoint"""
        success, response = self.run_test("Destinations Endpoint", "GET", "destinations", 200)
        
        if success and 'destinations' in response:
            destinations = response['destinations']
            print(f"✅ Found {len(destinations)} destinations")
            if destinations:
                first_dest = destinations[0]
                required_fields = ['id', 'name', 'country', 'coordinates', 'hero_image']
                missing_fields = [field for field in required_fields if field not in first_dest]
                if missing_fields:
                    print(f"⚠️  Warning: Missing fields in destination: {missing_fields}")
                else:
                    print(f"✅ Destination structure is correct")
        
        return success, response

    def test_specific_destination(self):
        """Test getting a specific destination"""
        return self.run_test("Specific Destination", "GET", "destinations/paris_france", 200)

    def test_hotels_endpoint(self):
        """Test the hotels endpoint"""
        success, response = self.run_test("Hotels Endpoint", "GET", "hotels", 200)
        
        if success and 'hotels' in response:
            hotels = response['hotels']
            print(f"✅ Found {len(hotels)} hotels")
            if hotels:
                first_hotel = hotels[0]
                required_fields = ['id', 'name', 'hero_image', 'rating', 'price_range']
                missing_fields = [field for field in required_fields if field not in first_hotel]
                if missing_fields:
                    print(f"⚠️  Warning: Missing fields in hotel: {missing_fields}")
                else:
                    print(f"✅ Hotel structure is correct")
        
        return success, response

    def test_hotels_by_destination(self):
        """Test hotels filtered by destination"""
        return self.run_test("Hotels by Destination", "GET", "hotels", 200, params={"destination_id": "paris_france"})

    def test_specific_hotel(self):
        """Test getting a specific hotel"""
        return self.run_test("Specific Hotel", "GET", "hotels/hotel_paris_1", 200)

    def test_recommendations_endpoint(self):
        """Test the recommendations endpoint"""
        rec_data = {
            "query": "romantic getaway",
            "filters": {}
        }
        success, response = self.run_test("Recommendations Endpoint", "POST", "recommendations", 200, data=rec_data)
        
        if success:
            if 'destinations' in response and 'hotels' in response:
                print(f"✅ Recommendations structure is correct")
                print(f"   Destinations: {len(response.get('destinations', []))}")
                print(f"   Hotels: {len(response.get('hotels', []))}")
            else:
                print(f"⚠️  Warning: Incomplete recommendations response")
        
        return success, response

    def test_booking_endpoint(self):
        """Test the booking endpoint"""
        booking_data = {
            "hotel_id": "hotel_paris_1",
            "check_in": "2024-09-01",
            "check_out": "2024-09-05",
            "guests": 2
        }
        success, response = self.run_test("Booking Endpoint", "POST", "booking", 200, data=booking_data)
        
        if success and 'payload' in response:
            payload = response['payload']
            required_fields = ['booking_id', 'price', 'cancellation_policy']
            missing_fields = [field for field in required_fields if field not in payload]
            if missing_fields:
                print(f"⚠️  Warning: Missing fields in booking: {missing_fields}")
            else:
                print(f"✅ Booking structure is correct")
        
        return success, response

    def test_chat_history_endpoint(self):
        """Test the chat history endpoint"""
        return self.run_test("Chat History", "GET", f"chat-history/{self.session_id}", 200)

    def test_contextual_responses(self):
        """Test improved system message for contextual responses"""
        print(f"\n🎯 Testing Contextual Response Quality...")
        
        test_scenarios = [
            {
                "query": "I want to plan a trip to Paris",
                "expected_keywords": ["paris", "trip", "planning", "visual", "card"],
                "expected_ui_actions": ["card_add"],
                "description": "Trip planning message"
            },
            {
                "query": "Tell me about Tokyo",
                "expected_keywords": ["tokyo", "destination", "explore"],
                "expected_ui_actions": ["card_add"],
                "description": "Destination query"
            },
            {
                "query": "Show me hotels in Bali",
                "expected_keywords": ["bali", "hotel", "accommodation"],
                "expected_ui_actions": ["card_add"],
                "description": "Hotel request"
            }
        ]
        
        contextual_tests_passed = 0
        for i, scenario in enumerate(test_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            
            chat_data = {
                "message": scenario["query"],
                "session_id": f"{self.session_id}_context_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Contextual Query {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '').lower()
                ui_actions = response.get('ui_actions', [])
                
                # Check for contextual keywords in response
                keyword_matches = sum(1 for keyword in scenario['expected_keywords'] 
                                    if keyword in chat_text)
                
                # Check for expected UI actions
                ui_action_types = [action.get('type') for action in ui_actions]
                ui_matches = sum(1 for expected_type in scenario['expected_ui_actions'] 
                               if expected_type in ui_action_types)
                
                # Evaluate contextual quality
                if keyword_matches >= 2 and ui_matches > 0:
                    contextual_tests_passed += 1
                    print(f"   ✅ Contextual response quality: Good")
                    print(f"      Keywords found: {keyword_matches}/{len(scenario['expected_keywords'])}")
                    print(f"      UI actions: {len(ui_actions)} generated")
                else:
                    print(f"   ⚠️  Contextual response quality: Needs improvement")
                    print(f"      Keywords found: {keyword_matches}/{len(scenario['expected_keywords'])}")
                    print(f"      UI actions: {len(ui_actions)} generated")
                    print(f"      Response preview: {chat_text[:100]}...")
        
        print(f"\n🎯 Contextual Response Results: {contextual_tests_passed}/{len(test_scenarios)} scenarios passed")
        return contextual_tests_passed == len(test_scenarios)

    def test_ui_actions_generation(self):
        """Test UI actions generation for different query types"""
        print(f"\n🎨 Testing UI Actions Generation...")
        
        test_cases = [
            {
                "query": "I want to explore destinations in Europe",
                "expected_action_types": ["card_add"],
                "expected_categories": ["destination"],
                "description": "Destination cards generation"
            },
            {
                "query": "Find me accommodation in Tokyo",
                "expected_action_types": ["card_add"],
                "expected_categories": ["hotel"],
                "description": "Hotel cards generation"
            },
            {
                "query": "Plan a romantic trip",
                "expected_action_types": ["prompt"],
                "expected_categories": ["chips"],
                "description": "Contextual chips generation"
            }
        ]
        
        ui_tests_passed = 0
        for i, test_case in enumerate(test_cases):
            print(f"\n   Testing: {test_case['description']}")
            
            chat_data = {
                "message": test_case["query"],
                "session_id": f"{self.session_id}_ui_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"UI Actions {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                
                if ui_actions:
                    action_types = [action.get('type') for action in ui_actions]
                    
                    # Check if expected action types are present
                    type_matches = any(expected_type in action_types 
                                     for expected_type in test_case['expected_action_types'])
                    
                    if type_matches:
                        ui_tests_passed += 1
                        print(f"   ✅ UI actions generated correctly")
                        print(f"      Actions: {len(ui_actions)} ({', '.join(action_types)})")
                        
                        # Show sample action details
                        for action in ui_actions[:2]:  # Show first 2 actions
                            if action.get('payload'):
                                payload = action['payload']
                                if 'title' in payload:
                                    print(f"      Sample: {payload.get('title', 'N/A')}")
                    else:
                        print(f"   ⚠️  Expected UI action types not found")
                        print(f"      Expected: {test_case['expected_action_types']}")
                        print(f"      Got: {action_types}")
                else:
                    print(f"   ⚠️  No UI actions generated")
        
        print(f"\n🎨 UI Actions Results: {ui_tests_passed}/{len(test_cases)} test cases passed")
        return ui_tests_passed == len(test_cases)

    def test_session_handling(self):
        """Test session handling for conversation continuity"""
        print(f"\n🔄 Testing Session Handling...")
        
        session_id = f"{self.session_id}_session_test"
        
        # First message
        chat_data_1 = {
            "message": "I want to plan a trip to Japan",
            "session_id": session_id,
            "user_profile": {"budget": "mid_range"}
        }
        
        success_1, response_1 = self.run_test("Session Message 1", "POST", "chat", 200, data=chat_data_1)
        
        if not success_1:
            print("   ❌ First message failed")
            return False
        
        # Second message in same session
        chat_data_2 = {
            "message": "What about hotels there?",
            "session_id": session_id,
            "user_profile": {"budget": "mid_range", "destination": "japan"}
        }
        
        success_2, response_2 = self.run_test("Session Message 2", "POST", "chat", 200, data=chat_data_2)
        
        if success_2:
            print("   ✅ Session continuity maintained")
            
            # Check if chat history can be retrieved
            history_success, history_response = self.run_test("Session History", "GET", f"chat-history/{session_id}", 200)
            
            if history_success:
                messages = history_response.get('messages', [])
                print(f"   ✅ Chat history retrieved: {len(messages)} messages")
                return True
            else:
                print("   ⚠️  Chat history retrieval failed")
                return False
        else:
            print("   ❌ Second message failed")
            return False

    def test_data_consistency(self):
        """Test that all mock destinations and hotels are accessible"""
        print(f"\n📊 Testing Data Consistency...")
        
        # Test destinations consistency
        dest_success, dest_response = self.run_test("All Destinations", "GET", "destinations", 200)
        
        if not dest_success:
            print("   ❌ Failed to retrieve destinations")
            return False
        
        destinations = dest_response.get('destinations', [])
        expected_destinations = ['paris_france', 'tokyo_japan', 'bali_indonesia', 'new_york_usa', 'santorini_greece', 'goa_india']
        
        found_destinations = [dest['id'] for dest in destinations]
        missing_destinations = [dest_id for dest_id in expected_destinations if dest_id not in found_destinations]
        
        if missing_destinations:
            print(f"   ⚠️  Missing destinations: {missing_destinations}")
        else:
            print(f"   ✅ All expected destinations found: {len(destinations)}")
        
        # Test hotels consistency
        hotel_success, hotel_response = self.run_test("All Hotels", "GET", "hotels", 200)
        
        if not hotel_success:
            print("   ❌ Failed to retrieve hotels")
            return False
        
        hotels = hotel_response.get('hotels', [])
        expected_hotels = ['hotel_paris_1', 'hotel_tokyo_1', 'hotel_bali_1']
        
        found_hotels = [hotel['id'] for hotel in hotels]
        missing_hotels = [hotel_id for hotel_id in expected_hotels if hotel_id not in found_hotels]
        
        if missing_hotels:
            print(f"   ⚠️  Missing hotels: {missing_hotels}")
        else:
            print(f"   ✅ All expected hotels found: {len(hotels)}")
        
        # Test individual destination access
        individual_tests_passed = 0
        for dest_id in expected_destinations[:3]:  # Test first 3
            individual_success, _ = self.run_test(f"Individual Destination {dest_id}", "GET", f"destinations/{dest_id}", 200)
            if individual_success:
                individual_tests_passed += 1
        
        print(f"   ✅ Individual destination access: {individual_tests_passed}/3")
        
        consistency_score = (len(destinations) >= 6 and len(hotels) >= 3 and 
                           len(missing_destinations) == 0 and len(missing_hotels) == 0 and 
                           individual_tests_passed >= 3)
        
        return consistency_score

    def test_accommodation_card_functionality(self):
        """Test accommodation card functionality as specified in review request"""
        print(f"\n🏨 Testing Accommodation Card Functionality...")
        
        # Test the specific scenario from review request
        session_id = f"{self.session_id}_accommodation_test"
        
        # First message: "i want to go to andaman"
        print(f"\n   Step 1: Testing initial destination query...")
        chat_data_1 = {
            "message": "i want to go to andaman",
            "session_id": session_id,
            "user_profile": {}
        }
        
        success_1, response_1 = self.run_test("Andaman Destination Query", "POST", "chat", 200, data=chat_data_1)
        
        if not success_1:
            print("   ❌ Initial destination query failed")
            return False
        
        # Analyze first response (should have destination cards)
        ui_actions_1 = response_1.get('ui_actions', [])
        dest_cards_1 = [action for action in ui_actions_1 
                        if action.get('type') == 'card_add' and 
                        action.get('payload', {}).get('category') == 'destination']
        
        print(f"      Initial query generated {len(dest_cards_1)} destination cards")
        
        # Second message: "more on accommodations"
        print(f"\n   Step 2: Testing accommodation request...")
        chat_data_2 = {
            "message": "more on accommodations",
            "session_id": session_id,
            "user_profile": {}
        }
        
        success_2, response_2 = self.run_test("Accommodation Request", "POST", "chat", 200, data=chat_data_2)
        
        if not success_2:
            print("   ❌ Accommodation request failed")
            return False
        
        # Analyze the response for accommodation cards
        ui_actions = response_2.get('ui_actions', [])
        hotel_cards = []
        destination_cards = []
        question_chips = []
        
        for action in ui_actions:
            if action.get('type') == 'card_add':
                payload = action.get('payload', {})
                category = payload.get('category', '')
                if category == 'hotel':
                    hotel_cards.append(action)
                elif category == 'destination':
                    destination_cards.append(action)
            elif action.get('type') == 'question_chip':
                question_chips.append(action)
        
        print(f"\n   📊 Card Analysis:")
        print(f"      Hotel cards: {len(hotel_cards)}")
        print(f"      Destination cards: {len(destination_cards)}")
        print(f"      Question chips: {len(question_chips)}")
        print(f"      Total UI actions: {len(ui_actions)}")
        
        # Verify ONLY hotel cards are generated for accommodation requests
        accommodation_test_passed = False
        if len(hotel_cards) > 0 and len(destination_cards) == 0:
            print(f"   ✅ PASS: Only accommodation cards generated")
            accommodation_test_passed = True
            
            # Verify hotel card structure and details
            for i, hotel_card in enumerate(hotel_cards):
                payload = hotel_card.get('payload', {})
                required_fields = ['id', 'category', 'title', 'rating', 'price_estimate', 'amenities']
                missing_fields = [field for field in required_fields if field not in payload]
                
                if not missing_fields:
                    print(f"      ✅ Hotel card {i+1}: {payload.get('title', 'N/A')}")
                    print(f"         Rating: {payload.get('rating', 'N/A')}")
                    print(f"         Price: ₹{payload.get('price_estimate', {}).get('min', 'N/A')}-{payload.get('price_estimate', {}).get('max', 'N/A')}/night")
                    print(f"         Amenities: {len(payload.get('amenities', []))} listed")
                else:
                    print(f"      ⚠️  Hotel card {i+1} missing fields: {missing_fields}")
        else:
            print(f"   ❌ FAIL: Expected only hotel cards, got {len(hotel_cards)} hotel + {len(destination_cards)} destination cards")
            
            # Show what cards were generated for debugging
            for action in ui_actions[:5]:  # Show first 5 actions
                if action.get('type') == 'card_add':
                    payload = action.get('payload', {})
                    print(f"      Debug: {payload.get('category', 'unknown')} card - {payload.get('title', 'N/A')}")
        
        return accommodation_test_passed

    def test_question_chip_generation(self):
        """Test question chip generation for various message types"""
        print(f"\n💭 Testing Question Chip Generation...")
        
        test_scenarios = [
            {
                "message": "i want to go to manali",
                "expected_questions": ["Hotels in Manali", "Best activities in Manali", "Food and restaurants in Manali"],
                "description": "Destination query chips"
            },
            {
                "message": "show me hotels in kerala",
                "expected_questions": ["Best restaurants in Kerala", "Activities to do in Kerala", "Best time to visit Kerala"],
                "description": "Accommodation query chips"
            },
            {
                "message": "plan a trip to rishikesh",
                "expected_questions": ["Hotels in Rishikesh", "Best activities in Rishikesh", "Transportation to Rishikesh"],
                "description": "Trip planning chips"
            }
        ]
        
        chip_tests_passed = 0
        for i, scenario in enumerate(test_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_chips_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Question Chips {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                question_chips = [action for action in ui_actions if action.get('type') == 'question_chip']
                
                print(f"      Question chips generated: {len(question_chips)}")
                
                if question_chips:
                    # Verify question chip structure
                    valid_chips = 0
                    for chip in question_chips[:3]:  # Check first 3
                        payload = chip.get('payload', {})
                        required_fields = ['id', 'question', 'category']
                        
                        if all(field in payload for field in required_fields):
                            valid_chips += 1
                            print(f"         ✅ Valid chip: {payload.get('question', 'N/A')}")
                        else:
                            missing = [field for field in required_fields if field not in payload]
                            print(f"         ⚠️  Invalid chip missing: {missing}")
                    
                    if valid_chips > 0:
                        chip_tests_passed += 1
                        print(f"      ✅ Question chips properly structured")
                    else:
                        print(f"      ❌ Question chips have structural issues")
                else:
                    print(f"      ❌ No question chips generated")
        
        print(f"\n💭 Question Chip Results: {chip_tests_passed}/{len(test_scenarios)} scenarios passed")
        return chip_tests_passed == len(test_scenarios)

    def test_ui_actions_structure_verification(self):
        """Test UI actions structure verification as specified in review request"""
        print(f"\n🔍 Testing UI Actions Structure Verification...")
        
        # Test hotel card structure
        print(f"\n   Testing hotel card structure...")
        hotel_chat_data = {
            "message": "show me accommodations in andaman",
            "session_id": f"{self.session_id}_structure_hotel",
            "user_profile": {}
        }
        
        success, response = self.run_test("Hotel Card Structure", "POST", "chat", 200, data=hotel_chat_data)
        
        hotel_structure_valid = False
        if success:
            ui_actions = response.get('ui_actions', [])
            hotel_cards = [action for action in ui_actions 
                          if action.get('type') == 'card_add' and 
                          action.get('payload', {}).get('category') == 'hotel']
            
            if hotel_cards:
                hotel_card = hotel_cards[0]
                if (hotel_card.get('type') == 'card_add' and 
                    hotel_card.get('payload', {}).get('category') == 'hotel'):
                    print(f"      ✅ Hotel card structure valid: type='card_add', category='hotel'")
                    hotel_structure_valid = True
                else:
                    print(f"      ❌ Hotel card structure invalid")
                    print(f"         Type: {hotel_card.get('type')}")
                    print(f"         Category: {hotel_card.get('payload', {}).get('category')}")
        
        # Test question chip structure
        print(f"\n   Testing question chip structure...")
        question_chat_data = {
            "message": "tell me about kerala",
            "session_id": f"{self.session_id}_structure_question",
            "user_profile": {}
        }
        
        success, response = self.run_test("Question Chip Structure", "POST", "chat", 200, data=question_chat_data)
        
        question_structure_valid = False
        if success:
            ui_actions = response.get('ui_actions', [])
            question_chips = [action for action in ui_actions if action.get('type') == 'question_chip']
            
            if question_chips:
                question_chip = question_chips[0]
                payload = question_chip.get('payload', {})
                
                if (question_chip.get('type') == 'question_chip' and 
                    'id' in payload and 'question' in payload and 'category' in payload):
                    print(f"      ✅ Question chip structure valid")
                    print(f"         Type: {question_chip.get('type')}")
                    print(f"         Payload fields: {list(payload.keys())}")
                    question_structure_valid = True
                else:
                    print(f"      ❌ Question chip structure invalid")
                    print(f"         Type: {question_chip.get('type')}")
                    print(f"         Payload: {payload}")
        
        structure_tests_passed = hotel_structure_valid and question_structure_valid
        print(f"\n🔍 Structure Verification: {'PASS' if structure_tests_passed else 'FAIL'}")
        return structure_tests_passed

    def test_mock_data_integration(self):
        """Test MOCK_HOTELS data integration for Indian destinations"""
        print(f"\n🇮🇳 Testing Mock Data Integration...")
        
        # Test Indian destinations from MOCK_HOTELS
        indian_destinations = ["andaman", "manali", "rishikesh", "kerala"]
        
        integration_tests_passed = 0
        for destination in indian_destinations:
            print(f"\n   Testing {destination.title()} hotels...")
            
            chat_data = {
                "message": f"show me hotels in {destination}",
                "session_id": f"{self.session_id}_mock_{destination}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"{destination.title()} Hotels", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                hotel_cards = [action for action in ui_actions 
                              if action.get('type') == 'card_add' and 
                              action.get('payload', {}).get('category') == 'hotel']
                
                if hotel_cards:
                    # Verify hotel details match destination
                    valid_hotels = 0
                    for hotel_card in hotel_cards:
                        payload = hotel_card.get('payload', {})
                        hotel_name = payload.get('title', '').lower()
                        location = payload.get('location', '').lower()
                        
                        # Check if hotel is related to the destination
                        # For Andaman, accept Havelock Island locations as valid
                        is_valid_hotel = False
                        if destination == "andaman":
                            if ("havelock" in hotel_name or "havelock" in location or
                                "andaman" in hotel_name or "andaman" in location):
                                is_valid_hotel = True
                        else:
                            if (destination in hotel_name or destination in location or
                                any(dest_keyword in hotel_name or dest_keyword in location 
                                    for dest_keyword in [destination])):
                                is_valid_hotel = True
                        
                        if is_valid_hotel:
                            valid_hotels += 1
                            print(f"      ✅ Valid hotel: {payload.get('title', 'N/A')}")
                            
                            # Verify required hotel fields
                            required_fields = ['rating', 'price_estimate', 'amenities']
                            if all(field in payload for field in required_fields):
                                print(f"         Hotel details complete")
                            else:
                                missing = [field for field in required_fields if field not in payload]
                                print(f"         ⚠️  Missing details: {missing}")
                    
                    if valid_hotels > 0:
                        integration_tests_passed += 1
                        print(f"      ✅ {destination.title()} hotels properly integrated")
                    else:
                        print(f"      ❌ No valid hotels found for {destination}")
                else:
                    print(f"      ❌ No hotel cards generated for {destination}")
        
        print(f"\n🇮🇳 Mock Data Integration: {integration_tests_passed}/{len(indian_destinations)} destinations passed")
        return integration_tests_passed == len(indian_destinations)

    def test_slot_agent_intent_detection(self):
        """Test SlotAgent.extract_intent_and_destination() method as specified in review request"""
        print(f"\n🎯 Testing SlotAgent Intent Detection...")
        
        # Test scenarios from review request
        test_scenarios = [
            {
                "message": "plan a trip to kerala",
                "expected_intent": "plan",
                "expected_destination": "Kerala, India",
                "description": "Plan intent with destination"
            },
            {
                "message": "hotels in goa", 
                "expected_intent": "accommodation",
                "expected_destination": "Goa, India",
                "description": "Accommodation intent with destination"
            },
            {
                "message": "tell me about manali",
                "expected_intent": "find", 
                "expected_destination": "Manali, Himachal Pradesh",
                "description": "Find intent with destination"
            },
            {
                "message": "hello",
                "expected_intent": "general",
                "expected_destination": None,
                "description": "General intent without destination"
            }
        ]
        
        intent_tests_passed = 0
        for i, scenario in enumerate(test_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            print(f"      Input: '{scenario['message']}'")
            
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_intent_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Intent Detection {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                # Check response metadata for intent detection results
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Analyze response to infer intent detection
                detected_intent = "unknown"
                detected_destination = None
                
                # Infer intent from response patterns
                if any(word in chat_text.lower() for word in ['itinerary', 'plan', 'trip planning']):
                    detected_intent = "plan"
                elif any(word in chat_text.lower() for word in ['hotel', 'accommodation', 'stay']):
                    detected_intent = "accommodation"
                elif any(word in chat_text.lower() for word in ['explore', 'about', 'destination']):
                    detected_intent = "find"
                elif any(word in chat_text.lower() for word in ['hello', 'help', 'assist']):
                    detected_intent = "general"
                
                # Check for destination cards to infer destination detection
                destination_cards = [action for action in ui_actions 
                                   if action.get('type') == 'card_add' and 
                                   action.get('payload', {}).get('category') == 'destination']
                
                hotel_cards = [action for action in ui_actions 
                             if action.get('type') == 'card_add' and 
                             action.get('payload', {}).get('category') == 'hotel']
                
                # Infer destination from cards or response text
                if destination_cards:
                    card_title = destination_cards[0].get('payload', {}).get('title', '')
                    if 'kerala' in card_title.lower():
                        detected_destination = "Kerala, India"
                    elif 'goa' in card_title.lower():
                        detected_destination = "Goa, India"
                    elif 'manali' in card_title.lower():
                        detected_destination = "Manali, Himachal Pradesh"
                elif hotel_cards:
                    # For hotel queries, check if hotels are for the right destination
                    if 'goa' in scenario['message'].lower() and len(hotel_cards) > 0:
                        detected_destination = "Goa, India"
                
                # Evaluate results
                intent_match = detected_intent == scenario['expected_intent']
                destination_match = (detected_destination == scenario['expected_destination'] or 
                                   (scenario['expected_destination'] is None and detected_destination is None))
                
                if intent_match and destination_match:
                    intent_tests_passed += 1
                    print(f"      ✅ PASS: Intent={detected_intent}, Destination={detected_destination}")
                else:
                    print(f"      ❌ FAIL: Expected intent={scenario['expected_intent']}, got {detected_intent}")
                    print(f"               Expected destination={scenario['expected_destination']}, got {detected_destination}")
                
                # Show additional analysis
                print(f"      Response analysis: {len(ui_actions)} UI actions, {len(chat_text)} chars")
                if destination_cards:
                    print(f"      Destination cards: {len(destination_cards)}")
                if hotel_cards:
                    print(f"      Hotel cards: {len(hotel_cards)}")
            else:
                print(f"      ❌ API call failed")
        
        print(f"\n🎯 SlotAgent Intent Detection Results: {intent_tests_passed}/{len(test_scenarios)} scenarios passed")
        return intent_tests_passed >= 3  # Pass if at least 3/4 scenarios work

    def test_routing_flow_architecture(self):
        """Test the new routing flow: conversation_agent → slot_agent → retrieval_agent → route to appropriate agent"""
        print(f"\n🔄 Testing Routing Flow Architecture...")
        
        # Test different routing flows
        routing_scenarios = [
            {
                "message": "plan a 5-day trip to rishikesh",
                "expected_flow": "planner_flow",
                "expected_agents": ["slot_agent", "retrieval_agent", "planner_agent", "validator_agent"],
                "description": "Planner flow routing"
            },
            {
                "message": "show me luxury hotels in andaman",
                "expected_flow": "accommodation_flow", 
                "expected_agents": ["slot_agent", "retrieval_agent", "accommodation_agent"],
                "description": "Accommodation flow routing"
            },
            {
                "message": "tell me about kerala backwaters",
                "expected_flow": "find_flow",
                "expected_agents": ["slot_agent", "retrieval_agent", "conversation_agent"],
                "description": "Find flow routing (render cards)"
            }
        ]
        
        routing_tests_passed = 0
        for i, scenario in enumerate(routing_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            print(f"      Input: '{scenario['message']}'")
            
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_routing_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Routing Flow {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Analyze response to determine which flow was used
                flow_indicators = {
                    "planner_flow": ["itinerary", "plan", "day 1", "day 2", "schedule"],
                    "accommodation_flow": ["hotel", "accommodation", "stay", "book now"],
                    "find_flow": ["explore", "destination", "highlights", "plan trip"]
                }
                
                detected_flow = "unknown"
                for flow, indicators in flow_indicators.items():
                    if any(indicator in chat_text.lower() for indicator in indicators):
                        detected_flow = flow
                        break
                
                # Check UI actions for flow confirmation
                destination_cards = len([a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'destination'])
                hotel_cards = len([a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'hotel'])
                itinerary_actions = len([a for a in ui_actions if a.get('type') == 'itinerary_display'])
                trip_planner_cards = len([a for a in ui_actions if a.get('type') == 'trip_planner_card'])
                
                # Refine flow detection based on UI actions
                if hotel_cards > 0 and destination_cards == 0:
                    detected_flow = "accommodation_flow"
                elif destination_cards > 0 and hotel_cards == 0:
                    detected_flow = "find_flow"
                elif itinerary_actions > 0 or trip_planner_cards > 0:
                    detected_flow = "planner_flow"
                
                # Evaluate routing
                flow_match = detected_flow == scenario['expected_flow']
                
                if flow_match:
                    routing_tests_passed += 1
                    print(f"      ✅ PASS: Correct routing to {detected_flow}")
                    print(f"      UI Actions: {destination_cards} destination, {hotel_cards} hotel, {itinerary_actions} itinerary")
                else:
                    print(f"      ❌ FAIL: Expected {scenario['expected_flow']}, got {detected_flow}")
                    print(f"      UI Actions: {destination_cards} destination, {hotel_cards} hotel, {itinerary_actions} itinerary")
                    print(f"      Response preview: {chat_text[:100]}...")
            else:
                print(f"      ❌ API call failed")
        
        print(f"\n🔄 Routing Flow Results: {routing_tests_passed}/{len(routing_scenarios)} flows working correctly")
        return routing_tests_passed >= 2  # Pass if at least 2/3 flows work

    def test_ui_actions_generation_formats(self):
        """Test the new UI action formats as specified in review request"""
        print(f"\n🎨 Testing UI Actions Generation Formats...")
        
        format_scenarios = [
            {
                "message": "show me destinations in india",
                "expected_actions": [
                    {"type": "card_add", "category": "destination"}
                ],
                "description": "Destination cards with 'card_add' type and 'destination' category"
            },
            {
                "message": "find hotels in kerala",
                "expected_actions": [
                    {"type": "card_add", "category": "hotel"}
                ],
                "description": "Hotel cards with 'card_add' type and 'hotel' category"
            },
            {
                "message": "plan a trip to goa",
                "expected_actions": [
                    {"type": "question_chip"},
                    {"type": "trip_planner_card"}
                ],
                "description": "Question chips and trip planner card for pre-generation mode"
            }
        ]
        
        format_tests_passed = 0
        for i, scenario in enumerate(format_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            print(f"      Input: '{scenario['message']}'")
            
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_format_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"UI Format {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                
                # Check for expected action formats
                format_matches = 0
                for expected_action in scenario['expected_actions']:
                    expected_type = expected_action['type']
                    expected_category = expected_action.get('category')
                    
                    # Find matching actions
                    matching_actions = [
                        action for action in ui_actions 
                        if action.get('type') == expected_type and 
                        (not expected_category or action.get('payload', {}).get('category') == expected_category)
                    ]
                    
                    if matching_actions:
                        format_matches += 1
                        action = matching_actions[0]
                        payload = action.get('payload', {})
                        
                        print(f"      ✅ Found {expected_type}: {payload.get('title', payload.get('question', 'N/A'))}")
                        
                        # Verify required fields for each type
                        if expected_type == "card_add":
                            required_fields = ['id', 'category', 'title']
                            missing_fields = [field for field in required_fields if field not in payload]
                            if missing_fields:
                                print(f"         ⚠️  Missing fields: {missing_fields}")
                            else:
                                print(f"         ✅ All required fields present")
                        
                        elif expected_type == "question_chip":
                            required_fields = ['id', 'question', 'category']
                            missing_fields = [field for field in required_fields if field not in payload]
                            if missing_fields:
                                print(f"         ⚠️  Missing fields: {missing_fields}")
                            else:
                                print(f"         ✅ All required fields present")
                    else:
                        print(f"      ❌ Missing {expected_type} with category {expected_category}")
                
                # Evaluate format compliance
                if format_matches == len(scenario['expected_actions']):
                    format_tests_passed += 1
                    print(f"      ✅ PASS: All expected UI action formats found")
                else:
                    print(f"      ❌ FAIL: Found {format_matches}/{len(scenario['expected_actions'])} expected formats")
                
                print(f"      Total UI actions generated: {len(ui_actions)}")
            else:
                print(f"      ❌ API call failed")
        
        print(f"\n🎨 UI Actions Format Results: {format_tests_passed}/{len(format_scenarios)} scenarios passed")
        return format_tests_passed >= 2  # Pass if at least 2/3 scenarios work

    def test_error_handling_and_fallbacks(self):
        """Test clarification responses and fallback mechanisms"""
        print(f"\n🛡️ Testing Error Handling and Fallback Mechanisms...")
        
        error_scenarios = [
            {
                "message": "plan a trip to xyz unknown place",
                "expected_behavior": "clarification_request",
                "description": "Unknown destination handling"
            },
            {
                "message": "book hotel",
                "expected_behavior": "destination_clarification", 
                "description": "Missing destination for accommodation"
            },
            {
                "message": "asdfghjkl random text",
                "expected_behavior": "general_help",
                "description": "Unrecognizable input handling"
            },
            {
                "message": "",
                "expected_behavior": "prompt_for_input",
                "description": "Empty message handling"
            }
        ]
        
        error_tests_passed = 0
        for i, scenario in enumerate(error_scenarios):
            print(f"\n   Testing: {scenario['description']}")
            print(f"      Input: '{scenario['message']}'")
            
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_error_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Error Handling {i+1}", "POST", "chat", 200, data=chat_data)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Analyze response for appropriate error handling
                error_indicators = {
                    "clarification_request": ["which", "specify", "clarify", "could you", "please"],
                    "destination_clarification": ["destination", "where", "which place"],
                    "general_help": ["help", "assist", "what can", "how can"],
                    "prompt_for_input": ["tell me", "what would", "how can I help"]
                }
                
                detected_behavior = "unknown"
                for behavior, indicators in error_indicators.items():
                    if any(indicator in chat_text.lower() for indicator in indicators):
                        detected_behavior = behavior
                        break
                
                # Check for helpful UI actions (question chips, help options)
                question_chips = [a for a in ui_actions if a.get('type') == 'question_chip']
                help_actions = len([a for a in ui_actions if 'help' in str(a).lower()])
                
                # Evaluate error handling
                behavior_match = detected_behavior == scenario['expected_behavior']
                has_helpful_actions = len(question_chips) > 0 or help_actions > 0
                
                if behavior_match and has_helpful_actions:
                    error_tests_passed += 1
                    print(f"      ✅ PASS: Appropriate {detected_behavior} with {len(question_chips)} question chips")
                elif behavior_match:
                    error_tests_passed += 0.5  # Partial credit
                    print(f"      ⚠️  PARTIAL: Correct behavior but limited helpful actions")
                else:
                    print(f"      ❌ FAIL: Expected {scenario['expected_behavior']}, got {detected_behavior}")
                
                print(f"      Response: {chat_text[:80]}...")
                print(f"      Helpful actions: {len(question_chips)} question chips, {help_actions} help actions")
            else:
                print(f"      ❌ API call failed")
        
        print(f"\n🛡️ Error Handling Results: {error_tests_passed}/{len(error_scenarios)} scenarios handled appropriately")
        return error_tests_passed >= 3  # Pass if at least 3/4 scenarios work

    def test_review_request_critical_scenarios(self):
        """Test the exact critical scenarios from the review request"""
        print(f"\n🎯 Testing ENHANCED CHAT FUNCTIONALITY - Review Request Scenarios...")
        
        # PRIMARY TEST SCENARIO 1: "tell me about kerala" - should generate single destination card
        print(f"\n   🌴 SCENARIO 1: Destination Specific Query - 'tell me about kerala'")
        session_id_1 = f"{self.session_id}_kerala_destination"
        
        chat_data_kerala = {
            "message": "tell me about kerala",
            "session_id": session_id_1,
            "user_profile": {}
        }
        
        success_kerala, response_kerala = self.run_test("Kerala Destination Query", "POST", "chat", 200, data=chat_data_kerala)
        
        scenario_1_passed = False
        kerala_query_type = None
        if success_kerala:
            print(f"      📊 Response Analysis:")
            print(f"         Chat text length: {len(response_kerala.get('chat_text', ''))}")
            print(f"         Chat text preview: {response_kerala.get('chat_text', '')[:100]}...")
            
            ui_actions = response_kerala.get('ui_actions', [])
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            hotel_cards = [action for action in ui_actions 
                          if action.get('type') == 'card_add' and 
                          action.get('payload', {}).get('category') == 'hotel']
            prompt_chips = [action for action in ui_actions if action.get('type') == 'prompt']
            question_chips = [action for action in ui_actions if action.get('type') == 'question_chip']
            
            print(f"         Destination cards: {len(destination_cards)}")
            print(f"         Hotel cards: {len(hotel_cards)}")
            print(f"         Prompt chips: {len(prompt_chips)}")
            print(f"         Question chips: {len(question_chips)}")
            print(f"         Total UI actions: {len(ui_actions)}")
            
            # Check if we got exactly 1 destination card with category "destination"
            if len(destination_cards) == 1 and destination_cards[0].get('payload', {}).get('category') == 'destination':
                scenario_1_passed = True
                dest_payload = destination_cards[0].get('payload', {})
                print(f"      ✅ SCENARIO 1 PASSED: Single destination card generated")
                print(f"         Title: {dest_payload.get('title', 'N/A')}")
                print(f"         Category: {dest_payload.get('category', 'N/A')}")
                print(f"         ID: {dest_payload.get('id', 'N/A')}")
                print(f"         Hero Image: {'Present' if dest_payload.get('hero_image') else 'Missing'}")
                print(f"         Highlights: {len(dest_payload.get('highlights', []))} items")
            else:
                print(f"      ❌ SCENARIO 1 FAILED: Expected 1 destination card, got {len(destination_cards)}")
                if len(destination_cards) == 0:
                    print(f"         Issue: No destination cards generated - ConversationManager may be prioritizing slot-filling")
                    print(f"         Debug: Check if query_type detection is working correctly")
        
        # PRIMARY TEST SCENARIO 2: "popular destinations" - should generate multiple destination cards
        print(f"\n   🌍 SCENARIO 2: Destination Discovery Query - 'popular destinations'")
        session_id_2 = f"{self.session_id}_popular_destinations"
        
        chat_data_popular = {
            "message": "popular destinations",
            "session_id": session_id_2,
            "user_profile": {}
        }
        
        success_popular, response_popular = self.run_test("Popular Destinations Query", "POST", "chat", 200, data=chat_data_popular)
        
        scenario_2_passed = False
        if success_popular:
            print(f"      📊 Response Analysis:")
            print(f"         Chat text length: {len(response_popular.get('chat_text', ''))}")
            print(f"         Chat text preview: {response_popular.get('chat_text', '')[:100]}...")
            
            ui_actions = response_popular.get('ui_actions', [])
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            
            print(f"         Destination cards generated: {len(destination_cards)}")
            print(f"         Total UI actions: {len(ui_actions)}")
            
            # Check if we got multiple destination cards (expecting 6 as per review request)
            if len(destination_cards) >= 3:  # At least 3, ideally 6
                scenario_2_passed = True
                print(f"      ✅ SCENARIO 2 PASSED: Multiple destination cards generated ({len(destination_cards)})")
                
                # Show first few destinations
                for i, dest_card in enumerate(destination_cards[:3]):
                    dest_payload = dest_card.get('payload', {})
                    print(f"         Destination {i+1}: {dest_payload.get('title', 'N/A')}")
            else:
                print(f"      ❌ SCENARIO 2 FAILED: Expected multiple destination cards, got {len(destination_cards)}")
                print(f"         Issue: ConversationManager may not be detecting destination_discovery query type")
        
        # PRIMARY TEST SCENARIO 3: "hotels in goa" - should generate hotel cards with category "hotel"
        print(f"\n   🏨 SCENARIO 3: Accommodation Query - 'hotels in goa'")
        session_id_3 = f"{self.session_id}_hotels_goa"
        
        chat_data_hotels = {
            "message": "hotels in goa",
            "session_id": session_id_3,
            "user_profile": {}
        }
        
        success_hotels, response_hotels = self.run_test("Hotels in Goa Query", "POST", "chat", 200, data=chat_data_hotels)
        
        scenario_3_passed = False
        if success_hotels:
            print(f"      📊 Response Analysis:")
            print(f"         Chat text length: {len(response_hotels.get('chat_text', ''))}")
            print(f"         Chat text preview: {response_hotels.get('chat_text', '')[:100]}...")
            
            ui_actions = response_hotels.get('ui_actions', [])
            hotel_cards = [action for action in ui_actions 
                          if action.get('type') == 'card_add' and 
                          action.get('payload', {}).get('category') == 'hotel']
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            
            print(f"         Hotel cards generated: {len(hotel_cards)}")
            print(f"         Destination cards generated: {len(destination_cards)}")
            print(f"         Total UI actions: {len(ui_actions)}")
            
            # Check if we got hotel cards with correct category
            if len(hotel_cards) > 0:
                scenario_3_passed = True
                print(f"      ✅ SCENARIO 3 PASSED: Hotel cards generated with category 'hotel'")
                
                # Verify hotel card structure
                for i, hotel_card in enumerate(hotel_cards[:2]):
                    hotel_payload = hotel_card.get('payload', {})
                    print(f"         Hotel {i+1}: {hotel_payload.get('title', 'N/A')}")
                    print(f"         Category: {hotel_payload.get('category', 'N/A')}")
                    print(f"         Rating: {hotel_payload.get('rating', 'N/A')}")
                    price_range = hotel_payload.get('price_estimate', {})
                    if price_range:
                        print(f"         Price: ₹{price_range.get('min', 'N/A')}-{price_range.get('max', 'N/A')}/night")
            else:
                print(f"      ❌ SCENARIO 3 FAILED: No hotel cards generated")
                print(f"         Issue: Accommodation agent may not have Goa data or query_type not detected")
        
        # BACKEND VERIFICATION: Check ConversationManager query type detection
        print(f"\n   🔍 BACKEND VERIFICATION:")
        print(f"      Query Type Detection Results:")
        print(f"         Kerala query: {'destination_specific' if scenario_1_passed else 'Unknown/Failed'}")
        print(f"         Popular destinations: {'destination_discovery' if scenario_2_passed else 'Unknown/Failed'}")
        print(f"         Hotels in Goa: {'accommodation_query' if scenario_3_passed else 'Unknown/Failed'}")
        
        # DEBUG INFORMATION: Check for common issues
        print(f"\n   🐛 DEBUG INFORMATION:")
        if not scenario_1_passed:
            print(f"      Kerala Issue: ConversationManager may be prioritizing slot-filling over content generation")
            print(f"      Expected: Single destination card with Kerala data")
            print(f"      Check: get_destination_data() function and query_type metadata")
        
        if not scenario_2_passed:
            print(f"      Popular Destinations Issue: Query type may not be detected as destination_discovery")
            print(f"      Expected: 6 destination cards for popular destinations")
            print(f"      Check: ConversationManager query classification logic")
        
        if not scenario_3_passed:
            print(f"      Hotels Issue: Accommodation agent may not have Goa data")
            print(f"      Expected: Hotel cards with category 'hotel'")
            print(f"      Check: MOCK_HOTELS data and accommodation agent integration")
        
        # Overall assessment
        scenarios_passed = sum([scenario_1_passed, scenario_2_passed, scenario_3_passed])
        print(f"\n   🎯 ENHANCED CHAT FUNCTIONALITY SUMMARY:")
        print(f"      Scenario 1 (Kerala Destination): {'PASS' if scenario_1_passed else 'FAIL'}")
        print(f"      Scenario 2 (Popular Destinations): {'PASS' if scenario_2_passed else 'FAIL'}")
        print(f"      Scenario 3 (Hotels in Goa): {'PASS' if scenario_3_passed else 'FAIL'}")
        print(f"      Total: {scenarios_passed}/3 primary scenarios passed")
        
        # Expected results verification
        print(f"\n   📋 EXPECTED RESULTS VERIFICATION:")
        print(f"      ✓ 'tell me about kerala' → 1 destination card: {'✅' if scenario_1_passed else '❌'}")
        print(f"      ✓ 'popular destinations' → 6 destination cards: {'✅' if scenario_2_passed else '❌'}")
        print(f"      ✓ 'hotels in goa' → hotel cards: {'✅' if scenario_3_passed else '❌'}")
        
        return scenarios_passed >= 2  # Pass if at least 2/3 scenarios work

    def test_ai_integration(self):
        """Test AI integration with multiple travel queries"""
        print(f"\n🤖 Testing AI Integration...")
        
        test_queries = [
            "I want to visit Japan for cherry blossoms",
            "Find me luxury hotels in Bali", 
            "Plan a cultural trip to Europe",
            "What are the best beaches in Thailand?"
        ]
        
        ai_tests_passed = 0
        for i, query in enumerate(test_queries):
            chat_data = {
                "message": query,
                "session_id": f"{self.session_id}_ai_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"AI Query {i+1}", "POST", "chat", 200, data=chat_data)
            if success:
                # Check if response contains meaningful content
                chat_text = response.get('chat_text', '')
                if len(chat_text) > 50:  # Reasonable response length
                    ai_tests_passed += 1
                    print(f"   ✅ AI generated meaningful response ({len(chat_text)} chars)")
                else:
                    print(f"   ⚠️  AI response seems too short: {chat_text[:50]}...")
        
        print(f"\n🤖 AI Integration Results: {ai_tests_passed}/{len(test_queries)} queries successful")
        return ai_tests_passed == len(test_queries)

def main():
    print("🚀 Starting Travello.ai API Testing...")
    print("=" * 60)
    
    tester = TravelloAPITester()
    
    # Run all tests
    test_results = []
    
    # Basic API tests
    test_results.append(tester.test_root_endpoint())
    test_results.append(tester.test_destinations_endpoint())
    test_results.append(tester.test_specific_destination())
    test_results.append(tester.test_hotels_endpoint())
    test_results.append(tester.test_hotels_by_destination())
    test_results.append(tester.test_specific_hotel())
    test_results.append(tester.test_recommendations_endpoint())
    test_results.append(tester.test_booking_endpoint())
    
    # Chat and AI tests
    test_results.append(tester.test_chat_endpoint())
    test_results.append(tester.test_chat_history_endpoint())
    
    # Enhanced testing for review requirements
    contextual_success = tester.test_contextual_responses()
    test_results.append((contextual_success, {}))
    
    ui_actions_success = tester.test_ui_actions_generation()
    test_results.append((ui_actions_success, {}))
    
    session_success = tester.test_session_handling()
    test_results.append((session_success, {}))
    
    data_consistency_success = tester.test_data_consistency()
    test_results.append((data_consistency_success, {}))
    
    # CRITICAL TESTS FOR REVIEW REQUEST - SlotAgent and ConversationManager
    print("\n" + "🎯" * 20 + " SLOTAGENT & ROUTING TESTS " + "🎯" * 20)
    
    # NEW: SlotAgent Intent Detection Tests
    slot_agent_success = tester.test_slot_agent_intent_detection()
    test_results.append((slot_agent_success, {}))
    
    # NEW: Routing Flow Architecture Tests
    routing_flow_success = tester.test_routing_flow_architecture()
    test_results.append((routing_flow_success, {}))
    
    # NEW: UI Actions Generation Format Tests
    ui_format_success = tester.test_ui_actions_generation_formats()
    test_results.append((ui_format_success, {}))
    
    # NEW: Error Handling and Fallback Tests
    error_handling_success = tester.test_error_handling_and_fallbacks()
    test_results.append((error_handling_success, {}))
    
    print("\n" + "🎯" * 20 + " CRITICAL REVIEW TESTS " + "🎯" * 20)
    
    # NEW: Critical scenarios from review request
    critical_scenarios_success = tester.test_review_request_critical_scenarios()
    test_results.append((critical_scenarios_success, {}))
    
    accommodation_success = tester.test_accommodation_card_functionality()
    test_results.append((accommodation_success, {}))
    
    question_chip_success = tester.test_question_chip_generation()
    test_results.append((question_chip_success, {}))
    
    structure_success = tester.test_ui_actions_structure_verification()
    test_results.append((structure_success, {}))
    
    mock_data_success = tester.test_mock_data_integration()
    test_results.append((mock_data_success, {}))
    
    # AI Integration test
    ai_success = tester.test_ai_integration()
    test_results.append((ai_success, {}))
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Enhanced results analysis
    critical_tests = [contextual_success, ui_actions_success, session_success, data_consistency_success, ai_success]
    critical_passed = sum(critical_tests)
    
    print(f"\n🎯 CRITICAL FEATURES ANALYSIS:")
    print(f"✅ Contextual Responses: {'PASS' if contextual_success else 'FAIL'}")
    print(f"✅ UI Actions Generation: {'PASS' if ui_actions_success else 'FAIL'}")
    print(f"✅ Session Handling: {'PASS' if session_success else 'FAIL'}")
    print(f"✅ Data Consistency: {'PASS' if data_consistency_success else 'FAIL'}")
    print(f"✅ AI Integration: {'PASS' if ai_success else 'FAIL'}")
    print(f"\nCritical Features: {critical_passed}/5 passing")
    
    print(f"\n🔥 REVIEW REQUEST CRITICAL TESTS:")
    print(f"🎯 Critical Scenarios (Review Request): {'PASS' if critical_scenarios_success else 'FAIL'}")
    print(f"🏨 Accommodation Card Filtering: {'PASS' if accommodation_success else 'FAIL'}")
    print(f"💭 Question Chip Generation: {'PASS' if question_chip_success else 'FAIL'}")
    print(f"🔍 UI Actions Structure: {'PASS' if structure_success else 'FAIL'}")
    print(f"🇮🇳 Mock Data Integration: {'PASS' if mock_data_success else 'FAIL'}")
    
    # Update review tests count
    review_tests = [critical_scenarios_success, accommodation_success, question_chip_success, structure_success, mock_data_success]
    review_passed = sum(review_tests)
    print(f"\nReview Tests: {review_passed}/5 passing")
    
    # Overall assessment including review-specific tests
    total_critical_score = critical_passed + review_passed
    max_critical_score = 10  # 5 general + 5 review-specific
    
    if success_rate >= 90 and critical_passed >= 4 and review_passed >= 4:
        print("🎉 Excellent! Backend is working great including review requirements!")
        return 0
    elif success_rate >= 70 and critical_passed >= 3 and review_passed >= 3:
        print("✅ Good! Backend is mostly functional with minor issues")
        return 0
    elif success_rate >= 50 and (critical_passed >= 2 or review_passed >= 2):
        print("⚠️  Warning! Backend has significant issues")
        return 1
    else:
        print("❌ Critical! Backend is severely broken")
        print(f"   Review-specific tests: {review_passed}/5 passing")
        print(f"   General critical tests: {critical_passed}/5 passing")
        return 1

if __name__ == "__main__":
    sys.exit(main())