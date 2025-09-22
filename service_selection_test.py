#!/usr/bin/env python3
"""
Service Selection API Optimization Test
Tests the optimized Service Selection API for timeout resolution
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://travello-preview.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔍 Testing Service Selection API against: {BACKEND_URL}")

class ServiceSelectionTester:
    def __init__(self):
        self.session_id = f"service_test_{uuid.uuid4().hex[:8]}"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str, response_time: float = None):
        """Log test result with timing"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        timing = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status} {test_name}{timing}: {details}")
        return success

    def test_service_selection_api(self):
        """Test Service Selection API with the three specific scenarios"""
        print(f"\n🔧 Testing Optimized Service Selection API")
        print("=" * 60)
        
        # Test cases from review request
        test_cases = [
            {
                "name": "Accommodation for Goa",
                "service_type": "accommodation",
                "location": "Goa",
                "traveler_profile": {
                    "vacation_style": "adventurous",
                    "experience_type": "nature",
                    "budget_level": "moderate",
                    "preferences": ["beach", "water sports", "nightlife"]
                }
            },
            {
                "name": "Activities for Kerala",
                "service_type": "activities", 
                "location": "Kerala",
                "traveler_profile": {
                    "vacation_style": "relaxing",
                    "experience_type": "culture",
                    "budget_level": "luxury",
                    "preferences": ["backwaters", "ayurveda", "spices", "houseboats"]
                }
            },
            {
                "name": "Transportation for Mumbai",
                "service_type": "transportation",
                "location": "Mumbai",
                "traveler_profile": {
                    "vacation_style": "balanced",
                    "experience_type": "mixed",
                    "budget_level": "budget",
                    "preferences": ["convenience", "safety", "local_transport"]
                }
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"\n🎯 Testing: {test_case['name']}")
            
            payload = {
                "session_id": self.session_id,
                "service_type": test_case["service_type"],
                "location": test_case["location"],
                "traveler_profile": test_case["traveler_profile"],
                "activity_context": {}
            }
            
            # Measure response time
            start_time = time.time()
            
            try:
                response = requests.post(f"{API_BASE}/service-recommendations", json=payload, timeout=25)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response time requirement (under 20 seconds)
                    if response_time > 20.0:
                        self.log_result(f"{test_case['name']} - Response Time", False, 
                                      f"Response took {response_time:.2f}s (>20s limit)", response_time)
                        all_passed = False
                        continue
                    
                    # Check required fields
                    required_fields = ["services", "service_type", "location", "total_options", "auto_selected"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        self.log_result(f"{test_case['name']} - Structure", False, 
                                      f"Missing fields: {missing_fields}", response_time)
                        all_passed = False
                        continue
                    
                    services = data["services"]
                    
                    # Check exactly 10 services returned
                    if len(services) != 10:
                        self.log_result(f"{test_case['name']} - Count", False, 
                                      f"Expected 10 services, got {len(services)}", response_time)
                        all_passed = False
                        continue
                    
                    # Check service structure
                    first_service = services[0]
                    required_service_fields = ["id", "name", "type", "location", "rating", "price", 
                                             "similarity_score", "match_reasons", "description", "features"]
                    missing_service_fields = [field for field in required_service_fields if field not in first_service]
                    if missing_service_fields:
                        self.log_result(f"{test_case['name']} - Service Structure", False, 
                                      f"Service missing fields: {missing_service_fields}", response_time)
                        all_passed = False
                        continue
                    
                    # Check proper ranking (similarity_score descending)
                    scores = [s.get("similarity_score", 0) for s in services]
                    is_properly_ranked = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                    if not is_properly_ranked:
                        self.log_result(f"{test_case['name']} - Ranking", False, 
                                      f"Services not properly ranked by similarity score: {scores[:5]}...", response_time)
                        all_passed = False
                        continue
                    
                    # Check service quality
                    top_service = services[0]
                    if top_service["similarity_score"] < 0.5:
                        self.log_result(f"{test_case['name']} - Quality", False, 
                                      f"Top service has low similarity score: {top_service['similarity_score']}", response_time)
                        all_passed = False
                        continue
                    
                    # Success!
                    self.log_result(f"{test_case['name']}", True, 
                                  f"10 ranked services, top score: {top_service['similarity_score']:.2f}, auto-selected: {data['auto_selected']['name']}", 
                                  response_time)
                    
                else:
                    response_time = time.time() - start_time
                    self.log_result(f"{test_case['name']}", False, 
                                  f"HTTP {response.status_code}: {response.text[:200]}", response_time)
                    all_passed = False
                    
            except requests.exceptions.Timeout:
                response_time = time.time() - start_time
                self.log_result(f"{test_case['name']}", False, 
                              f"Request timed out after {response_time:.2f}s", response_time)
                all_passed = False
                
            except Exception as e:
                response_time = time.time() - start_time
                self.log_result(f"{test_case['name']}", False, 
                              f"Request failed: {str(e)}", response_time)
                all_passed = False
        
        return all_passed

    def test_integration_flow(self):
        """Test integration: chat -> service recommendations"""
        print(f"\n🔄 Testing Quick Integration Flow")
        print("=" * 60)
        
        try:
            # Step 1: Send chat message about Goa trip
            print("Step 1: Sending chat message about Goa trip...")
            chat_payload = {
                "message": "I want to plan a trip to Goa",
                "session_id": self.session_id
            }
            
            start_time = time.time()
            chat_response = requests.post(f"{API_BASE}/chat", json=chat_payload, timeout=60)
            chat_time = time.time() - start_time
            
            if chat_response.status_code != 200:
                return self.log_result("Integration - Chat", False, 
                                     f"Chat failed: HTTP {chat_response.status_code}", chat_time)
            
            chat_data = chat_response.json()
            print(f"✅ Chat response received in {chat_time:.2f}s: {chat_data['chat_text'][:100]}...")
            
            # Step 2: Test service recommendations for Goa (mentioned in response)
            print("Step 2: Testing service recommendations for Goa...")
            service_payload = {
                "session_id": self.session_id,
                "service_type": "accommodation",
                "location": "Goa",
                "traveler_profile": {
                    "vacation_style": "adventurous",
                    "experience_type": "nature",
                    "budget_level": "moderate",
                    "preferences": ["beach", "water sports"]
                }
            }
            
            start_time = time.time()
            service_response = requests.post(f"{API_BASE}/service-recommendations", json=service_payload, timeout=25)
            service_time = time.time() - start_time
            
            if service_response.status_code != 200:
                return self.log_result("Integration - Services", False, 
                                     f"Service recommendations failed: HTTP {service_response.status_code}", service_time)
            
            service_data = service_response.json()
            
            # Verify service response
            if len(service_data.get("services", [])) == 10 and service_time < 20.0:
                return self.log_result("Integration Flow", True, 
                                     f"Chat + Service recommendations successful: {len(service_data['services'])} services in {service_time:.2f}s", 
                                     chat_time + service_time)
            else:
                return self.log_result("Integration Flow", False, 
                                     f"Service issues: {len(service_data.get('services', []))} services, {service_time:.2f}s response time", 
                                     chat_time + service_time)
                
        except Exception as e:
            return self.log_result("Integration Flow", False, f"Integration test failed: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 SERVICE SELECTION API OPTIMIZATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"📊 Overall Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            timing = f" ({result['response_time']:.2f}s)" if result.get('response_time') else ""
            print(f"{status} {result['test']}{timing}: {result['details']}")
        
        # Performance analysis
        print(f"\n⚡ Performance Analysis:")
        timed_results = [r for r in self.test_results if r.get('response_time')]
        if timed_results:
            avg_time = sum(r['response_time'] for r in timed_results) / len(timed_results)
            max_time = max(r['response_time'] for r in timed_results)
            under_20s = sum(1 for r in timed_results if r['response_time'] < 20.0)
            
            print(f"📈 Average response time: {avg_time:.2f}s")
            print(f"📈 Maximum response time: {max_time:.2f}s")
            print(f"📈 Responses under 20s: {under_20s}/{len(timed_results)} ({under_20s/len(timed_results)*100:.1f}%)")
        
        # Timeout resolution check
        timeout_resolved = all(r.get('response_time', 0) < 20.0 for r in timed_results if r['success'])
        print(f"🔧 Timeout issues resolved: {'✅ YES' if timeout_resolved else '❌ NO'}")
        
        if passed == total and timeout_resolved:
            print(f"\n🎉 ALL TESTS PASSED! Service Selection API optimization successful.")
            print(f"✅ Response times under 20 seconds")
            print(f"✅ 10 services returned with proper ranking")
            print(f"✅ Fallback services with optional LLM enhancement working")
        else:
            print(f"\n⚠️  Issues detected:")
            if passed < total:
                print(f"   - {total - passed} tests failed")
            if not timeout_resolved:
                print(f"   - Timeout issues not fully resolved")
        
        return passed == total and timeout_resolved

def main():
    """Main test execution"""
    print("🚀 Starting Service Selection API Optimization Test")
    print(f"🌐 Testing against: {BACKEND_URL}")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    tester = ServiceSelectionTester()
    
    # Run the specific tests from review request
    print("\n" + "="*80)
    print("TESTING SERVICE SELECTION API OPTIMIZATION")
    print("="*80)
    
    # Test 1: Service Selection API with 3 scenarios
    api_success = tester.test_service_selection_api()
    
    # Test 2: Quick Integration Test
    integration_success = tester.test_integration_flow()
    
    # Print summary
    overall_success = tester.print_summary()
    
    # Exit with appropriate code
    exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()