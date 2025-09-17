#!/usr/bin/env python3
"""
Enhanced Chatbot System Test - Focus on PRD requirements
Tests ProfileAgent, PricingAgent integration and enhanced functionality
"""

import requests
import json
from datetime import datetime

class EnhancedChatbotTester:
    def __init__(self, base_url="https://ai-travel-planner-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"enhanced_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, data):
        """Run a single API test"""
        url = f"{self.api_url}/chat"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.tests_passed += 1
                print(f"✅ API Success - Status: {response.status_code}")
                return True, response.json()
            else:
                print(f"❌ API Failed - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, {}
                
        except Exception as e:
            print(f"❌ Request Failed - Error: {str(e)}")
            return False, {}

    def test_profile_intake_flow(self):
        """Test Profile Intake Flow - Priority Requirement 1"""
        print(f"\n👤 TESTING PROFILE INTAKE FLOW")
        
        # Test trip planning request triggers profile intake
        chat_data = {
            "message": "plan a trip to Kerala",
            "session_id": f"{self.session_id}_profile",
            "user_profile": {}
        }
        
        success, response = self.run_test("Profile Intake Trigger", chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            ui_actions = response.get('ui_actions', [])
            metadata = response.get('metadata', {})
            
            print(f"   📊 Analysis:")
            print(f"      Chat text: {chat_text[:100]}...")
            print(f"      UI actions: {len(ui_actions)}")
            print(f"      Intent: {metadata.get('intent', 'unknown')}")
            
            # Check for profile intake indicators
            profile_indicators = ['travel style', 'preference', 'adventure', 'culture', 'luxury', 'budget']
            profile_matches = sum(1 for indicator in profile_indicators if indicator.lower() in chat_text.lower())
            
            # Check for persona classification question chips
            persona_chips = [action for action in ui_actions 
                           if action.get('type') == 'question_chip' and 
                           any(persona in str(action).lower() for persona in ['adventure', 'culture', 'luxury', 'budget'])]
            
            print(f"      Profile indicators: {profile_matches}")
            print(f"      Persona question chips: {len(persona_chips)}")
            
            if profile_matches >= 1 and len(persona_chips) >= 2:
                print(f"   ✅ PROFILE INTAKE FLOW: WORKING")
                return True
            else:
                print(f"   ❌ PROFILE INTAKE FLOW: NOT TRIGGERED")
                return False
        
        return False

    def test_itinerary_variants_generation(self):
        """Test 3 Itinerary Variants Generation - Priority Requirement 2"""
        print(f"\n🗓️ TESTING ITINERARY VARIANTS GENERATION")
        
        # Mock completed profile for variant generation
        mock_profile = {
            "persona_classification": {
                "primary_persona": "cultural_explorer",
                "primary_confidence": 0.85
            },
            "structured_data": {
                "travel_style": ["culture", "adventure"],
                "budget_range": {"min": 50000, "max": 100000, "currency": "INR"}
            }
        }
        
        chat_data = {
            "message": "create my itinerary for Rajasthan",
            "session_id": f"{self.session_id}_variants",
            "user_profile": mock_profile,
            "trip_details": {
                "destination": "Rajasthan",
                "duration": "5 days"
            }
        }
        
        success, response = self.run_test("Itinerary Variants Generation", chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            ui_actions = response.get('ui_actions', [])
            metadata = response.get('metadata', {})
            
            print(f"   📊 Analysis:")
            print(f"      Chat text: {chat_text[:100]}...")
            print(f"      UI actions: {len(ui_actions)}")
            print(f"      Enhanced planning: {metadata.get('enhanced_planning', False)}")
            
            # Check for variant indicators
            variant_indicators = ['adventurer', 'balanced', 'luxury', 'variant', 'option']
            variant_matches = sum(1 for indicator in variant_indicators if indicator.lower() in chat_text.lower())
            
            # Check for itinerary-related UI actions
            itinerary_actions = [action for action in ui_actions 
                               if action.get('type') in ['itinerary_display', 'trip_planner_card']]
            
            print(f"      Variant indicators: {variant_matches}")
            print(f"      Itinerary actions: {len(itinerary_actions)}")
            print(f"      Variants generated: {metadata.get('variants_generated', 0)}")
            
            if variant_matches >= 2 or len(itinerary_actions) > 0 or metadata.get('variants_generated', 0) > 0:
                print(f"   ✅ ITINERARY VARIANTS: WORKING")
                return True
            else:
                print(f"   ❌ ITINERARY VARIANTS: NOT GENERATED")
                return False
        
        return False

    def test_dynamic_pricing(self):
        """Test Dynamic Pricing Integration - Priority Requirement 3"""
        print(f"\n💰 TESTING DYNAMIC PRICING")
        
        # Test pricing in accommodation request
        chat_data = {
            "message": "show me luxury hotels in Goa with pricing",
            "session_id": f"{self.session_id}_pricing",
            "user_profile": {
                "persona_classification": {
                    "primary_persona": "luxury_connoisseur"
                }
            }
        }
        
        success, response = self.run_test("Dynamic Pricing Integration", chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            ui_actions = response.get('ui_actions', [])
            
            print(f"   📊 Analysis:")
            print(f"      Chat text: {chat_text[:100]}...")
            print(f"      UI actions: {len(ui_actions)}")
            
            # Check for pricing indicators
            pricing_indicators = ['₹', 'price', 'cost', 'luxury', 'per night']
            pricing_matches = sum(1 for indicator in pricing_indicators if indicator in chat_text)
            
            # Check hotel cards with pricing
            hotel_cards = [action for action in ui_actions 
                          if action.get('type') == 'card_add' and 
                          action.get('payload', {}).get('category') == 'hotel']
            
            pricing_in_cards = sum(1 for card in hotel_cards 
                                 if card.get('payload', {}).get('price_estimate'))
            
            print(f"      Pricing indicators: {pricing_matches}")
            print(f"      Hotel cards with pricing: {pricing_in_cards}/{len(hotel_cards)}")
            
            if pricing_matches >= 2 and pricing_in_cards > 0:
                print(f"   ✅ DYNAMIC PRICING: WORKING")
                return True
            else:
                print(f"   ❌ DYNAMIC PRICING: NOT INTEGRATED")
                return False
        
        return False

    def test_agent_integration(self):
        """Test ProfileAgent and PricingAgent Integration - Priority Requirement 4"""
        print(f"\n🤖 TESTING AGENT INTEGRATION")
        
        # Test multiple agent coordination
        chat_data = {
            "message": "I love adventure and want a luxury trip to Himachal",
            "session_id": f"{self.session_id}_agents",
            "user_profile": {}
        }
        
        success, response = self.run_test("Agent Integration", chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            metadata = response.get('metadata', {})
            
            print(f"   📊 Analysis:")
            print(f"      Chat text: {chat_text[:100]}...")
            print(f"      Agent: {metadata.get('agent', 'unknown')}")
            print(f"      Enhanced planning: {metadata.get('enhanced_planning', False)}")
            
            # Check for agent integration indicators
            agent_indicators = ['profile', 'persona', 'adventure', 'luxury', 'preference']
            agent_matches = sum(1 for indicator in agent_indicators if indicator.lower() in chat_text.lower())
            
            print(f"      Agent integration indicators: {agent_matches}")
            
            if agent_matches >= 2 or metadata.get('enhanced_planning'):
                print(f"   ✅ AGENT INTEGRATION: WORKING")
                return True
            else:
                print(f"   ❌ AGENT INTEGRATION: LIMITED")
                return False
        
        return False

    def test_core_functionality(self):
        """Test Core Functionality Still Works - Priority Requirement 5"""
        print(f"\n🔧 TESTING CORE FUNCTIONALITY PRESERVATION")
        
        test_scenarios = [
            {
                "message": "tell me about Goa",
                "expected": "destination_info",
                "name": "Destination Info"
            },
            {
                "message": "hotels in Manali",
                "expected": "hotel_search", 
                "name": "Hotel Search"
            },
            {
                "message": "hello, how can you help?",
                "expected": "general_conversation",
                "name": "General Conversation"
            }
        ]
        
        core_passed = 0
        for i, scenario in enumerate(test_scenarios):
            chat_data = {
                "message": scenario["message"],
                "session_id": f"{self.session_id}_core_{i}",
                "user_profile": {}
            }
            
            success, response = self.run_test(scenario["name"], chat_data)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Check scenario-specific functionality
                if scenario["expected"] == "destination_info":
                    if 'goa' in chat_text.lower() or any(a.get('payload', {}).get('category') == 'destination' for a in ui_actions):
                        core_passed += 1
                        print(f"      ✅ {scenario['name']}: Working")
                    else:
                        print(f"      ❌ {scenario['name']}: Not working")
                
                elif scenario["expected"] == "hotel_search":
                    if 'hotel' in chat_text.lower() or any(a.get('payload', {}).get('category') == 'hotel' for a in ui_actions):
                        core_passed += 1
                        print(f"      ✅ {scenario['name']}: Working")
                    else:
                        print(f"      ❌ {scenario['name']}: Not working")
                
                elif scenario["expected"] == "general_conversation":
                    if len(chat_text) > 20 and any(word in chat_text.lower() for word in ['help', 'assist', 'travel']):
                        core_passed += 1
                        print(f"      ✅ {scenario['name']}: Working")
                    else:
                        print(f"      ❌ {scenario['name']}: Not working")
        
        print(f"   Core functionality: {core_passed}/{len(test_scenarios)} working")
        return core_passed >= 2

    def run_comprehensive_test(self):
        """Run all enhanced chatbot tests"""
        print(f"🚀 ENHANCED CHATBOT SYSTEM COMPREHENSIVE TEST")
        print(f"   Testing PRD requirements for demo at 12:30")
        print(f"   Session ID: {self.session_id}")
        
        # Run all priority tests
        profile_intake = self.test_profile_intake_flow()
        itinerary_variants = self.test_itinerary_variants_generation()
        dynamic_pricing = self.test_dynamic_pricing()
        agent_integration = self.test_agent_integration()
        core_functionality = self.test_core_functionality()
        
        # Calculate results
        priority_features = [profile_intake, itinerary_variants, dynamic_pricing, agent_integration, core_functionality]
        features_passed = sum(priority_features)
        
        print(f"\n🎯 ENHANCED CHATBOT SYSTEM RESULTS:")
        print(f"   Profile Intake Flow: {'✅ PASS' if profile_intake else '❌ FAIL'}")
        print(f"   Itinerary Variants Generation: {'✅ PASS' if itinerary_variants else '❌ FAIL'}")
        print(f"   Dynamic Pricing Integration: {'✅ PASS' if dynamic_pricing else '❌ FAIL'}")
        print(f"   Agent Integration: {'✅ PASS' if agent_integration else '❌ FAIL'}")
        print(f"   Core Functionality: {'✅ PASS' if core_functionality else '❌ FAIL'}")
        print(f"   Features Working: {features_passed}/5")
        
        # Demo readiness assessment
        demo_ready = features_passed >= 3
        print(f"\n🚀 DEMO READINESS: {'✅ READY' if demo_ready else '❌ NEEDS WORK'}")
        
        if demo_ready:
            print(f"   ✅ System ready for 12:30 demo!")
            print(f"   ✅ Enhanced chatbot features operational")
        else:
            print(f"   ❌ System needs attention before demo")
            print(f"   ❌ Check failed features above")
        
        print(f"\n📊 API Test Summary: {self.tests_passed}/{self.tests_run} API calls successful")
        
        return demo_ready

if __name__ == "__main__":
    tester = EnhancedChatbotTester()
    tester.run_comprehensive_test()