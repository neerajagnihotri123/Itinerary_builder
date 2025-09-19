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

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://trip-architect-4.preview.emergentagent.com')
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

    def test_service_recommendations_api(self):
        """Test POST /api/service-recommendations endpoint"""
        try:
            print(f"\n🔧 Testing Service Recommendations API")
            
            # Test different service types and locations
            test_cases = [
                {
                    "service_type": "accommodation",
                    "location": "Goa",
                    "traveler_profile": {
                        "vacation_style": "adventurous",
                        "experience_type": "nature",
                        "budget_level": "moderate",
                        "preferences": ["beach", "water sports"]
                    }
                },
                {
                    "service_type": "activities", 
                    "location": "Kerala",
                    "traveler_profile": {
                        "vacation_style": "relaxing",
                        "experience_type": "culture",
                        "budget_level": "luxury",
                        "preferences": ["backwaters", "ayurveda"]
                    }
                },
                {
                    "service_type": "transportation",
                    "location": "Mumbai",
                    "traveler_profile": {
                        "vacation_style": "balanced",
                        "experience_type": "mixed",
                        "budget_level": "budget",
                        "preferences": ["convenience", "safety"]
                    }
                }
            ]
            
            all_passed = True
            
            for i, test_case in enumerate(test_cases):
                payload = {
                    "session_id": self.session_id,
                    **test_case
                }
                
                response = requests.post(f"{API_BASE}/service-recommendations", json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["services", "service_type", "location", "total_options", "auto_selected"]
                    
                    if all(field in data for field in required_fields):
                        services = data["services"]
                        
                        # Verify we get exactly 10 services
                        if len(services) == 10:
                            # Check service structure
                            first_service = services[0]
                            required_service_fields = ["id", "name", "type", "location", "rating", "price", 
                                                     "similarity_score", "match_reasons", "description", "features"]
                            
                            if all(field in first_service for field in required_service_fields):
                                # Verify services are ranked (similarity_score descending)
                                scores = [s.get("similarity_score", 0) for s in services]
                                is_ranked = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                                
                                if is_ranked:
                                    print(f"✅ {test_case['service_type']} in {test_case['location']}: {len(services)} ranked services")
                                else:
                                    print(f"❌ Services not properly ranked by similarity score")
                                    all_passed = False
                            else:
                                print(f"❌ Service missing required fields: {required_service_fields}")
                                all_passed = False
                        else:
                            print(f"❌ Expected 10 services, got {len(services)}")
                            all_passed = False
                    else:
                        print(f"❌ Response missing required fields: {required_fields}")
                        all_passed = False
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    all_passed = False
            
            if all_passed:
                self.log_result("Service Recommendations API", True, 
                              f"All 3 service types tested successfully with 10 ranked services each")
                return True
            else:
                self.log_result("Service Recommendations API", False, "Some test cases failed")
                return False
                
        except Exception as e:
            self.log_result("Service Recommendations API", False, f"Request failed: {str(e)}")
            return False

    def test_conflict_detection_api(self):
        """Test POST /api/conflict-check endpoint"""
        try:
            print(f"\n🚨 Testing Conflict Detection API")
            
            # Create sample itinerary with potential conflicts
            sample_itinerary = [
                {
                    "day": 1,
                    "date": "2024-12-15",
                    "title": "Day 1: Arrival in Goa",
                    "activities": [
                        {
                            "time": "9:00 AM",
                            "title": "Airport Pickup",
                            "description": "Arrival and hotel check-in",
                            "location": "Goa Airport",
                            "category": "arrival",
                            "duration": "2 hours"
                        },
                        {
                            "time": "10:30 AM",  # CONFLICT: Overlaps with previous activity
                            "title": "Beach Visit",
                            "description": "Visit Baga Beach",
                            "location": "Baga Beach",
                            "category": "leisure",
                            "duration": "3 hours"
                        },
                        {
                            "time": "2:00 PM",
                            "title": "Water Sports",
                            "description": "Parasailing and jet skiing",
                            "location": "Calangute Beach",
                            "category": "adventure",
                            "duration": "4 hours"
                        },
                        {
                            "time": "6:00 PM",
                            "title": "Sunset Cruise",
                            "description": "Evening cruise with dinner",
                            "location": "Mandovi River",
                            "category": "leisure",
                            "duration": "3 hours"
                        },
                        {
                            "time": "8:00 PM",  # CONFLICT: Overlaps with cruise
                            "title": "Night Market",
                            "description": "Shopping at Anjuna Flea Market",
                            "location": "Anjuna",
                            "category": "shopping",
                            "duration": "2 hours"
                        }
                    ]
                },
                {
                    "day": 2,
                    "date": "2024-12-16", 
                    "title": "Day 2: Adventure Day",
                    "activities": [
                        {
                            "time": "6:00 AM",
                            "title": "Scuba Diving",
                            "description": "Deep sea diving experience",
                            "location": "Grande Island",
                            "category": "adventure",
                            "duration": "8 hours"  # Very long activity
                        },
                        {
                            "time": "3:00 PM",
                            "title": "Spice Plantation",
                            "description": "Visit spice gardens",
                            "location": "Ponda",  # Far from Grande Island
                            "category": "culture",
                            "duration": "3 hours"
                        }
                    ]
                }
            ]
            
            payload = {
                "session_id": self.session_id,
                "itinerary": sample_itinerary
            }
            
            response = requests.post(f"{API_BASE}/conflict-check", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["has_conflicts", "has_warnings", "conflicts", "warnings", 
                                 "suggestions", "feasibility_score", "total_issues"]
                
                if all(field in data for field in required_fields):
                    # Should detect conflicts (time overlaps)
                    if data["has_conflicts"]:
                        conflicts = data["conflicts"]
                        
                        # Check if time overlap conflicts are detected
                        time_conflicts = [c for c in conflicts if c.get("type") == "time_overlap"]
                        if len(time_conflicts) >= 2:  # Should detect at least 2 overlaps
                            # Check feasibility score (should be low due to conflicts)
                            feasibility_score = data["feasibility_score"]
                            if feasibility_score < 0.8:  # Should be penalized for conflicts
                                self.log_result("Conflict Detection API", True, 
                                              f"Detected {len(conflicts)} conflicts, {len(data['warnings'])} warnings, feasibility: {feasibility_score:.2f}")
                                return True
                            else:
                                self.log_result("Conflict Detection API", False, 
                                              f"Feasibility score too high ({feasibility_score}) despite conflicts")
                        else:
                            self.log_result("Conflict Detection API", False, 
                                          f"Expected time overlap conflicts, got: {[c.get('type') for c in conflicts]}")
                    else:
                        self.log_result("Conflict Detection API", False, 
                                      "Should have detected conflicts in sample itinerary")
                else:
                    self.log_result("Conflict Detection API", False, f"Missing required fields: {required_fields}")
            else:
                self.log_result("Conflict Detection API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Conflict Detection API", False, f"Request failed: {str(e)}")
            
        return False

    def test_itinerary_editing_api(self):
        """Test POST /api/edit-itinerary endpoint"""
        try:
            print(f"\n✏️ Testing Itinerary Editing API")
            
            # Sample itinerary for editing
            sample_itinerary = [
                {
                    "day": 1,
                    "date": "2024-12-15",
                    "title": "Day 1: Goa Arrival",
                    "activities": [
                        {
                            "time": "10:00 AM",
                            "title": "Hotel Check-in",
                            "description": "Arrival and check-in",
                            "location": "Goa Hotel",
                            "category": "arrival",
                            "duration": "1 hour"
                        },
                        {
                            "time": "2:00 PM",
                            "title": "Beach Visit",
                            "description": "Relax at Baga Beach",
                            "location": "Baga Beach",
                            "category": "leisure",
                            "duration": "3 hours"
                        }
                    ]
                },
                {
                    "day": 2,
                    "date": "2024-12-16",
                    "title": "Day 2: Adventure",
                    "activities": [
                        {
                            "time": "9:00 AM",
                            "title": "Water Sports",
                            "description": "Parasailing and jet skiing",
                            "location": "Calangute Beach",
                            "category": "adventure",
                            "duration": "4 hours"
                        }
                    ]
                }
            ]
            
            # Test different editing operations
            edit_operations = [
                {
                    "operation": "move_activity",
                    "operation_data": {
                        "from_day": 0,
                        "to_day": 1,
                        "activity_index": 1  # Move beach visit from day 1 to day 2
                    }
                },
                {
                    "operation": "add_destination",
                    "operation_data": {
                        "destination": "Old Goa",
                        "day_index": 1,
                        "date": "2024-12-17"
                    }
                },
                {
                    "operation": "lock_service",
                    "operation_data": {
                        "service_id": "hotel_goa_premium",
                        "day_index": 0,
                        "activity_index": 0
                    }
                }
            ]
            
            all_passed = True
            
            for operation in edit_operations:
                payload = {
                    "session_id": self.session_id,
                    "itinerary": sample_itinerary,
                    **operation
                }
                
                response = requests.post(f"{API_BASE}/edit-itinerary", json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["edited_itinerary", "operation", "conflict_check", "success"]
                    
                    if all(field in data for field in required_fields):
                        if data["success"]:
                            edited_itinerary = data["edited_itinerary"]
                            
                            # Verify operation was applied
                            if operation["operation"] == "move_activity":
                                # Check if activity was moved
                                day2_activities = edited_itinerary[1]["activities"]
                                moved_activity_found = any("Beach Visit" in act.get("title", "") for act in day2_activities)
                                if moved_activity_found:
                                    print(f"✅ Move activity operation successful")
                                else:
                                    print(f"❌ Move activity operation failed")
                                    all_passed = False
                                    
                            elif operation["operation"] == "add_destination":
                                # Check if new day was added
                                if len(edited_itinerary) > len(sample_itinerary):
                                    print(f"✅ Add destination operation successful")
                                else:
                                    print(f"❌ Add destination operation failed")
                                    all_passed = False
                                    
                            elif operation["operation"] == "lock_service":
                                # Check if service was locked
                                first_activity = edited_itinerary[0]["activities"][0]
                                if first_activity.get("locked"):
                                    print(f"✅ Lock service operation successful")
                                else:
                                    print(f"❌ Lock service operation failed")
                                    all_passed = False
                        else:
                            print(f"❌ Operation {operation['operation']} returned success=False")
                            all_passed = False
                    else:
                        print(f"❌ Missing required fields for {operation['operation']}: {required_fields}")
                        all_passed = False
                else:
                    print(f"❌ {operation['operation']} failed: HTTP {response.status_code}: {response.text}")
                    all_passed = False
            
            if all_passed:
                self.log_result("Itinerary Editing API", True, 
                              f"All 3 editing operations (move_activity, add_destination, lock_service) successful")
                return True
            else:
                self.log_result("Itinerary Editing API", False, "Some editing operations failed")
                return False
                
        except Exception as e:
            self.log_result("Itinerary Editing API", False, f"Request failed: {str(e)}")
            return False

    def test_integration_flow(self):
        """Test the full integration flow: chat -> itinerary -> services -> conflicts"""
        try:
            print(f"\n🔄 Testing Full Integration Flow")
            
            # Step 1: Chat message to trigger trip planning
            chat_payload = {
                "message": "I want to plan a trip to Goa",
                "session_id": self.session_id
            }
            
            chat_response = requests.post(f"{API_BASE}/chat", json=chat_payload, timeout=60)
            if chat_response.status_code != 200:
                self.log_result("Integration Flow - Chat", False, f"Chat failed: {chat_response.status_code}")
                return False
            
            # Step 2: Generate itinerary
            itinerary_payload = {
                "session_id": self.session_id,
                "trip_details": {
                    "destination": "Goa",
                    "start_date": "2024-12-15",
                    "end_date": "2024-12-18",
                    "adults": 2,
                    "budget_per_night": 8000
                },
                "persona_tags": ["adventurer", "nature_lover"]
            }
            
            itinerary_response = requests.post(f"{API_BASE}/generate-itinerary", json=itinerary_payload, timeout=120)
            if itinerary_response.status_code != 200:
                self.log_result("Integration Flow - Itinerary", False, f"Itinerary generation failed: {itinerary_response.status_code}")
                return False
            
            itinerary_data = itinerary_response.json()
            if not itinerary_data.get("variants") or len(itinerary_data["variants"]) == 0:
                self.log_result("Integration Flow - Itinerary", False, "No itinerary variants generated")
                return False
            
            # Step 3: Get service recommendations for accommodation
            service_payload = {
                "session_id": self.session_id,
                "service_type": "accommodation",
                "location": "Goa",
                "traveler_profile": {
                    "vacation_style": "adventurous",
                    "experience_type": "nature",
                    "budget_level": "moderate"
                }
            }
            
            service_response = requests.post(f"{API_BASE}/service-recommendations", json=service_payload, timeout=60)
            if service_response.status_code != 200:
                self.log_result("Integration Flow - Services", False, f"Service recommendations failed: {service_response.status_code}")
                return False
            
            service_data = service_response.json()
            if not service_data.get("services") or len(service_data["services"]) != 10:
                self.log_result("Integration Flow - Services", False, f"Expected 10 services, got {len(service_data.get('services', []))}")
                return False
            
            # Step 4: Check conflicts in generated itinerary
            first_variant = itinerary_data["variants"][0]
            conflict_payload = {
                "session_id": self.session_id,
                "itinerary": first_variant.get("itinerary", [])
            }
            
            conflict_response = requests.post(f"{API_BASE}/conflict-check", json=conflict_payload, timeout=60)
            if conflict_response.status_code != 200:
                self.log_result("Integration Flow - Conflicts", False, f"Conflict check failed: {conflict_response.status_code}")
                return False
            
            conflict_data = conflict_response.json()
            if "feasibility_score" not in conflict_data:
                self.log_result("Integration Flow - Conflicts", False, "No feasibility score in conflict response")
                return False
            
            # Success - all steps completed
            self.log_result("Integration Flow", True, 
                          f"Complete flow successful: Chat -> Itinerary ({len(itinerary_data['variants'])} variants) -> Services (10 recommendations) -> Conflicts (feasibility: {conflict_data['feasibility_score']:.2f})")
            return True
            
        except Exception as e:
            self.log_result("Integration Flow", False, f"Integration flow failed: {str(e)}")
            return False

    def test_advanced_features(self):
        """Test the advanced features from review request"""
        print(f"\n🚀 Testing Advanced Features")
        print("=" * 80)
        
        # Test sequence for advanced features
        tests = [
            ("Health Check", self.test_health_check),
            ("Service Recommendations API", self.test_service_recommendations_api),
            ("Conflict Detection API", self.test_conflict_detection_api),
            ("Itinerary Editing API", self.test_itinerary_editing_api),
            ("Integration Flow", self.test_integration_flow)
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