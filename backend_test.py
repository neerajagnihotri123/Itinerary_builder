import requests
import sys
import json
from datetime import datetime

class TravelloAPITester:
    def __init__(self, base_url="https://travelai-hub-1.preview.emergentagent.com"):
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
    
    # AI Integration test
    ai_success = tester.test_ai_integration()
    test_results.append((ai_success, {}))
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 Excellent! Backend is working great!")
        return 0
    elif success_rate >= 70:
        print("✅ Good! Backend is mostly functional with minor issues")
        return 0
    elif success_rate >= 50:
        print("⚠️  Warning! Backend has significant issues")
        return 1
    else:
        print("❌ Critical! Backend is severely broken")
        return 1

if __name__ == "__main__":
    sys.exit(main())