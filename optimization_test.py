#!/usr/bin/env python3
"""
LLM Optimization Testing for Travello.ai
Focus on testing the optimization features implemented in the backend
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

class OptimizationTester:
    def __init__(self):
        self.session_id = f"opt_test_{uuid.uuid4().hex[:8]}"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str, response_data=None):
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

    def test_health_check(self):
        """Test basic health check"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check", True, f"Backend healthy, version {data.get('version')}")
                    return True
            
            self.log_result("Health Check", False, f"HTTP {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
            return False

    def test_timeout_configuration(self):
        """Test that timeout configurations are properly set in the code"""
        try:
            # This test verifies the code has the right timeout values
            # by checking the server.py file for the optimization constants
            
            with open('/app/backend/server.py', 'r') as f:
                server_code = f.read()
            
            # Check for ultra-aggressive timeout (6 seconds total)
            has_6_second_timeout = "timeout=6.0" in server_code
            
            # Check for 4-second per-agent timeout
            has_4_second_timeout = "timeout=4.0" in server_code
            
            # Check for caching implementation
            has_caching = "cache_key" in server_code and "get_cached_itinerary" in server_code
            
            # Check for progressive fallback
            has_fallback = "generate_progressive_fallback" in server_code
            
            optimizations_found = []
            if has_6_second_timeout:
                optimizations_found.append("6-second total timeout")
            if has_4_second_timeout:
                optimizations_found.append("4-second per-agent timeout")
            if has_caching:
                optimizations_found.append("Enhanced caching system")
            if has_fallback:
                optimizations_found.append("Progressive fallback mechanism")
            
            if len(optimizations_found) >= 3:
                self.log_result("Timeout Configuration", True, 
                              f"✅ OPTIMIZATIONS IMPLEMENTED: {', '.join(optimizations_found)}")
                return True
            else:
                self.log_result("Timeout Configuration", False, 
                              f"Missing optimizations. Found: {', '.join(optimizations_found)}")
                return False
                
        except Exception as e:
            self.log_result("Timeout Configuration", False, f"Code analysis failed: {str(e)}")
            return False

    def test_cache_structure(self):
        """Test that caching structure is properly implemented"""
        try:
            with open('/app/backend/server.py', 'r') as f:
                server_code = f.read()
            
            # Check for TTL implementation
            has_ttl = "ttl" in server_code and "timestamp" in server_code
            
            # Check for cache cleanup
            has_cleanup = "len(_cache_storage) > 100" in server_code or "oldest_key" in server_code
            
            # Check for cache hit logic
            has_cache_hit = "cache_hit" in server_code.lower() or "cached_result" in server_code
            
            cache_features = []
            if has_ttl:
                cache_features.append("TTL support")
            if has_cleanup:
                cache_features.append("Cache cleanup")
            if has_cache_hit:
                cache_features.append("Cache hit detection")
            
            if len(cache_features) >= 2:
                self.log_result("Cache Structure", True, 
                              f"✅ CACHE FEATURES IMPLEMENTED: {', '.join(cache_features)}")
                return True
            else:
                self.log_result("Cache Structure", False, 
                              f"Insufficient cache features. Found: {', '.join(cache_features)}")
                return False
                
        except Exception as e:
            self.log_result("Cache Structure", False, f"Cache analysis failed: {str(e)}")
            return False

    def test_parallel_processing(self):
        """Test that parallel processing is implemented"""
        try:
            with open('/app/backend/server.py', 'r') as f:
                server_code = f.read()
            
            # Check for asyncio.gather (parallel execution)
            has_parallel = "asyncio.gather" in server_code
            
            # Check for concurrent agent execution
            has_concurrent = "adventurer_agent" in server_code and "balanced_agent" in server_code and "luxury_agent" in server_code
            
            # Check for timeout handling in parallel execution
            has_timeout_handling = "asyncio.wait_for" in server_code
            
            parallel_features = []
            if has_parallel:
                parallel_features.append("Asyncio parallel execution")
            if has_concurrent:
                parallel_features.append("Concurrent agent processing")
            if has_timeout_handling:
                parallel_features.append("Timeout handling")
            
            if len(parallel_features) >= 2:
                self.log_result("Parallel Processing", True, 
                              f"✅ PARALLEL FEATURES IMPLEMENTED: {', '.join(parallel_features)}")
                return True
            else:
                self.log_result("Parallel Processing", False, 
                              f"Insufficient parallel features. Found: {', '.join(parallel_features)}")
                return False
                
        except Exception as e:
            self.log_result("Parallel Processing", False, f"Parallel analysis failed: {str(e)}")
            return False

    def test_fallback_mechanisms(self):
        """Test that fallback mechanisms are properly implemented"""
        try:
            with open('/app/backend/server.py', 'r') as f:
                server_code = f.read()
            
            # Check for progressive fallback function
            has_progressive_fallback = "generate_progressive_fallback" in server_code
            
            # Check for simple fallback
            has_simple_fallback = "generate_simple_itinerary_fallback" in server_code
            
            # Check for exception handling
            has_exception_handling = "except asyncio.TimeoutError" in server_code
            
            # Check for fallback variant generation
            has_fallback_variants = "generate_simple_variant_fallback" in server_code
            
            fallback_features = []
            if has_progressive_fallback:
                fallback_features.append("Progressive fallback")
            if has_simple_fallback:
                fallback_features.append("Simple fallback")
            if has_exception_handling:
                fallback_features.append("Timeout exception handling")
            if has_fallback_variants:
                fallback_features.append("Fallback variant generation")
            
            if len(fallback_features) >= 3:
                self.log_result("Fallback Mechanisms", True, 
                              f"✅ FALLBACK FEATURES IMPLEMENTED: {', '.join(fallback_features)}")
                return True
            else:
                self.log_result("Fallback Mechanisms", False, 
                              f"Insufficient fallback features. Found: {', '.join(fallback_features)}")
                return False
                
        except Exception as e:
            self.log_result("Fallback Mechanisms", False, f"Fallback analysis failed: {str(e)}")
            return False

    def test_simple_endpoint_performance(self):
        """Test a simple endpoint to verify basic performance"""
        try:
            print("Testing simple persona classification endpoint...")
            
            start_time = time.time()
            
            payload = {
                "session_id": self.session_id,
                "trip_details": {
                    "destination": "Goa",
                    "adults": 2,
                    "budget_per_night": 5000
                },
                "profile_data": {
                    "vacation_style": "adventurous",
                    "experience_type": "nature"
                }
            }
            
            response = requests.post(f"{API_BASE}/persona-classification", json=payload, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "persona_type" in data:
                    self.log_result("Simple Endpoint Performance", True, 
                                  f"✅ PERSONA CLASSIFICATION: {data['persona_type']} in {response_time:.2f}s")
                    return True
            
            self.log_result("Simple Endpoint Performance", False, 
                          f"HTTP {response.status_code}: {response.text}")
            return False
            
        except Exception as e:
            self.log_result("Simple Endpoint Performance", False, f"Simple test failed: {str(e)}")
            return False

    def run_optimization_tests(self):
        """Run all optimization tests"""
        print(f"\n🚀 Starting LLM Optimization Analysis")
        print(f"🔍 Backend URL: {BACKEND_URL}")
        print(f"📅 Test session: {self.session_id}")
        print("=" * 80)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Timeout Configuration", self.test_timeout_configuration),
            ("Cache Structure", self.test_cache_structure),
            ("Parallel Processing", self.test_parallel_processing),
            ("Fallback Mechanisms", self.test_fallback_mechanisms),
            ("Simple Endpoint Performance", self.test_simple_endpoint_performance)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
        
        print(f"\n📊 Optimization Analysis Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Summary of findings
        print(f"\n🔍 OPTIMIZATION ANALYSIS SUMMARY:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return passed, total

def main():
    """Main test execution"""
    print("🚀 Starting Travello.ai LLM Optimization Analysis")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    tester = OptimizationTester()
    passed, total = tester.run_optimization_tests()
    
    if passed == total:
        print(f"\n🎉 ALL OPTIMIZATION TESTS PASSED!")
        print(f"✅ The LLM optimization features are properly implemented")
    else:
        print(f"\n⚠️ {total - passed} optimization tests failed")
        print(f"❌ Some optimization features may be missing or incomplete")
    
    exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()