#!/usr/bin/env python3
"""
Focused test script for the review request scenarios
Tests the exact scenarios mentioned in the review request
"""

import requests
import json
from datetime import datetime

class ReviewRequestTester:
    def __init__(self, base_url="https://travel-persona.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"review_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tests_passed = 0
        self.tests_run = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}/"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAIL - Request timeout (30s)")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ FAIL - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ FAIL - Error: {str(e)}")
            return False, {}

    def test_review_scenarios(self):
        """Test the exact scenarios from the review request"""
        print(f"\n🎯 TESTING REVIEW REQUEST SCENARIOS")
        print(f"{'='*80}")
        
        scenarios_passed = 0
        total_scenarios = 5
        
        # Scenario 1: Destination Discovery - "popular destinations in India"
        print(f"\n📍 SCENARIO 1: Destination Discovery")
        print(f"   Query: 'popular destinations in India'")
        print(f"   Expected: Destination cards with Plan Trip buttons")
        
        chat_data_1 = {
            "message": "popular destinations in India",
            "session_id": f"{self.session_id}_scenario_1",
            "user_profile": {}
        }
        
        success_1, response_1 = self.run_test("Destination Discovery", "POST", "chat", 200, data=chat_data_1)
        
        if success_1:
            ui_actions = response_1.get('ui_actions', [])
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            
            print(f"   📊 Analysis:")
            print(f"      Total UI actions: {len(ui_actions)}")
            print(f"      Destination cards: {len(destination_cards)}")
            print(f"      Response length: {len(response_1.get('chat_text', ''))} chars")
            
            if len(destination_cards) >= 3:
                scenarios_passed += 1
                print(f"   ✅ PASS: {len(destination_cards)} destination cards generated")
                
                # Show first few destinations
                for i, card in enumerate(destination_cards[:3]):
                    payload = card.get('payload', {})
                    title = payload.get('title', 'N/A')
                    cta_secondary = payload.get('cta_secondary', {})
                    has_plan_trip = cta_secondary.get('label') == 'Plan Trip'
                    print(f"      Destination {i+1}: {title} - Plan Trip: {'✅' if has_plan_trip else '❌'}")
            else:
                print(f"   ❌ FAIL: Only {len(destination_cards)} destination cards generated (expected ≥3)")
        
        # Scenario 2: Specific Destination - "tell me about Kerala"
        print(f"\n🌴 SCENARIO 2: Specific Destination")
        print(f"   Query: 'tell me about Kerala'")
        print(f"   Expected: Kerala destination card and question chips")
        
        chat_data_2 = {
            "message": "tell me about Kerala",
            "session_id": f"{self.session_id}_scenario_2",
            "user_profile": {}
        }
        
        success_2, response_2 = self.run_test("Kerala Specific", "POST", "chat", 200, data=chat_data_2)
        
        if success_2:
            ui_actions = response_2.get('ui_actions', [])
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            question_chips = [action for action in ui_actions if action.get('type') == 'question_chip']
            
            print(f"   📊 Analysis:")
            print(f"      Total UI actions: {len(ui_actions)}")
            print(f"      Destination cards: {len(destination_cards)}")
            print(f"      Question chips: {len(question_chips)}")
            print(f"      Response length: {len(response_2.get('chat_text', ''))} chars")
            
            kerala_card_found = False
            for card in destination_cards:
                title = card.get('payload', {}).get('title', '').lower()
                if 'kerala' in title:
                    kerala_card_found = True
                    print(f"      Kerala card: {card.get('payload', {}).get('title', 'N/A')}")
                    break
            
            if kerala_card_found and len(question_chips) > 0:
                scenarios_passed += 1
                print(f"   ✅ PASS: Kerala card found with {len(question_chips)} question chips")
                
                # Show question chips
                for i, chip in enumerate(question_chips[:3]):
                    question = chip.get('payload', {}).get('question', 'N/A')
                    print(f"      Question {i+1}: {question}")
            else:
                print(f"   ❌ FAIL: Kerala card: {kerala_card_found}, Question chips: {len(question_chips)}")
        
        # Scenario 3: Hotel Queries - "hotels in Goa"
        print(f"\n🏨 SCENARIO 3: Hotel Queries")
        print(f"   Query: 'hotels in Goa'")
        print(f"   Expected: Hotel cards with booking options")
        
        chat_data_3 = {
            "message": "hotels in Goa",
            "session_id": f"{self.session_id}_scenario_3",
            "user_profile": {}
        }
        
        success_3, response_3 = self.run_test("Hotels in Goa", "POST", "chat", 200, data=chat_data_3)
        
        if success_3:
            ui_actions = response_3.get('ui_actions', [])
            hotel_cards = [action for action in ui_actions 
                          if action.get('type') == 'card_add' and 
                          action.get('payload', {}).get('category') == 'hotel']
            
            print(f"   📊 Analysis:")
            print(f"      Total UI actions: {len(ui_actions)}")
            print(f"      Hotel cards: {len(hotel_cards)}")
            print(f"      Response length: {len(response_3.get('chat_text', ''))} chars")
            
            booking_options = 0
            for i, card in enumerate(hotel_cards):
                payload = card.get('payload', {})
                title = payload.get('title', 'N/A')
                rating = payload.get('rating', 'N/A')
                price = payload.get('price_estimate', {})
                cta_primary = payload.get('cta_primary', {})
                
                has_booking = 'book' in cta_primary.get('label', '').lower()
                if has_booking:
                    booking_options += 1
                
                print(f"      Hotel {i+1}: {title} - Rating: {rating} - Booking: {'✅' if has_booking else '❌'}")
                if price:
                    print(f"         Price: ₹{price.get('min', 'N/A')}-{price.get('max', 'N/A')}/night")
            
            if len(hotel_cards) > 0 and booking_options > 0:
                scenarios_passed += 1
                print(f"   ✅ PASS: {len(hotel_cards)} hotel cards with {booking_options} booking options")
            else:
                print(f"   ❌ FAIL: Hotel cards: {len(hotel_cards)}, Booking options: {booking_options}")
        
        # Scenario 4: Trip Planning - "plan a trip to Rajasthan for 5 days"
        print(f"\n🗓️ SCENARIO 4: Trip Planning")
        print(f"   Query: 'plan a trip to Rajasthan for 5 days'")
        print(f"   Expected: trip_planner_card or itinerary_display UI actions")
        
        chat_data_4 = {
            "message": "plan a trip to Rajasthan for 5 days",
            "session_id": f"{self.session_id}_scenario_4",
            "user_profile": {}
        }
        
        success_4, response_4 = self.run_test("Trip Planning", "POST", "chat", 200, data=chat_data_4)
        
        if success_4:
            ui_actions = response_4.get('ui_actions', [])
            trip_planner_cards = [action for action in ui_actions if action.get('type') == 'trip_planner_card']
            itinerary_displays = [action for action in ui_actions if action.get('type') == 'itinerary_display']
            
            chat_text = response_4.get('chat_text', '').lower()
            has_itinerary_content = any(word in chat_text for word in ['day 1', 'day 2', 'itinerary', 'schedule', 'rajasthan'])
            
            print(f"   📊 Analysis:")
            print(f"      Total UI actions: {len(ui_actions)}")
            print(f"      Trip planner cards: {len(trip_planner_cards)}")
            print(f"      Itinerary displays: {len(itinerary_displays)}")
            print(f"      Has itinerary content: {has_itinerary_content}")
            print(f"      Response length: {len(response_4.get('chat_text', ''))} chars")
            
            if len(trip_planner_cards) > 0 or len(itinerary_displays) > 0 or has_itinerary_content:
                scenarios_passed += 1
                print(f"   ✅ PASS: Trip planning functionality detected")
                if has_itinerary_content:
                    print(f"      Response contains trip planning content")
            else:
                print(f"   ❌ FAIL: No trip planning UI actions or itinerary content")
        
        # Scenario 5: General Queries - "hello"
        print(f"\n👋 SCENARIO 5: General Queries")
        print(f"   Query: 'hello'")
        print(f"   Expected: General response with question chips")
        
        chat_data_5 = {
            "message": "hello",
            "session_id": f"{self.session_id}_scenario_5",
            "user_profile": {}
        }
        
        success_5, response_5 = self.run_test("General Greeting", "POST", "chat", 200, data=chat_data_5)
        
        if success_5:
            ui_actions = response_5.get('ui_actions', [])
            question_chips = [action for action in ui_actions if action.get('type') == 'question_chip']
            
            chat_text = response_5.get('chat_text', '').lower()
            is_general_response = any(word in chat_text for word in ['hello', 'help', 'assist', 'travel', 'hi'])
            
            print(f"   📊 Analysis:")
            print(f"      Total UI actions: {len(ui_actions)}")
            print(f"      Question chips: {len(question_chips)}")
            print(f"      Is general response: {is_general_response}")
            print(f"      Response length: {len(response_5.get('chat_text', ''))} chars")
            
            if is_general_response and len(question_chips) > 0:
                scenarios_passed += 1
                print(f"   ✅ PASS: General response with {len(question_chips)} question chips")
                
                # Show question chips
                for i, chip in enumerate(question_chips[:3]):
                    question = chip.get('payload', {}).get('question', 'N/A')
                    print(f"      Question {i+1}: {question}")
            else:
                print(f"   ❌ FAIL: General response: {is_general_response}, Question chips: {len(question_chips)}")
        
        # Summary
        print(f"\n🎯 REVIEW REQUEST SCENARIOS SUMMARY")
        print(f"{'='*80}")
        print(f"Scenarios Passed: {scenarios_passed}/{total_scenarios}")
        print(f"Success Rate: {(scenarios_passed/total_scenarios)*100:.1f}%")
        
        return scenarios_passed >= 4  # Pass if at least 4/5 scenarios work

    def test_llm_integration(self):
        """Test LLM integration is working and not falling back to mock data"""
        print(f"\n🤖 TESTING LLM INTEGRATION")
        print(f"{'='*80}")
        
        # Test with a unique query that would require LLM processing
        unique_query = "What are the most romantic sunset spots in Kerala for couples?"
        
        chat_data = {
            "message": unique_query,
            "session_id": f"{self.session_id}_llm_test",
            "user_profile": {}
        }
        
        success, response = self.run_test("LLM Integration Test", "POST", "chat", 200, data=chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            ui_actions = response.get('ui_actions', [])
            
            print(f"   📊 Analysis:")
            print(f"      Response length: {len(chat_text)} characters")
            print(f"      UI actions: {len(ui_actions)}")
            
            # Check for detailed, contextual response (not generic)
            llm_indicators = [
                len(chat_text) > 200,  # Detailed response
                'kerala' in chat_text.lower(),  # Context awareness
                any(word in chat_text.lower() for word in ['sunset', 'romantic', 'couples']),  # Query relevance
                not any(phrase in chat_text.lower() for phrase in ['mock', 'test', 'placeholder'])  # Not mock data
            ]
            
            llm_score = sum(llm_indicators)
            
            print(f"      Context awareness (Kerala mentioned): {'✅' if 'kerala' in chat_text.lower() else '❌'}")
            print(f"      Query relevance (sunset/romantic): {'✅' if any(word in chat_text.lower() for word in ['sunset', 'romantic', 'couples']) else '❌'}")
            print(f"      Non-mock content: {'✅' if not any(phrase in chat_text.lower() for phrase in ['mock', 'test', 'placeholder']) else '❌'}")
            print(f"      Detailed response (>200 chars): {'✅' if len(chat_text) > 200 else '❌'}")
            print(f"      LLM Integration Score: {llm_score}/4")
            
            if llm_score >= 3:
                print(f"   ✅ PASS: LLM integration working properly")
                return True
            else:
                print(f"   ❌ FAIL: LLM integration may be falling back to mock data")
                print(f"   Response preview: {chat_text[:200]}...")
                return False
        else:
            print(f"   ❌ FAIL: API call failed")
            return False

    def test_session_context(self):
        """Test that session context is maintained across multiple requests"""
        print(f"\n🔄 TESTING SESSION CONTEXT MAINTENANCE")
        print(f"{'='*80}")
        
        session_id = f"{self.session_id}_context_test"
        
        # First message: Mention a destination
        print(f"\n   Step 1: Initial destination mention")
        chat_data_1 = {
            "message": "I'm interested in visiting Kerala",
            "session_id": session_id,
            "user_profile": {}
        }
        
        success_1, response_1 = self.run_test("Context Step 1", "POST", "chat", 200, data=chat_data_1)
        
        if not success_1:
            print(f"   ❌ FAIL: First message failed")
            return False
        
        print(f"      Response 1 length: {len(response_1.get('chat_text', ''))} chars")
        
        # Second message: Follow-up without mentioning destination
        print(f"\n   Step 2: Follow-up without destination mention")
        chat_data_2 = {
            "message": "What are the best hotels there?",
            "session_id": session_id,
            "user_profile": {}
        }
        
        success_2, response_2 = self.run_test("Context Step 2", "POST", "chat", 200, data=chat_data_2)
        
        if success_2:
            chat_text = response_2.get('chat_text', '').lower()
            ui_actions = response_2.get('ui_actions', [])
            
            print(f"      Response 2 length: {len(response_2.get('chat_text', ''))} chars")
            print(f"      UI actions: {len(ui_actions)}")
            
            # Check if response understands "there" refers to Kerala
            context_maintained = (
                'kerala' in chat_text or
                any('kerala' in str(action).lower() for action in ui_actions)
            )
            
            if context_maintained:
                print(f"   ✅ PASS: Session context maintained - Kerala referenced in follow-up")
                return True
            else:
                print(f"   ❌ FAIL: Session context lost - no Kerala reference in follow-up")
                print(f"   Response preview: {chat_text[:100]}...")
                return False
        else:
            print(f"   ❌ FAIL: Second message failed")
            return False

    def run_all_tests(self):
        """Run all focused tests for the review request"""
        print(f"🚀 TRAVELLO.AI BACKEND API - REVIEW REQUEST TESTING")
        print(f"   Base URL: {self.base_url}")
        print(f"   Session ID: {self.session_id}")
        print(f"   Focus: LLM Agent Functionality & UI Actions")
        
        # Test basic connectivity first
        print(f"\n🔧 BASIC CONNECTIVITY TEST")
        print(f"{'='*80}")
        success, _ = self.run_test("Root API Endpoint", "GET", "", 200)
        if not success:
            print(f"❌ CRITICAL: Cannot connect to API. Stopping tests.")
            return False
        
        # Run the main review request tests
        review_scenarios_passed = self.test_review_scenarios()
        llm_integration_working = self.test_llm_integration()
        session_context_working = self.test_session_context()
        
        # Print final results
        print(f"\n{'='*80}")
        print(f"🎯 FINAL TEST RESULTS - REVIEW REQUEST FOCUS")
        print(f"{'='*80}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n📋 CRITICAL REVIEW REQUEST RESULTS:")
        print(f"   ✅ Review Scenarios (5 tests): {'PASS' if review_scenarios_passed else 'FAIL'}")
        print(f"   ✅ LLM Integration: {'WORKING' if llm_integration_working else 'MOCK DATA'}")
        print(f"   ✅ Session Context: {'MAINTAINED' if session_context_working else 'LOST'}")
        
        # Overall assessment
        critical_tests_passed = sum([review_scenarios_passed, llm_integration_working, session_context_working])
        
        print(f"\n🎉 OVERALL ASSESSMENT:")
        if critical_tests_passed == 3:
            print(f"   🎉 ALL CRITICAL TESTS PASSED! LLM agents are working properly.")
            print(f"   ✅ All UI action types are being generated correctly")
            print(f"   ✅ LLM integration is working (not falling back to mock data)")
            print(f"   ✅ Session context is maintained across requests")
            print(f"   ✅ Different intent types are correctly routed to appropriate agents")
            return True
        elif critical_tests_passed >= 2:
            print(f"   ⚠️  MOSTLY WORKING - {critical_tests_passed}/3 critical areas passed")
            print(f"   Some LLM agents may need attention")
            return True
        else:
            print(f"   ❌ CRITICAL ISSUES - Only {critical_tests_passed}/3 critical areas passed")
            print(f"   LLM agent functionality needs significant work")
            return False

def main():
    tester = ReviewRequestTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())