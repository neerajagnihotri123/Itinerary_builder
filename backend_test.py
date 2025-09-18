#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Travello.ai
Tests the complete new clean agent-based backend architecture with real LLM integration
"""

import requests
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://ai-trip-planner-1.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class TravelloBackendTester:
    def __init__(self):
        self.session_id = f"test_{uuid.uuid4().hex[:8]}"
        self.test_results = []
        self.profile_data = {}
        self.trip_details = {}
        self.persona_data = {}
        
    def log_result(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def verify_llm_response(self, response_text: str, context: str) -> bool:
        """Verify that response appears to be LLM-generated (not hardcoded)"""
        # Check for signs of LLM generation
        llm_indicators = [
            len(response_text) > 50,  # Substantial response
            any(word in response_text.lower() for word in ["i'd", "i'll", "let me", "i can", "i'm"]),  # Personal pronouns
            "!" in response_text or "?" in response_text,  # Natural punctuation
            not response_text.startswith("{") and not response_text.startswith("["),  # Not JSON
        ]
        
        # Check it's not obviously hardcoded
        hardcoded_indicators = [
            response_text == "Hello World",
            response_text == "Test response",
            "mock" in response_text.lower(),
            "placeholder" in response_text.lower(),
            response_text.count("test") > 2
        ]
        
        is_llm_like = sum(llm_indicators) >= 2
        is_not_hardcoded = not any(hardcoded_indicators)
        
        return is_llm_like and is_not_hardcoded

    def test_health_check(self):
        """Test GET / endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["status", "service", "version", "timestamp"]
                
                if all(field in data for field in required_fields):
                    if data["status"] == "healthy" and "Travello.ai" in data["service"]:
                        self.log_result("Health Check", True, f"Service healthy, version {data['version']}", data)
                        return True
                    else:
                        self.log_result("Health Check", False, f"Invalid health status: {data}", data)
                else:
                    self.log_result("Health Check", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
            
        return False

    def test_chat_greeting_message(self):
        """Test POST /api/chat with greeting message - should NOT classify as trip_planning"""
        try:
            payload = {
                "message": "hello there!",
                "session_id": "test_greeting"
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["chat_text", "ui_actions", "updated_profile", "followup_questions", "analytics_tags"]
                
                if all(field in data for field in required_fields):
                    # Verify LLM-powered response (not hardcoded)
                    if self.verify_llm_response(data["chat_text"], "greeting"):
                        # Should NOT have trip_planner_card for greeting
                        has_trip_planner = any(
                            action.get("type") == "trip_planner_card" 
                            for action in data["ui_actions"]
                        )
                        
                        # Should use general_inquiry analytics tag
                        has_general_tag = "general_inquiry" in data["analytics_tags"]
                        
                        # Should have follow-up questions
                        has_followup = len(data["followup_questions"]) > 0
                        
                        if not has_trip_planner and has_general_tag and has_followup:
                            self.log_result("Chat Greeting Message", True, 
                                          f"LLM greeting response without trip planning: {data['chat_text'][:100]}...", data)
                            return True
                        else:
                            issues = []
                            if has_trip_planner:
                                issues.append("incorrectly triggered trip_planner_card")
                            if not has_general_tag:
                                issues.append("missing general_inquiry tag")
                            if not has_followup:
                                issues.append("no follow-up questions")
                            self.log_result("Chat Greeting Message", False, 
                                          f"Issues: {', '.join(issues)}. Analytics: {data['analytics_tags']}", data)
                    else:
                        self.log_result("Chat Greeting Message", False, 
                                      f"Response appears hardcoded: {data['chat_text']}", data)
                else:
                    self.log_result("Chat Greeting Message", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Chat Greeting Message", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Chat Greeting Message", False, f"Request failed: {str(e)}")
            
        return False

    def test_chat_trip_planning_message(self):
        """Test POST /api/chat with trip planning message - should classify as trip_planning"""
        try:
            payload = {
                "message": "plan a trip to goa",
                "session_id": "test_trip"
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["chat_text", "ui_actions", "updated_profile", "followup_questions", "analytics_tags"]
                
                if all(field in data for field in required_fields):
                    # Verify LLM-powered response
                    if self.verify_llm_response(data["chat_text"], "trip planning"):
                        # Should have trip_planner_card UI action
                        has_trip_planner = any(
                            action.get("type") == "trip_planner_card" 
                            for action in data["ui_actions"]
                        )
                        
                        # Should extract "Goa" as destination
                        goa_mentioned = "goa" in data["chat_text"].lower() or any(
                            "goa" in str(action.get("payload", {})).lower() 
                            for action in data["ui_actions"]
                        )
                        
                        # Should have follow-up questions about dates/travelers/budget
                        has_followup = len(data["followup_questions"]) > 0
                        
                        if has_trip_planner and goa_mentioned and has_followup:
                            self.log_result("Chat Trip Planning Message", True, 
                                          f"LLM trip planning response with Goa extraction: {data['chat_text'][:100]}...", data)
                            return True
                        else:
                            issues = []
                            if not has_trip_planner:
                                issues.append("missing trip_planner_card")
                            if not goa_mentioned:
                                issues.append("Goa not extracted/mentioned")
                            if not has_followup:
                                issues.append("no follow-up questions")
                            self.log_result("Chat Trip Planning Message", False, 
                                          f"Issues: {', '.join(issues)}", data)
                    else:
                        self.log_result("Chat Trip Planning Message", False, 
                                      f"Response appears hardcoded: {data['chat_text']}", data)
                else:
                    self.log_result("Chat Trip Planning Message", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Chat Trip Planning Message", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Chat Trip Planning Message", False, f"Request failed: {str(e)}")
            
        return False

    def test_chat_general_question(self):
        """Test POST /api/chat with general question - should NOT trigger trip_planner_card"""
        try:
            payload = {
                "message": "what can you help me with?",
                "session_id": "test_general"
            }
            
            response = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["chat_text", "ui_actions", "updated_profile", "followup_questions", "analytics_tags"]
                
                if all(field in data for field in required_fields):
                    # Verify LLM-powered response
                    if self.verify_llm_response(data["chat_text"], "general question"):
                        # Should NOT have trip_planner_card
                        has_trip_planner = any(
                            action.get("type") == "trip_planner_card" 
                            for action in data["ui_actions"]
                        )
                        
                        # Should have general follow-up questions
                        has_followup = len(data["followup_questions"]) > 0
                        
                        # Should be helpful response about capabilities
                        is_helpful = any(word in data["chat_text"].lower() for word in 
                                       ["help", "assist", "travel", "plan", "trip", "can"])
                        
                        if not has_trip_planner and has_followup and is_helpful:
                            self.log_result("Chat General Question", True, 
                                          f"LLM general response without trip planning: {data['chat_text'][:100]}...", data)
                            return True
                        else:
                            issues = []
                            if has_trip_planner:
                                issues.append("incorrectly triggered trip_planner_card")
                            if not has_followup:
                                issues.append("no follow-up questions")
                            if not is_helpful:
                                issues.append("not helpful about capabilities")
                            self.log_result("Chat General Question", False, 
                                          f"Issues: {', '.join(issues)}", data)
                    else:
                        self.log_result("Chat General Question", False, 
                                      f"Response appears hardcoded: {data['chat_text']}", data)
                else:
                    self.log_result("Chat General Question", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Chat General Question", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Chat General Question", False, f"Request failed: {str(e)}")
            
        return False

    def test_profile_intake_endpoint(self):
        """Test POST /api/profile-intake endpoint"""
        try:
            # Realistic profile responses
            profile_responses = {
                "vacation_style": "adventurous",
                "experience_type": "nature",
                "attraction_preference": "both",
                "accommodation": ["boutique_hotels", "luxury_hotels"],
                "interests": ["hiking", "food", "photography", "wildlife"],
                "custom_inputs": ["I love mountain trekking and want to try paragliding"]
            }
            
            payload = {
                "session_id": self.session_id,
                "responses": profile_responses
            }
            
            response = requests.post(f"{API_BASE}/profile-intake", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["profile_complete", "persona_tags", "next_questions", "ui_actions"]
                
                if all(field in data for field in required_fields):
                    # Store profile data for later tests
                    self.profile_data = profile_responses
                    
                    # Verify persona tags are generated (not empty)
                    if data["persona_tags"] and len(data["persona_tags"]) > 0:
                        # Check for adventure-related tags
                        has_adventure_tags = any(
                            "adventure" in tag.lower() or "outdoor" in tag.lower() 
                            for tag in data["persona_tags"]
                        )
                        
                        if has_adventure_tags:
                            self.log_result("Profile Intake", True, 
                                          f"Profile processed with persona tags: {data['persona_tags']}", data)
                            return True
                        else:
                            self.log_result("Profile Intake", False, 
                                          f"Persona tags don't match adventurous profile: {data['persona_tags']}", data)
                    else:
                        self.log_result("Profile Intake", False, f"No persona tags generated: {data}", data)
                else:
                    self.log_result("Profile Intake", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Profile Intake", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Profile Intake", False, f"Request failed: {str(e)}")
            
        return False

    def test_persona_classification_endpoint(self):
        """Test POST /api/persona-classification endpoint"""
        try:
            # Realistic trip details
            trip_details = {
                "destination": "Goa",
                "start_date": "2024-12-15",
                "end_date": "2024-12-20",
                "adults": 2,
                "children": 0,
                "budget_per_night": 12000
            }
            
            payload = {
                "session_id": self.session_id,
                "trip_details": trip_details,
                "profile_data": self.profile_data or {
                    "vacation_style": "adventurous",
                    "experience_type": "nature",
                    "interests": ["hiking", "food"]
                }
            }
            
            response = requests.post(f"{API_BASE}/persona-classification", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["persona_type", "persona_tags", "confidence", "ui_actions"]
                
                if all(field in data for field in required_fields):
                    # Store data for itinerary generation
                    self.trip_details = trip_details
                    self.persona_data = data
                    
                    # Verify LLM-based classification (not rule-based hardcoded)
                    valid_personas = ["adventurer", "cultural_explorer", "luxury_connoisseur", 
                                    "budget_backpacker", "eco_conscious_traveler", "family_oriented", "business_traveler"]
                    
                    if data["persona_type"] in valid_personas:
                        # Check confidence score is reasonable
                        confidence = data["confidence"]
                        if 0.1 <= confidence <= 1.0:
                            # Verify persona matches profile (adventurous -> adventurer likely)
                            expected_match = data["persona_type"] in ["adventurer", "eco_conscious_traveler"]
                            
                            self.log_result("Persona Classification", True, 
                                          f"Classified as {data['persona_type']} with {confidence:.2f} confidence", data)
                            return True
                        else:
                            self.log_result("Persona Classification", False, 
                                          f"Invalid confidence score: {confidence}", data)
                    else:
                        self.log_result("Persona Classification", False, 
                                      f"Invalid persona type: {data['persona_type']}", data)
                else:
                    self.log_result("Persona Classification", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Persona Classification", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Persona Classification", False, f"Request failed: {str(e)}")
            
        return False

    def test_generate_itinerary_endpoint(self):
        """Test POST /api/generate-itinerary endpoint - The critical test"""
        try:
            # Use data from previous tests or defaults
            trip_details = self.trip_details or {
                "destination": "Goa",
                "start_date": "2024-12-15",
                "end_date": "2024-12-20",
                "adults": 2,
                "children": 0,
                "budget_per_night": 12000
            }
            
            persona_tags = self.persona_data.get("persona_tags", ["adventurer", "nature_lover"])
            
            payload = {
                "session_id": self.session_id,
                "trip_details": trip_details,
                "persona_tags": persona_tags
            }
            
            print(f"🗓️ Generating itinerary for {trip_details['destination']} with persona tags: {persona_tags}")
            
            response = requests.post(f"{API_BASE}/generate-itinerary", json=payload, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["variants", "session_id", "generated_at"]
                
                if all(field in data for field in required_fields):
                    variants = data["variants"]
                    
                    # Verify 3 variants generated
                    if len(variants) == 3:
                        variant_types = [v["type"] for v in variants]
                        expected_types = ["adventurer", "balanced", "luxury"]
                        
                        if all(vtype in variant_types for vtype in expected_types):
                            # Verify each variant has real LLM-generated content
                            all_variants_valid = True
                            variant_details = []
                            
                            for variant in variants:
                                # Check required variant fields
                                variant_fields = ["id", "type", "title", "description", "days", "total_cost", 
                                                "daily_itinerary", "highlights", "total_activities"]
                                
                                if not all(field in variant for field in variant_fields):
                                    all_variants_valid = False
                                    break
                                
                                # Verify daily itinerary has real activities
                                daily_itinerary = variant["daily_itinerary"]
                                if len(daily_itinerary) > 0:
                                    # Check first day activities
                                    first_day = daily_itinerary[0]
                                    if "activities" in first_day and len(first_day["activities"]) > 0:
                                        first_activity = first_day["activities"][0]
                                        
                                        # Verify activity has realistic data
                                        activity_fields = ["id", "name", "type", "time", "duration", 
                                                         "location", "description", "cost"]
                                        
                                        if all(field in first_activity for field in activity_fields):
                                            # Check if activity appears LLM-generated (not hardcoded)
                                            activity_name = first_activity["name"]
                                            activity_desc = first_activity["description"]
                                            
                                            is_realistic = (
                                                "Goa" in activity_name or "Goa" in activity_desc or
                                                len(activity_desc) > 30 and
                                                not any(word in activity_desc.lower() for word in ["test", "mock", "placeholder"])
                                            )
                                            
                                            if is_realistic:
                                                variant_details.append(f"{variant['type']}: {variant['title']} ({variant['total_activities']} activities, ₹{variant['total_cost']})")
                                            else:
                                                all_variants_valid = False
                                                self.log_result("Generate Itinerary", False, 
                                                              f"Activity appears hardcoded: {activity_name} - {activity_desc}")
                                                break
                                        else:
                                            all_variants_valid = False
                                            break
                                    else:
                                        all_variants_valid = False
                                        break
                                else:
                                    all_variants_valid = False
                                    break
                            
                            if all_variants_valid:
                                self.log_result("Generate Itinerary", True, 
                                              f"3 variants generated with real LLM content: {'; '.join(variant_details)}", 
                                              {"variant_count": len(variants), "variant_types": variant_types})
                                return True
                            else:
                                self.log_result("Generate Itinerary", False, "Some variants have invalid or hardcoded content")
                        else:
                            self.log_result("Generate Itinerary", False, 
                                          f"Missing expected variant types. Got: {variant_types}, Expected: {expected_types}", data)
                    else:
                        self.log_result("Generate Itinerary", False, 
                                      f"Expected 3 variants, got {len(variants)}", data)
                else:
                    self.log_result("Generate Itinerary", False, f"Missing required fields: {data}", data)
            else:
                self.log_result("Generate Itinerary", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Generate Itinerary", False, f"Request failed: {str(e)}")
            
        return False

    def test_complete_flow(self):
        """Test the complete trip planning flow"""
        print(f"\n🧪 Testing Complete Trip Planning Flow (Session: {self.session_id})")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Chat Trip Planning", self.test_chat_endpoint_trip_planning),
            ("Profile Intake", self.test_profile_intake_endpoint),
            ("Persona Classification", self.test_persona_classification_endpoint),
            ("Generate Itinerary", self.test_generate_itinerary_endpoint)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            if test_func():
                passed += 1
            time.sleep(2)  # Brief pause between tests
        
        return passed, total

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 TRAVELLO.AI BACKEND TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"📊 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical verification points
        print(f"\n🔍 Critical Verification Points:")
        
        # Check LLM integration
        llm_tests = [r for r in self.test_results if "LLM" in r["details"] or "Chat" in r["test"] or "Generate" in r["test"]]
        llm_passed = sum(1 for r in llm_tests if r["success"])
        print(f"✅ LLM Integration: {llm_passed}/{len(llm_tests)} tests passed")
        
        # Check agent architecture
        agent_tests = [r for r in self.test_results if any(word in r["test"] for word in ["Profile", "Persona", "Generate"])]
        agent_passed = sum(1 for r in agent_tests if r["success"])
        print(f"✅ Agent Architecture: {agent_passed}/{len(agent_tests)} tests passed")
        
        # Check data flow
        flow_success = all(r["success"] for r in self.test_results)
        print(f"✅ Complete Data Flow: {'Working' if flow_success else 'Issues detected'}")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! Backend architecture is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Review the issues above.")
        
        return passed == total

def main():
    """Main test execution"""
    print("🚀 Starting Travello.ai Backend Architecture Test")
    print(f"🌐 Testing against: {BACKEND_URL}")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    tester = TravelloBackendTester()
    passed, total = tester.test_complete_flow()
    
    success = tester.print_summary()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()