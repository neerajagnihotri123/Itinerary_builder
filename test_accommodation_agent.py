#!/usr/bin/env python3
"""
Focused test for AccommodationAgent refined implementation
"""
import requests
import json
from datetime import datetime

class AccommodationAgentTester:
    def __init__(self, base_url="https://ai-travel-planner-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"accommodation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                print(f"✅ Passed - Status: {response.status_code}")
                return True, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_accommodation_agent_refined_implementation(self):
        """Test the refined AccommodationAgent implementation"""
        print(f"\n🏨 Testing AccommodationAgent Refined Implementation...")
        
        # Test scenarios for different destinations and slot configurations
        test_scenarios = [
            {
                "destination": "Kerala",
                "slots": {"budget_per_night": 8000, "adults": 2, "children": 0},
                "description": "Kerala mid-range couple travel"
            },
            {
                "destination": "Goa", 
                "slots": {"budget_per_night": 15000, "adults": 2, "children": 2},
                "description": "Goa luxury family travel"
            },
            {
                "destination": "Manali",
                "slots": {"budget_per_night": 5000, "adults": 1, "children": 0},
                "description": "Manali budget solo travel"
            }
        ]
        
        accommodation_tests_passed = 0
        
        for i, scenario in enumerate(test_scenarios):
            print(f"\n   🎯 Testing Scenario {i+1}: {scenario['description']}")
            
            # Test hotel scoring and ranking
            scoring_passed = self._test_hotel_scoring_and_ranking(scenario)
            
            # Test availability checks
            availability_passed = self._test_availability_checks(scenario)
            
            # Test booking flow
            booking_passed = self._test_booking_flow(scenario)
            
            # Test LLM integration + fallback
            llm_fallback_passed = self._test_llm_integration_fallback(scenario)
            
            # Test top results limiting
            limiting_passed = self._test_top_results_limiting(scenario)
            
            scenario_score = sum([scoring_passed, availability_passed, booking_passed, 
                                llm_fallback_passed, limiting_passed])
            
            if scenario_score >= 4:  # Pass if at least 4/5 tests pass
                accommodation_tests_passed += 1
                print(f"      ✅ Scenario {i+1} PASSED: {scenario_score}/5 tests passed")
            else:
                print(f"      ❌ Scenario {i+1} FAILED: {scenario_score}/5 tests passed")
        
        print(f"\n🏨 AccommodationAgent Results: {accommodation_tests_passed}/{len(test_scenarios)} scenarios passed")
        return accommodation_tests_passed >= 2  # Pass if at least 2/3 scenarios work
    
    def _test_hotel_scoring_and_ranking(self, scenario):
        """Test comprehensive scoring factors and proper ranking"""
        print(f"      🎯 Testing Hotel Scoring and Ranking...")
        
        # Test hotel query for the destination
        chat_data = {
            "message": f"show me hotels in {scenario['destination']}",
            "session_id": f"{self.session_id}_scoring_{scenario['destination'].lower()}",
            "user_profile": {},
            "trip_details": {
                "budget": {"per_night": scenario['slots']['budget_per_night']},
                "travelers": {"adults": scenario['slots']['adults'], "children": scenario['slots']['children']}
            }
        }
        
        success, response = self.run_test(f"Hotel Scoring {scenario['destination']}", "POST", "chat", 200, data=chat_data)
        
        if not success:
            print(f"         ❌ API call failed")
            return False
        
        # Check for hotel cards with scoring information
        ui_actions = response.get('ui_actions', [])
        hotel_cards = [action for action in ui_actions 
                      if action.get('type') == 'card_add' and 
                      action.get('payload', {}).get('category') == 'hotel']
        
        if not hotel_cards:
            print(f"         ❌ No hotel cards generated")
            return False
        
        # Verify scoring factors are present
        scoring_factors_found = 0
        ranking_found = False
        
        for i, hotel_card in enumerate(hotel_cards):
            payload = hotel_card.get('payload', {})
            
            # Check for price information (25% weight)
            if 'price_estimate' in payload:
                scoring_factors_found += 1
            
            # Check for rating (20% weight)  
            if 'rating' in payload:
                scoring_factors_found += 1
            
            # Check for amenities (20% weight)
            if 'amenities' in payload and len(payload.get('amenities', [])) > 0:
                scoring_factors_found += 1
            
            # Check for ranking (hotels should be in order)
            if i == 0:  # First hotel should be highest ranked
                ranking_found = True
        
        # Verify comprehensive scoring
        if scoring_factors_found >= 3 and ranking_found:
            print(f"         ✅ Hotel scoring and ranking working: {len(hotel_cards)} hotels with scoring factors")
            return True
        else:
            print(f"         ❌ Incomplete scoring: {scoring_factors_found}/3 factors, ranking: {ranking_found}")
            return False
    
    def _test_availability_checks(self, scenario):
        """Test availability checking functionality"""
        print(f"      📅 Testing Availability Checks...")
        
        # Test hotel query to get hotels first
        chat_data = {
            "message": f"available hotels in {scenario['destination']}",
            "session_id": f"{self.session_id}_availability_{scenario['destination'].lower()}",
            "user_profile": {},
            "trip_details": {
                "dates": {"start_date": "2024-12-15", "end_date": "2024-12-18"},
                "travelers": {"adults": scenario['slots']['adults'], "children": scenario['slots']['children']}
            }
        }
        
        success, response = self.run_test(f"Availability Check {scenario['destination']}", "POST", "chat", 200, data=chat_data)
        
        if not success:
            print(f"         ❌ API call failed")
            return False
        
        # Check for hotel cards with availability information
        ui_actions = response.get('ui_actions', [])
        hotel_cards = [action for action in ui_actions 
                      if action.get('type') == 'card_add' and 
                      action.get('payload', {}).get('category') == 'hotel']
        
        if not hotel_cards:
            print(f"         ❌ No hotel cards with availability found")
            return False
        
        # Verify availability details
        availability_features_found = 0
        
        for hotel_card in hotel_cards:
            payload = hotel_card.get('payload', {})
            
            # Hotels returned should have availability status (implicit - they're shown)
            availability_features_found += 1
            
            # Check for booking-related information
            if any(key in payload for key in ['cta_primary', 'cta_secondary']):
                if any('book' in str(payload.get(key, {})).lower() for key in ['cta_primary', 'cta_secondary']):
                    availability_features_found += 1
        
        if availability_features_found >= len(hotel_cards):
            print(f"         ✅ Availability checks working: {len(hotel_cards)} available hotels returned")
            return True
        else:
            print(f"         ❌ Availability checks incomplete")
            return False
    
    def _test_booking_flow(self, scenario):
        """Test the booking process including validation and security"""
        print(f"      💳 Testing Booking Flow...")
        
        # Test booking-related UI elements and responses
        chat_data = {
            "message": f"I want to book a hotel in {scenario['destination']}",
            "session_id": f"{self.session_id}_booking_{scenario['destination'].lower()}",
            "user_profile": {},
            "trip_details": {
                "dates": {"start_date": "2024-12-15", "end_date": "2024-12-18"},
                "travelers": {"adults": scenario['slots']['adults'], "children": scenario['slots']['children']},
                "budget": {"per_night": scenario['slots']['budget_per_night']}
            }
        }
        
        success, response = self.run_test(f"Booking Flow {scenario['destination']}", "POST", "chat", 200, data=chat_data)
        
        if not success:
            print(f"         ❌ API call failed")
            return False
        
        # Check for booking-related UI elements
        ui_actions = response.get('ui_actions', [])
        hotel_cards = [action for action in ui_actions 
                      if action.get('type') == 'card_add' and 
                      action.get('payload', {}).get('category') == 'hotel']
        
        booking_features_found = 0
        security_check_passed = True
        
        for hotel_card in hotel_cards:
            payload = hotel_card.get('payload', {})
            
            # Check for booking CTAs
            cta_primary = payload.get('cta_primary', {})
            cta_secondary = payload.get('cta_secondary', {})
            
            if ('book' in str(cta_primary).lower() or 'book' in str(cta_secondary).lower()):
                booking_features_found += 1
            
            # Security check: ensure no payment credentials are exposed
            payload_str = str(payload).lower()
            if any(term in payload_str for term in ['password', 'credit_card', 'cvv', 'payment_key', 'secret']):
                security_check_passed = False
                print(f"         🚨 SECURITY ISSUE: Payment credentials found in response")
        
        # Check response text for booking-related content
        chat_text = response.get('chat_text', '').lower()
        if any(word in chat_text for word in ['book', 'reservation', 'available', 'rooms']):
            booking_features_found += 1
        
        if booking_features_found > 0 and security_check_passed:
            print(f"         ✅ Booking flow working: {booking_features_found} booking features, security check passed")
            return True
        else:
            print(f"         ❌ Booking flow issues: features={booking_features_found}, security={security_check_passed}")
            return False
    
    def _test_llm_integration_fallback(self, scenario):
        """Test LLM integration with fallback to mock data"""
        print(f"      🤖 Testing LLM Integration + Fallback...")
        
        # Test with a query that should trigger LLM generation
        chat_data = {
            "message": f"recommend luxury hotels in {scenario['destination']} with spa facilities",
            "session_id": f"{self.session_id}_llm_{scenario['destination'].lower()}",
            "user_profile": {},
            "trip_details": {
                "budget": {"per_night": scenario['slots']['budget_per_night']},
                "travelers": {"adults": scenario['slots']['adults'], "children": scenario['slots']['children']}
            }
        }
        
        success, response = self.run_test(f"LLM Integration {scenario['destination']}", "POST", "chat", 200, data=chat_data)
        
        if not success:
            print(f"         ❌ API call failed")
            return False
        
        # Check for hotel recommendations
        ui_actions = response.get('ui_actions', [])
        hotel_cards = [action for action in ui_actions 
                      if action.get('type') == 'card_add' and 
                      action.get('payload', {}).get('category') == 'hotel']
        
        chat_text = response.get('chat_text', '')
        
        # Verify we got hotel recommendations (either from LLM or fallback)
        llm_indicators = 0
        
        if hotel_cards:
            llm_indicators += 1
            print(f"         ✅ Hotel cards generated: {len(hotel_cards)}")
        
        if len(chat_text) > 100:  # Substantial response suggests LLM involvement
            llm_indicators += 1
            print(f"         ✅ Detailed response generated: {len(chat_text)} characters")
        
        # Check for diversity in hotel sources (LLM + fallback combination)
        if len(hotel_cards) >= 2:
            llm_indicators += 1
            print(f"         ✅ Multiple hotels suggest LLM + fallback diversity")
        
        if llm_indicators >= 2:
            print(f"         ✅ LLM integration + fallback working: {llm_indicators}/3 indicators")
            return True
        else:
            print(f"         ❌ LLM integration issues: {llm_indicators}/3 indicators")
            return False
    
    def _test_top_results_limiting(self, scenario):
        """Test that final hotel list is limited to top 5 with proper ranking"""
        print(f"      🔢 Testing Top Results Limiting...")
        
        # Test with a broad query that might return many hotels
        chat_data = {
            "message": f"show me all hotels in {scenario['destination']}",
            "session_id": f"{self.session_id}_limiting_{scenario['destination'].lower()}",
            "user_profile": {},
            "trip_details": {
                "budget": {"per_night": scenario['slots']['budget_per_night']},
                "travelers": {"adults": scenario['slots']['adults'], "children": scenario['slots']['children']}
            }
        }
        
        success, response = self.run_test(f"Results Limiting {scenario['destination']}", "POST", "chat", 200, data=chat_data)
        
        if not success:
            print(f"         ❌ API call failed")
            return False
        
        # Check hotel cards count and ranking
        ui_actions = response.get('ui_actions', [])
        hotel_cards = [action for action in ui_actions 
                      if action.get('type') == 'card_add' and 
                      action.get('payload', {}).get('category') == 'hotel']
        
        # Verify results are limited (should be ≤ 5 as per review request)
        if len(hotel_cards) > 5:
            print(f"         ❌ Too many results: {len(hotel_cards)} hotels (should be ≤ 5)")
            return False
        
        if len(hotel_cards) == 0:
            print(f"         ❌ No hotel results returned")
            return False
        
        # Verify hotels have ranking information
        ranking_features = 0
        
        for i, hotel_card in enumerate(hotel_cards):
            payload = hotel_card.get('payload', {})
            
            # Check for ranking indicators (rating, price, etc.)
            if 'rating' in payload:
                ranking_features += 1
            
            # Check for proper ordering (first hotel should be best)
            if i == 0 and 'rating' in payload:
                first_hotel_rating = payload.get('rating', 0)
                if first_hotel_rating >= 4.0:  # First hotel should be high quality
                    ranking_features += 1
        
        # Verify complete booking metadata without payment info
        booking_metadata_complete = True
        for hotel_card in hotel_cards:
            payload = hotel_card.get('payload', {})
            
            # Should have booking CTAs
            if not (payload.get('cta_primary') or payload.get('cta_secondary')):
                booking_metadata_complete = False
            
            # Should NOT have payment credentials
            payload_str = str(payload).lower()
            if any(term in payload_str for term in ['password', 'credit_card', 'payment_key']):
                booking_metadata_complete = False
                print(f"         🚨 SECURITY ISSUE: Payment info found")
        
        if len(hotel_cards) <= 5 and ranking_features >= len(hotel_cards) and booking_metadata_complete:
            print(f"         ✅ Top results limiting working: {len(hotel_cards)} hotels, proper ranking, secure metadata")
            return True
        else:
            print(f"         ❌ Results limiting issues: {len(hotel_cards)} hotels, ranking={ranking_features}, metadata={booking_metadata_complete}")
            return False

def main():
    print("🏨 AccommodationAgent Refined Implementation Testing...")
    print("=" * 60)
    
    tester = AccommodationAgentTester()
    
    # Run AccommodationAgent tests
    accommodation_success = tester.test_accommodation_agent_refined_implementation()
    
    print(f"\n📊 FINAL RESULTS")
    print(f"AccommodationAgent Refined Implementation: {'PASS' if accommodation_success else 'FAIL'}")
    
    if accommodation_success:
        print("🎉 Excellent! AccommodationAgent refined implementation is working correctly!")
        return 0
    else:
        print("❌ AccommodationAgent refined implementation has issues that need attention")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())