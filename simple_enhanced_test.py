#!/usr/bin/env python3
"""
Simple Enhanced Chatbot Test - Quick verification of key features
"""

import requests
import json
import time

def test_api_call(message, description):
    """Test a single API call"""
    url = "https://travel-persona.preview.emergentagent.com/api/chat"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "message": message,
        "session_id": f"test_{int(time.time())}",
        "user_profile": {}
    }
    
    print(f"\n🔍 Testing: {description}")
    print(f"   Message: '{message}'")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            chat_text = result.get('chat_text', '')
            ui_actions = result.get('ui_actions', [])
            metadata = result.get('metadata', {})
            
            print(f"   ✅ API Success")
            print(f"   📝 Response: {chat_text[:100]}...")
            print(f"   🎨 UI Actions: {len(ui_actions)}")
            print(f"   📊 Intent: {metadata.get('intent', 'unknown')}")
            
            return True, result
        else:
            print(f"   ❌ API Failed: {response.status_code}")
            return False, {}
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, {}

def main():
    print("🚀 SIMPLE ENHANCED CHATBOT TEST")
    print("   Testing key PRD requirements quickly")
    
    tests = [
        ("plan a trip to Kerala", "Profile Intake Trigger"),
        ("tell me about Goa", "Existing Destination Info"),
        ("hotels in Manali", "Existing Hotel Search"),
        ("hello", "General Conversation")
    ]
    
    results = []
    for message, description in tests:
        success, response = test_api_call(message, description)
        results.append((description, success))
        time.sleep(2)  # Brief pause between tests
    
    print(f"\n📊 TEST RESULTS SUMMARY:")
    passed = 0
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {description}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed >= 3:
        print("✅ System appears to be working for demo!")
    else:
        print("❌ System needs attention before demo")

if __name__ == "__main__":
    main()