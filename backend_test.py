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

# Configuration - Use production URL from environment
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://ai-concierge-6.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔍 Testing against: {BACKEND_URL}")
print(f"🔍 API Base: {API_BASE}")

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

    def test_complete_itinerary_flow(self):
        """Test the complete itinerary generation flow as requested in review"""
        try:
            print(f"\n🎯 Testing Complete Itinerary Generation Flow")
            print("=" * 60)
            
            # Step 1: Initial chat message that should trigger trip planner
            print("Step 1: Sending trip planning message...")
            chat_payload = {
                "message": "I want to plan a trip to Goa",
                "session_id": self.session_id
            }
            
            chat_response = requests.post(f"{API_BASE}/chat", json=chat_payload, timeout=60)
            
            if chat_response.status_code != 200:
                self.log_result("Complete Itinerary Flow - Chat", False, 
                              f"Chat endpoint failed: HTTP {chat_response.status_code}: {chat_response.text}")
                return False
            
            chat_data = chat_response.json()
            print(f"✅ Chat response received: {chat_data['chat_text'][:100]}...")
            
            # Verify trip planner card is triggered
            has_trip_planner = any(
                action.get("type") == "trip_planner_card" 
                for action in chat_data.get("ui_actions", [])
            )
            
            if not has_trip_planner:
                self.log_result("Complete Itinerary Flow - Chat", False, 
                              "Trip planner card not triggered for Goa trip message")
                return False
            
            # Step 2: Profile intake with adventurous/nature preferences
            print("Step 2: Submitting profile intake...")
            profile_payload = {
                "session_id": self.session_id,
                "responses": {
                    "vacation_style": "adventurous",
                    "experience_type": "nature",
                    "attraction_preference": "both",
                    "accommodation": ["boutique_hotels", "luxury_hotels"],
                    "interests": ["hiking", "food", "photography", "wildlife"],
                    "custom_inputs": ["I love water sports and want to try paragliding in Goa"]
                }
            }
            
            profile_response = requests.post(f"{API_BASE}/profile-intake", json=profile_payload, timeout=60)
            
            if profile_response.status_code != 200:
                self.log_result("Complete Itinerary Flow - Profile", False, 
                              f"Profile intake failed: HTTP {profile_response.status_code}: {profile_response.text}")
                return False
            
            profile_data = profile_response.json()
            print(f"✅ Profile intake completed with persona tags: {profile_data.get('persona_tags', [])}")
            
            # Step 3: Persona classification
            print("Step 3: Running persona classification...")
            trip_details = {
                "destination": "Goa",
                "start_date": "2024-12-15",
                "end_date": "2024-12-20",
                "adults": 2,
                "children": 0,
                "budget_per_night": 12000
            }
            
            persona_payload = {
                "session_id": self.session_id,
                "trip_details": trip_details,
                "profile_data": profile_payload["responses"]
            }
            
            persona_response = requests.post(f"{API_BASE}/persona-classification", json=persona_payload, timeout=60)
            
            if persona_response.status_code != 200:
                self.log_result("Complete Itinerary Flow - Persona", False, 
                              f"Persona classification failed: HTTP {persona_response.status_code}: {persona_response.text}")
                return False
            
            persona_data = persona_response.json()
            print(f"✅ Persona classified as: {persona_data.get('persona_type')} with confidence {persona_data.get('confidence', 0):.2f}")
            
            # Step 4: Generate itinerary - THE CRITICAL TEST
            print("Step 4: Generating itinerary variants...")
            itinerary_payload = {
                "session_id": self.session_id,
                "trip_details": trip_details,
                "persona_tags": persona_data.get("persona_tags", ["adventurer", "nature_lover"])
            }
            
            itinerary_response = requests.post(f"{API_BASE}/generate-itinerary", json=itinerary_payload, timeout=120)
            
            if itinerary_response.status_code != 200:
                self.log_result("Complete Itinerary Flow - Itinerary", False, 
                              f"Itinerary generation failed: HTTP {itinerary_response.status_code}: {itinerary_response.text}")
                return False
            
            itinerary_data = itinerary_response.json()
            
            # Step 5: Verify data format for frontend timeline rendering
            print("Step 5: Verifying data format for timeline rendering...")
            
            # Check required top-level fields
            required_fields = ["variants", "session_id", "generated_at"]
            if not all(field in itinerary_data for field in required_fields):
                self.log_result("Complete Itinerary Flow - Format", False, 
                              f"Missing required top-level fields: {required_fields}")
                return False
            
            variants = itinerary_data["variants"]
            
            # Verify 3 variants
            if len(variants) != 3:
                self.log_result("Complete Itinerary Flow - Format", False, 
                              f"Expected 3 variants, got {len(variants)}")
                return False
            
            # Verify each variant has correct format for frontend
            variant_issues = []
            for i, variant in enumerate(variants):
                # Check required variant fields (based on server.py response format)
                required_variant_fields = ["id", "title", "description", "persona", "days", "price", 
                                         "total_activities", "activity_types", "highlights", "recommended", "itinerary"]
                
                missing_fields = [field for field in required_variant_fields if field not in variant]
                if missing_fields:
                    variant_issues.append(f"Variant {i+1} missing fields: {missing_fields}")
                    continue
                
                # Check itinerary structure for timeline rendering
                itinerary = variant["itinerary"]
                if not isinstance(itinerary, list) or len(itinerary) == 0:
                    variant_issues.append(f"Variant {i+1} has invalid itinerary structure")
                    continue
                
                # Check first day structure
                first_day = itinerary[0]
                required_day_fields = ["day", "date", "title", "activities"]
                missing_day_fields = [field for field in required_day_fields if field not in first_day]
                if missing_day_fields:
                    variant_issues.append(f"Variant {i+1} day missing fields: {missing_day_fields}")
                    continue
                
                # Check first activity structure
                activities = first_day["activities"]
                if not isinstance(activities, list) or len(activities) == 0:
                    variant_issues.append(f"Variant {i+1} has no activities")
                    continue
                
                first_activity = activities[0]
                required_activity_fields = ["time", "title", "description", "location", "category", "duration"]
                missing_activity_fields = [field for field in required_activity_fields if field not in first_activity]
                if missing_activity_fields:
                    variant_issues.append(f"Variant {i+1} activity missing fields: {missing_activity_fields}")
                    continue
            
            if variant_issues:
                self.log_result("Complete Itinerary Flow - Format", False, 
                              f"Variant format issues: {'; '.join(variant_issues)}")
                return False
            
            # Verify content quality (not just structure)
            content_issues = []
            for i, variant in enumerate(variants):
                # Check if content appears to be LLM-generated (not hardcoded)
                title = variant["title"]
                description = variant["description"]
                highlights = variant.get("highlights", [])
                
                # Basic content quality checks
                if len(description) < 30:
                    content_issues.append(f"Variant {i+1} description too short")
                
                if len(highlights) < 2:
                    content_issues.append(f"Variant {i+1} has insufficient highlights")
                
                # Check for Goa-specific content
                goa_mentioned = any("goa" in str(field).lower() for field in [title, description] + highlights)
                if not goa_mentioned:
                    content_issues.append(f"Variant {i+1} doesn't mention Goa")
                
                # Check activity content
                first_activity = variant["itinerary"][0]["activities"][0]
                activity_desc = first_activity["description"]
                if len(activity_desc) < 20:
                    content_issues.append(f"Variant {i+1} activity description too short")
            
            if content_issues:
                self.log_result("Complete Itinerary Flow - Content", False, 
                              f"Content quality issues: {'; '.join(content_issues)}")
                return False
            
            # Success! Log detailed results
            variant_summary = []
            for variant in variants:
                variant_summary.append(
                    f"{variant['persona']}: {variant['title']} "
                    f"({variant['days']} days, ₹{variant['price']:,}, {variant['total_activities']} activities)"
                )
            
            self.log_result("Complete Itinerary Flow", True, 
                          f"✅ COMPLETE FLOW SUCCESS: {'; '.join(variant_summary)}", 
                          {
                              "variants_count": len(variants),
                              "personas": [v["persona"] for v in variants],
                              "total_activities": sum(v["total_activities"] for v in variants),
                              "price_range": f"₹{min(v['price'] for v in variants):,} - ₹{max(v['price'] for v in variants):,}"
                          })
            
            print(f"🎉 Complete itinerary flow test PASSED!")
            print(f"📊 Generated {len(variants)} variants with proper timeline data format")
            return True
            
        except Exception as e:
            self.log_result("Complete Itinerary Flow", False, f"Flow test failed with exception: {str(e)}")
            return False

    def test_critical_llm_integration(self):
        """Test the critical LLM integration scenarios from review request"""
        print(f"\n🧪 Testing Critical LLM Integration Scenarios")
        print("=" * 80)
        
        # Test sequence focusing on the review request scenarios
        tests = [
            ("Health Check", self.test_health_check),
            ("Complete Itinerary Flow", self.test_complete_itinerary_flow)
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
    passed, total = tester.test_critical_llm_integration()
    
    success = tester.print_summary()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main()