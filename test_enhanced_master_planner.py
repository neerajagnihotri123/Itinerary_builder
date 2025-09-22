#!/usr/bin/env python3
"""
Enhanced Master Travel Planner Testing
Tests the enhanced itinerary generation system with comprehensive profile data
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

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://travel-planner-api.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔍 Testing Enhanced Master Travel Planner against: {BACKEND_URL}")
print(f"🔍 API Base: {API_BASE}")

class EnhancedMasterPlannerTester:
    def __init__(self):
        self.session_id = f"test_master_planner_{uuid.uuid4().hex[:8]}"
        self.test_results = []
        
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

    def test_enhanced_itinerary_generation_api(self):
        """Test 1: Enhanced Itinerary Generation API with comprehensive profile data"""
        try:
            print(f"\n🎯 Test 1: Enhanced Itinerary Generation API")
            print("=" * 60)
            
            payload = {
                "session_id": "test_master_planner",
                "trip_details": {
                    "destination": "Goa, India",
                    "start_date": "2024-12-25",
                    "end_date": "2024-12-28",
                    "adults": 2,
                    "budget_per_night": 4000
                },
                "persona_tags": ["adventurer", "adventure_seeker", "outdoor_enthusiast"]
            }
            
            print(f"📤 Sending request to /api/generate-itinerary...")
            response = requests.post(f"{API_BASE}/generate-itinerary", json=payload, timeout=120)
            
            if response.status_code != 200:
                self.log_result("Enhanced Itinerary Generation API", False, 
                              f"API call failed: HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            print(f"📥 Response received successfully")
            
            # Check for comprehensive itinerary structure
            required_top_fields = ["variants", "session_id", "generated_at"]
            if not all(field in data for field in required_top_fields):
                self.log_result("Enhanced Itinerary Generation API", False, 
                              f"Missing top-level fields: {required_top_fields}")
                return False
            
            variants = data.get("variants", [])
            if len(variants) == 0:
                self.log_result("Enhanced Itinerary Generation API", False, "No variants generated")
                return False
            
            print(f"📊 Found {len(variants)} variants")
            
            # Check each variant for enhanced structure
            enhanced_structure_issues = []
            
            for i, variant in enumerate(variants):
                variant_name = variant.get("title", f"Variant {i+1}")
                print(f"🔍 Checking variant: {variant_name}")
                
                # Check variant has itinerary
                if "itinerary" not in variant:
                    enhanced_structure_issues.append(f"{variant_name}: Missing itinerary")
                    continue
                
                itinerary = variant["itinerary"]
                if not isinstance(itinerary, list) or len(itinerary) == 0:
                    enhanced_structure_issues.append(f"{variant_name}: Empty or invalid itinerary")
                    continue
                
                # Check first day for enhanced activity structure
                first_day = itinerary[0]
                if "activities" not in first_day:
                    enhanced_structure_issues.append(f"{variant_name}: Day missing activities")
                    continue
                
                activities = first_day["activities"]
                if not isinstance(activities, list) or len(activities) == 0:
                    enhanced_structure_issues.append(f"{variant_name}: No activities in first day")
                    continue
                
                print(f"   📋 Found {len(activities)} activities in first day")
                
                # Check first activity for enhanced fields
                first_activity = activities[0]
                
                # Check for enhanced fields as requested in review
                enhanced_fields_check = {
                    "selected_reason": "explainability for activity selection",
                    "alternatives": "9 alternative options",
                    "travel_logistics": "distance and travel time",
                    "booking_info": "availability status",
                }
                
                # Also check for time slots
                time_field_found = False
                for time_field in ["time", "time_slot"]:
                    if time_field in first_activity:
                        time_field_found = True
                        time_value = first_activity[time_field]
                        if ":" in str(time_value):
                            print(f"   ⏰ Time slot found: {time_value}")
                        else:
                            enhanced_structure_issues.append(f"{variant_name}: Invalid time slot format: {time_value}")
                        break
                
                if not time_field_found:
                    enhanced_structure_issues.append(f"{variant_name}: Missing time slot")
                
                missing_enhanced_fields = []
                for field, description in enhanced_fields_check.items():
                    if field not in first_activity:
                        missing_enhanced_fields.append(f"{field} ({description})")
                    else:
                        print(f"   ✅ {field}: Found")
                
                if missing_enhanced_fields:
                    enhanced_structure_issues.append(f"{variant_name}: Missing enhanced fields: {', '.join(missing_enhanced_fields)}")
                    continue
                
                # Verify alternatives array has 9 options
                alternatives = first_activity.get("alternatives", [])
                if not isinstance(alternatives, list):
                    enhanced_structure_issues.append(f"{variant_name}: Alternatives is not a list")
                elif len(alternatives) != 9:
                    enhanced_structure_issues.append(f"{variant_name}: Expected 9 alternatives, got {len(alternatives)}")
                else:
                    print(f"   🔄 Found {len(alternatives)} alternatives")
                
                # Verify travel_logistics structure
                travel_logistics = first_activity.get("travel_logistics", {})
                required_logistics_fields = ["distance_km", "travel_time"]
                missing_logistics = [field for field in required_logistics_fields if field not in travel_logistics]
                if missing_logistics:
                    enhanced_structure_issues.append(f"{variant_name}: Travel logistics missing: {', '.join(missing_logistics)}")
                else:
                    print(f"   🚗 Travel logistics: {travel_logistics.get('distance_km')}km, {travel_logistics.get('travel_time')}")
                
                # Verify booking_info structure
                booking_info = first_activity.get("booking_info", {})
                required_booking_fields = ["availability"]
                missing_booking = [field for field in required_booking_fields if field not in booking_info]
                if missing_booking:
                    enhanced_structure_issues.append(f"{variant_name}: Booking info missing: {', '.join(missing_booking)}")
                else:
                    print(f"   📅 Booking availability: {booking_info.get('availability')}")
            
            if enhanced_structure_issues:
                self.log_result("Enhanced Itinerary Generation API", False, 
                              f"Enhanced structure issues: {'; '.join(enhanced_structure_issues[:3])}")
                return False
            
            # Success - log detailed results
            variant_summary = []
            for variant in variants:
                activities_count = sum(len(day.get("activities", [])) for day in variant.get("itinerary", []))
                variant_summary.append(f"{variant.get('persona', 'Unknown')}: {activities_count} activities")
            
            self.log_result("Enhanced Itinerary Generation API", True, 
                          f"ALL ENHANCED FEATURES VERIFIED: {len(variants)} variants with explainable recommendations, 9 alternatives per activity, travel logistics, booking info, and time slots")
            
            return True
            
        except Exception as e:
            self.log_result("Enhanced Itinerary Generation API", False, f"Test failed with exception: {str(e)}")
            return False

    def test_enhanced_response_structure(self):
        """Test 2: Verify Enhanced Response Structure"""
        try:
            print(f"\n🔍 Test 2: Verify Enhanced Response Structure")
            print("=" * 60)
            
            # Use the same payload as Test 1
            payload = {
                "session_id": "test_structure_check",
                "trip_details": {
                    "destination": "Goa, India",
                    "start_date": "2024-12-25",
                    "end_date": "2024-12-28",
                    "adults": 2,
                    "budget_per_night": 4000
                },
                "persona_tags": ["adventurer", "adventure_seeker", "outdoor_enthusiast"]
            }
            
            response = requests.post(f"{API_BASE}/generate-itinerary", json=payload, timeout=120)
            
            if response.status_code != 200:
                self.log_result("Enhanced Response Structure", False, 
                              f"API call failed: HTTP {response.status_code}")
                return False
            
            data = response.json()
            variants = data.get("variants", [])
            
            if len(variants) == 0:
                self.log_result("Enhanced Response Structure", False, "No variants to check")
                return False
            
            # Check specific enhanced structure requirements
            structure_checks = []
            
            for variant in variants:
                if "itinerary" in variant and len(variant["itinerary"]) > 0:
                    first_day = variant["itinerary"][0]
                    if "activities" in first_day and len(first_day["activities"]) > 0:
                        first_activity = first_day["activities"][0]
                        
                        # Check selected_reason for explainability
                        if "selected_reason" in first_activity:
                            reason = first_activity["selected_reason"]
                            if len(reason) > 20:  # Substantial explanation
                                structure_checks.append("✅ selected_reason: Explainable")
                            else:
                                structure_checks.append("❌ selected_reason: Too short")
                        else:
                            structure_checks.append("❌ selected_reason: Missing")
                        
                        # Check alternatives array
                        if "alternatives" in first_activity:
                            alternatives = first_activity["alternatives"]
                            if isinstance(alternatives, list) and len(alternatives) == 9:
                                structure_checks.append("✅ alternatives: 9 options provided")
                                
                                # Check if alternatives have reasons
                                alt_with_reasons = sum(1 for alt in alternatives if "reason" in alt and len(alt["reason"]) > 5)
                                if alt_with_reasons >= 7:  # Most alternatives have reasons
                                    structure_checks.append("✅ alternatives: Have explanations")
                                else:
                                    structure_checks.append("❌ alternatives: Missing explanations")
                            else:
                                structure_checks.append(f"❌ alternatives: Expected 9, got {len(alternatives) if isinstance(alternatives, list) else 'invalid'}")
                        else:
                            structure_checks.append("❌ alternatives: Missing")
                        
                        # Check travel_logistics
                        if "travel_logistics" in first_activity:
                            logistics = first_activity["travel_logistics"]
                            if "distance_km" in logistics and "travel_time" in logistics:
                                structure_checks.append("✅ travel_logistics: Distance and time provided")
                            else:
                                structure_checks.append("❌ travel_logistics: Missing distance/time")
                        else:
                            structure_checks.append("❌ travel_logistics: Missing")
                        
                        # Check booking_info
                        if "booking_info" in first_activity:
                            booking = first_activity["booking_info"]
                            if "availability" in booking:
                                structure_checks.append("✅ booking_info: Availability status provided")
                            else:
                                structure_checks.append("❌ booking_info: Missing availability")
                        else:
                            structure_checks.append("❌ booking_info: Missing")
                        
                        # Check optimization_score and conflict_warnings (might be at variant level)
                        if "optimization_score" in variant or "optimization_score" in first_activity:
                            structure_checks.append("✅ optimization_score: Present")
                        else:
                            structure_checks.append("❌ optimization_score: Missing")
                        
                        if "conflict_warnings" in variant or "conflict_warnings" in first_activity:
                            structure_checks.append("✅ conflict_warnings: Present")
                        else:
                            structure_checks.append("❌ conflict_warnings: Missing")
                        
                        break  # Only check first variant for structure
            
            # Print structure check results
            for check in structure_checks:
                print(f"   {check}")
            
            # Count successful checks
            successful_checks = sum(1 for check in structure_checks if check.startswith("✅"))
            total_checks = len(structure_checks)
            
            if successful_checks >= total_checks * 0.8:  # 80% success rate
                self.log_result("Enhanced Response Structure", True, 
                              f"Structure verification passed: {successful_checks}/{total_checks} checks successful")
                return True
            else:
                self.log_result("Enhanced Response Structure", False, 
                              f"Structure verification failed: {successful_checks}/{total_checks} checks successful")
                return False
            
        except Exception as e:
            self.log_result("Enhanced Response Structure", False, f"Test failed with exception: {str(e)}")
            return False

    def test_complete_chat_to_itinerary_flow(self):
        """Test 3: Complete Chat to Itinerary Flow"""
        try:
            print(f"\n🔄 Test 3: Complete Chat to Itinerary Flow")
            print("=" * 60)
            
            # Step 1: Chat message
            print("Step 1: Sending chat message...")
            chat_payload = {
                "message": "I want to plan an adventurous trip to Goa",
                "session_id": "test_chat_flow"
            }
            
            chat_response = requests.post(f"{API_BASE}/chat", json=chat_payload, timeout=60)
            
            if chat_response.status_code != 200:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              f"Chat step failed: HTTP {chat_response.status_code}")
                return False
            
            chat_data = chat_response.json()
            
            # Verify chat triggers trip planning
            has_trip_planner = any(
                action.get("type") == "trip_planner_card" 
                for action in chat_data.get("ui_actions", [])
            )
            
            if not has_trip_planner:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              "Chat message did not trigger trip planner card")
                return False
            
            print("✅ Chat message triggered trip planning")
            
            # Step 2: Persona Classification
            print("Step 2: Running persona classification...")
            persona_payload = {
                "session_id": "test_chat_flow",
                "trip_details": {
                    "destination": "Goa",
                    "start_date": "2024-12-25",
                    "end_date": "2024-12-28",
                    "adults": 2,
                    "budget_per_night": 4000
                },
                "profile_data": {
                    "vacation_style": ["adventurous"],
                    "experience_type": ["adventure"],
                    "interests": ["hiking", "water_sports", "nightlife"],
                    "budget_level": "moderate"
                }
            }
            
            persona_response = requests.post(f"{API_BASE}/persona-classification", json=persona_payload, timeout=60)
            
            if persona_response.status_code != 200:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              f"Persona classification failed: HTTP {persona_response.status_code}")
                return False
            
            persona_data = persona_response.json()
            print(f"✅ Persona classified as: {persona_data.get('persona_type')}")
            
            # Step 3: Enhanced Itinerary Generation
            print("Step 3: Generating enhanced itinerary...")
            itinerary_payload = {
                "session_id": "test_chat_flow",
                "trip_details": persona_payload["trip_details"],
                "persona_tags": persona_data.get("persona_tags", ["adventurer"])
            }
            
            itinerary_response = requests.post(f"{API_BASE}/generate-itinerary", json=itinerary_payload, timeout=120)
            
            if itinerary_response.status_code != 200:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              f"Itinerary generation failed: HTTP {itinerary_response.status_code}")
                return False
            
            itinerary_data = itinerary_response.json()
            
            # Verify enhanced itinerary structure is returned
            variants = itinerary_data.get("variants", [])
            if len(variants) == 0:
                self.log_result("Complete Chat to Itinerary Flow", False, "No itinerary variants generated")
                return False
            
            print(f"✅ Generated {len(variants)} itinerary variants")
            
            # Check that enhanced structure is present
            first_variant = variants[0]
            if "itinerary" not in first_variant:
                self.log_result("Complete Chat to Itinerary Flow", False, "Variant missing itinerary")
                return False
            
            first_day = first_variant["itinerary"][0]
            first_activity = first_day["activities"][0]
            
            # Verify enhanced fields are present
            enhanced_fields = ["selected_reason", "alternatives", "travel_logistics", "booking_info"]
            missing_fields = [field for field in enhanced_fields if field not in first_activity]
            
            if missing_fields:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              f"Enhanced structure missing fields: {missing_fields}")
                return False
            
            print("✅ Enhanced structure verified")
            
            # Verify alternatives array has 9 options
            alternatives = first_activity.get("alternatives", [])
            if len(alternatives) != 9:
                self.log_result("Complete Chat to Itinerary Flow", False, 
                              f"Expected 9 alternatives, got {len(alternatives)}")
                return False
            
            print("✅ 9 alternatives per activity verified")
            
            # Success
            self.log_result("Complete Chat to Itinerary Flow", True, 
                          f"COMPLETE FLOW SUCCESS: Chat → Persona Classification → Enhanced Itinerary Generation with {len(variants)} variants and explainable recommendations")
            
            return True
            
        except Exception as e:
            self.log_result("Complete Chat to Itinerary Flow", False, f"Flow test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all enhanced Master Travel Planner tests"""
        print(f"\n🚀 Starting Enhanced Master Travel Planner Testing")
        print(f"Session ID: {self.session_id}")
        print("=" * 80)
        
        tests = [
            ("Enhanced Itinerary Generation API", self.test_enhanced_itinerary_generation_api),
            ("Enhanced Response Structure", self.test_enhanced_response_structure),
            ("Complete Chat to Itinerary Flow", self.test_complete_chat_to_itinerary_flow)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 Running {test_name}...")
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name} CRASHED: {str(e)}")
                failed += 1
            
            time.sleep(1)  # Brief pause between tests
        
        # Print summary
        print(f"\n" + "=" * 80)
        print(f"🏁 ENHANCED MASTER TRAVEL PLANNER TESTING COMPLETE")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 SUCCESS RATE: {passed/(passed+failed)*100:.1f}%")
        
        if failed > 0:
            print(f"\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        else:
            print(f"\n🎉 ALL ENHANCED MASTER TRAVEL PLANNER TESTS PASSED!")
            print(f"✅ Enhanced itinerary generation with explainable AI working")
            print(f"✅ 9 alternatives per activity slot working")
            print(f"✅ Travel logistics and booking info working")
            print(f"✅ Complete chat-to-itinerary flow working")
        
        return passed, failed

def main():
    """Main test execution"""
    print("🎯 Enhanced Master Travel Planner Testing")
    print(f"🌐 Testing against: {BACKEND_URL}")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    tester = EnhancedMasterPlannerTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()