#!/usr/bin/env python3
"""
Focused test for RetrievalAgent implementation
"""
import requests
import json
from datetime import datetime

class RetrievalAgentTester:
    def __init__(self, base_url="https://travello-agents.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"retrieval_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.tests_run = 0
        self.tests_passed = 0

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
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_retrieval_agent_facts_retrieval(self):
        """Test RetrievalAgent facts retrieval for various destinations"""
        print(f"\n🔍 Testing RetrievalAgent Facts Retrieval...")
        
        destinations = ["Kerala", "Goa", "Manali", "Rishikesh", "Andaman"]
        results = {}
        
        for destination in destinations:
            print(f"\n   🎯 Testing {destination}...")
            
            chat_data = {
                "message": f"tell me about {destination}",
                "session_id": f"{self.session_id}_{destination.lower()}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Facts for {destination}", "POST", "chat", 200, data=chat_data)
            
            if success:
                # Analyze response
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Count different types of facts
                destination_cards = [action for action in ui_actions 
                                   if action.get('type') == 'card_add' and 
                                   action.get('payload', {}).get('category') == 'destination']
                
                question_chips = [action for action in ui_actions 
                                 if action.get('type') == 'question_chip']
                
                # Check for destination-specific content
                has_destination_info = destination.lower() in chat_text.lower()
                has_comprehensive_response = len(chat_text) > 100
                
                results[destination] = {
                    'success': True,
                    'response_length': len(chat_text),
                    'destination_cards': len(destination_cards),
                    'question_chips': len(question_chips),
                    'total_ui_actions': len(ui_actions),
                    'has_destination_info': has_destination_info,
                    'has_comprehensive_response': has_comprehensive_response,
                    'within_limit': len(ui_actions) <= 20
                }
                
                print(f"      ✅ Response length: {len(chat_text)} chars")
                print(f"      ✅ Destination cards: {len(destination_cards)}")
                print(f"      ✅ Question chips: {len(question_chips)}")
                print(f"      ✅ Total UI actions: {len(ui_actions)}")
                print(f"      ✅ Has destination info: {has_destination_info}")
                print(f"      ✅ Within top-20 limit: {len(ui_actions) <= 20}")
                
            else:
                results[destination] = {'success': False}
        
        return results

    def test_retrieval_agent_hotel_facts(self):
        """Test RetrievalAgent hotel facts retrieval"""
        print(f"\n🏨 Testing RetrievalAgent Hotel Facts...")
        
        destinations = ["Kerala", "Goa", "Andaman"]
        results = {}
        
        for destination in destinations:
            print(f"\n   🏨 Testing hotels in {destination}...")
            
            chat_data = {
                "message": f"show me hotels in {destination}",
                "session_id": f"{self.session_id}_hotels_{destination.lower()}",
                "user_profile": {}
            }
            
            success, response = self.run_test(f"Hotels in {destination}", "POST", "chat", 200, data=chat_data)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                hotel_cards = [action for action in ui_actions 
                              if action.get('type') == 'card_add' and 
                              action.get('payload', {}).get('category') == 'hotel']
                
                # Check metadata in hotel cards
                metadata_complete = 0
                total_checks = 0
                
                for hotel_card in hotel_cards:
                    payload = hotel_card.get('payload', {})
                    required_fields = ['rating', 'price_estimate', 'amenities', 'title']
                    
                    for field in required_fields:
                        total_checks += 1
                        if field in payload and payload[field] is not None:
                            metadata_complete += 1
                
                metadata_score = metadata_complete / total_checks if total_checks > 0 else 0
                
                results[destination] = {
                    'success': True,
                    'hotel_cards': len(hotel_cards),
                    'metadata_score': metadata_score,
                    'total_ui_actions': len(ui_actions)
                }
                
                print(f"      ✅ Hotel cards: {len(hotel_cards)}")
                print(f"      ✅ Metadata completeness: {metadata_score:.2f}")
                
                # Show sample hotel details
                if hotel_cards:
                    sample_hotel = hotel_cards[0].get('payload', {})
                    print(f"      ✅ Sample hotel: {sample_hotel.get('title', 'N/A')}")
                    print(f"         Rating: {sample_hotel.get('rating', 'N/A')}")
                    price_est = sample_hotel.get('price_estimate', {})
                    if isinstance(price_est, dict):
                        print(f"         Price: ₹{price_est.get('min', 'N/A')}-{price_est.get('max', 'N/A')}/night")
                    else:
                        print(f"         Price: {price_est}")
                
            else:
                results[destination] = {'success': False}
        
        return results

    def test_retrieval_agent_no_facts_response(self):
        """Test RetrievalAgent behavior when no facts found"""
        print(f"\n❌ Testing No Facts Response...")
        
        chat_data = {
            "message": "tell me about XYZ Unknown Destination",
            "session_id": f"{self.session_id}_no_facts",
            "user_profile": {}
        }
        
        success, response = self.run_test("No Facts Response", "POST", "chat", 200, data=chat_data)
        
        if success:
            chat_text = response.get('chat_text', '').lower()
            ui_actions = response.get('ui_actions', [])
            
            # Check for helpful response
            helpful_words = ['sorry', 'unknown', 'help', 'suggest', 'try', 'alternative']
            has_helpful_response = any(word in chat_text for word in helpful_words)
            
            # Check for suggestions
            has_suggestions = len(ui_actions) > 0 or any(word in chat_text for word in ['recommend', 'popular', 'consider'])
            
            print(f"      ✅ Response length: {len(response.get('chat_text', ''))} chars")
            print(f"      ✅ Has helpful response: {has_helpful_response}")
            print(f"      ✅ Has suggestions: {has_suggestions}")
            print(f"      ✅ UI actions: {len(ui_actions)}")
            
            return {
                'success': True,
                'has_helpful_response': has_helpful_response,
                'has_suggestions': has_suggestions,
                'ui_actions': len(ui_actions)
            }
        
        return {'success': False}

    def test_retrieval_agent_llm_integration(self):
        """Test LLM integration vs fallback"""
        print(f"\n🤖 Testing LLM Integration vs Fallback...")
        
        chat_data = {
            "message": "show me everything about Kerala - culture, food, places, activities",
            "session_id": f"{self.session_id}_llm_test",
            "user_profile": {}
        }
        
        success, response = self.run_test("LLM Integration", "POST", "chat", 200, data=chat_data)
        
        if success:
            chat_text = response.get('chat_text', '')
            ui_actions = response.get('ui_actions', [])
            
            # Check for detailed LLM-style response
            has_detailed_response = len(chat_text) > 300
            has_kerala_specifics = any(word in chat_text.lower() for word in [
                'kerala', 'backwater', 'god', 'country', 'spice', 'ayurveda', 'coconut'
            ])
            
            # Check for system integration
            has_ui_integration = len(ui_actions) > 0
            
            destination_cards = [action for action in ui_actions 
                               if action.get('type') == 'card_add' and 
                               action.get('payload', {}).get('category') == 'destination']
            
            question_chips = [action for action in ui_actions 
                             if action.get('type') == 'question_chip']
            
            print(f"      ✅ Response length: {len(chat_text)} chars")
            print(f"      ✅ Has detailed response: {has_detailed_response}")
            print(f"      ✅ Has Kerala specifics: {has_kerala_specifics}")
            print(f"      ✅ Has UI integration: {has_ui_integration}")
            print(f"      ✅ Destination cards: {len(destination_cards)}")
            print(f"      ✅ Question chips: {len(question_chips)}")
            
            return {
                'success': True,
                'response_length': len(chat_text),
                'has_detailed_response': has_detailed_response,
                'has_kerala_specifics': has_kerala_specifics,
                'has_ui_integration': has_ui_integration,
                'destination_cards': len(destination_cards),
                'question_chips': len(question_chips)
            }
        
        return {'success': False}

    def run_all_retrieval_tests(self):
        """Run all RetrievalAgent tests"""
        print(f"🚀 Starting RetrievalAgent Implementation Tests...")
        print(f"   Base URL: {self.base_url}")
        print(f"   Session ID: {self.session_id}")
        
        # Test 1: Facts Retrieval
        facts_results = self.test_retrieval_agent_facts_retrieval()
        
        # Test 2: Hotel Facts with Metadata
        hotel_results = self.test_retrieval_agent_hotel_facts()
        
        # Test 3: No Facts Response
        no_facts_result = self.test_retrieval_agent_no_facts_response()
        
        # Test 4: LLM Integration
        llm_result = self.test_retrieval_agent_llm_integration()
        
        # Analyze results
        print(f"\n{'='*60}")
        print(f"🔍 RETRIEVAL AGENT TEST RESULTS")
        print(f"{'='*60}")
        
        # Facts Retrieval Analysis
        print(f"\n📊 FACTS RETRIEVAL ANALYSIS:")
        successful_destinations = 0
        for dest, result in facts_results.items():
            if result.get('success'):
                successful_destinations += 1
                status = "✅ PASS" if (result.get('has_destination_info') and 
                                    result.get('has_comprehensive_response') and 
                                    result.get('within_limit')) else "⚠️  PARTIAL"
                print(f"   {dest}: {status}")
                print(f"      Response: {result.get('response_length', 0)} chars")
                print(f"      UI Actions: {result.get('total_ui_actions', 0)}")
            else:
                print(f"   {dest}: ❌ FAIL")
        
        # Hotel Facts Analysis
        print(f"\n🏨 HOTEL FACTS ANALYSIS:")
        successful_hotels = 0
        for dest, result in hotel_results.items():
            if result.get('success'):
                successful_hotels += 1
                status = "✅ PASS" if (result.get('hotel_cards', 0) > 0 and 
                                    result.get('metadata_score', 0) >= 0.7) else "⚠️  PARTIAL"
                print(f"   {dest}: {status}")
                print(f"      Hotel cards: {result.get('hotel_cards', 0)}")
                print(f"      Metadata: {result.get('metadata_score', 0):.2f}")
            else:
                print(f"   {dest}: ❌ FAIL")
        
        # No Facts Response Analysis
        print(f"\n❌ NO FACTS RESPONSE:")
        if no_facts_result.get('success'):
            status = "✅ PASS" if (no_facts_result.get('has_helpful_response') and 
                                 no_facts_result.get('has_suggestions')) else "⚠️  PARTIAL"
            print(f"   Unknown destination handling: {status}")
        else:
            print(f"   Unknown destination handling: ❌ FAIL")
        
        # LLM Integration Analysis
        print(f"\n🤖 LLM INTEGRATION:")
        if llm_result.get('success'):
            status = "✅ PASS" if (llm_result.get('has_detailed_response') and 
                                 llm_result.get('has_kerala_specifics') and 
                                 llm_result.get('has_ui_integration')) else "⚠️  PARTIAL"
            print(f"   LLM vs Fallback: {status}")
            print(f"      Response length: {llm_result.get('response_length', 0)} chars")
            print(f"      UI integration: {llm_result.get('has_ui_integration', False)}")
        else:
            print(f"   LLM vs Fallback: ❌ FAIL")
        
        # Overall Assessment
        print(f"\n🎯 OVERALL RETRIEVAL AGENT ASSESSMENT:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Specific RetrievalAgent criteria
        facts_score = successful_destinations / len(facts_results) if facts_results else 0
        hotels_score = successful_hotels / len(hotel_results) if hotel_results else 0
        no_facts_score = 1 if no_facts_result.get('success') else 0
        llm_score = 1 if llm_result.get('success') else 0
        
        overall_score = (facts_score + hotels_score + no_facts_score + llm_score) / 4
        
        print(f"\n📈 RETRIEVAL AGENT SPECIFIC SCORES:")
        print(f"   Facts Retrieval: {facts_score:.2f} ({successful_destinations}/{len(facts_results)})")
        print(f"   Hotel Facts: {hotels_score:.2f} ({successful_hotels}/{len(hotel_results)})")
        print(f"   No Facts Handling: {no_facts_score:.2f}")
        print(f"   LLM Integration: {llm_score:.2f}")
        print(f"   Overall Score: {overall_score:.2f}")
        
        if overall_score >= 0.8:
            print(f"🎉 EXCELLENT! RetrievalAgent implementation is working great!")
            return True
        elif overall_score >= 0.6:
            print(f"✅ GOOD! RetrievalAgent is mostly functional with minor issues")
            return True
        else:
            print(f"⚠️  NEEDS IMPROVEMENT! RetrievalAgent has significant issues")
            return False

if __name__ == "__main__":
    tester = RetrievalAgentTester()
    success = tester.run_all_retrieval_tests()
    exit(0 if success else 1)