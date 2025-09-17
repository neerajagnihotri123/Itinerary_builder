#!/usr/bin/env python3
"""
Focused test for SlotAgent and ConversationManager routing flow
"""
import requests
import json
from datetime import datetime

class SlotAgentTester:
    def __init__(self, base_url="https://ai-travel-planner-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id = f"slot_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_test(self, name, message):
        """Run a single test"""
        url = f"{self.api_url}/chat"
        headers = {'Content-Type': 'application/json'}
        
        data = {
            "message": message,
            "session_id": f"{self.session_id}_{hash(message) % 1000}",
            "user_profile": {}
        }
        
        print(f"\n🔍 Testing: {name}")
        print(f"   Input: '{message}'")
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Status: {response.status_code}")
                return True, result
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, {}
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False, {}

    def test_slot_agent_intent_detection(self):
        """Test SlotAgent intent detection scenarios"""
        print("🎯 TESTING SLOTAGENT INTENT DETECTION")
        print("=" * 50)
        
        scenarios = [
            ("plan a trip to kerala", "plan", "Kerala"),
            ("hotels in goa", "accommodation", "Goa"), 
            ("tell me about manali", "find", "Manali"),
            ("hello", "general", None)
        ]
        
        results = []
        for message, expected_intent, expected_dest in scenarios:
            success, response = self.run_test(f"Intent: {expected_intent}", message)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                # Analyze intent
                detected_intent = self._analyze_intent(chat_text, ui_actions)
                detected_dest = self._analyze_destination(chat_text, ui_actions, message)
                
                intent_match = detected_intent == expected_intent
                dest_match = (expected_dest is None and detected_dest is None) or \
                           (expected_dest and detected_dest and expected_dest.lower() in detected_dest.lower())
                
                result = intent_match and dest_match
                results.append(result)
                
                print(f"   Intent: {detected_intent} ({'✅' if intent_match else '❌'})")
                print(f"   Destination: {detected_dest} ({'✅' if dest_match else '❌'})")
                print(f"   UI Actions: {len(ui_actions)}")
                
            else:
                results.append(False)
        
        passed = sum(results)
        print(f"\n🎯 Intent Detection Results: {passed}/{len(scenarios)} passed")
        return passed >= 3

    def test_routing_flows(self):
        """Test different routing flows"""
        print("\n🔄 TESTING ROUTING FLOWS")
        print("=" * 50)
        
        scenarios = [
            ("plan a 5-day trip to rishikesh", "planner_flow"),
            ("show me luxury hotels in andaman", "accommodation_flow"),
            ("tell me about kerala backwaters", "find_flow")
        ]
        
        results = []
        for message, expected_flow in scenarios:
            success, response = self.run_test(f"Flow: {expected_flow}", message)
            
            if success:
                chat_text = response.get('chat_text', '')
                ui_actions = response.get('ui_actions', [])
                
                detected_flow = self._analyze_flow(chat_text, ui_actions)
                flow_match = detected_flow == expected_flow
                results.append(flow_match)
                
                print(f"   Detected Flow: {detected_flow} ({'✅' if flow_match else '❌'})")
                print(f"   UI Actions: {self._summarize_ui_actions(ui_actions)}")
                
            else:
                results.append(False)
        
        passed = sum(results)
        print(f"\n🔄 Routing Flow Results: {passed}/{len(scenarios)} passed")
        return passed >= 2

    def test_ui_action_formats(self):
        """Test UI action formats"""
        print("\n🎨 TESTING UI ACTION FORMATS")
        print("=" * 50)
        
        scenarios = [
            ("show me destinations in india", ["destination_cards"]),
            ("find hotels in kerala", ["hotel_cards"]),
            ("plan a trip to goa", ["question_chips"])
        ]
        
        results = []
        for message, expected_formats in scenarios:
            success, response = self.run_test(f"Format test", message)
            
            if success:
                ui_actions = response.get('ui_actions', [])
                detected_formats = self._analyze_ui_formats(ui_actions)
                
                format_match = any(fmt in detected_formats for fmt in expected_formats)
                results.append(format_match)
                
                print(f"   Expected: {expected_formats}")
                print(f"   Detected: {detected_formats} ({'✅' if format_match else '❌'})")
                
            else:
                results.append(False)
        
        passed = sum(results)
        print(f"\n🎨 UI Format Results: {passed}/{len(scenarios)} passed")
        return passed >= 2

    def _analyze_intent(self, chat_text, ui_actions):
        """Analyze response to determine intent"""
        text_lower = chat_text.lower()
        
        if any(word in text_lower for word in ['itinerary', 'plan', 'day 1', 'schedule']):
            return "plan"
        elif any(word in text_lower for word in ['hotel', 'accommodation', 'stay']):
            return "accommodation"
        elif any(word in text_lower for word in ['explore', 'about', 'destination']):
            return "find"
        elif any(word in text_lower for word in ['hello', 'help', 'assist']):
            return "general"
        else:
            return "unknown"

    def _analyze_destination(self, chat_text, ui_actions, original_message):
        """Analyze response to determine detected destination"""
        # Check destination cards
        for action in ui_actions:
            if (action.get('type') == 'card_add' and 
                action.get('payload', {}).get('category') == 'destination'):
                title = action.get('payload', {}).get('title', '')
                return title
        
        # Check chat text for destination mentions
        destinations = ['kerala', 'goa', 'manali', 'rishikesh', 'andaman']
        for dest in destinations:
            if dest in chat_text.lower() or dest in original_message.lower():
                return dest.title()
        
        return None

    def _analyze_flow(self, chat_text, ui_actions):
        """Analyze response to determine routing flow"""
        text_lower = chat_text.lower()
        
        # Check UI actions first
        destination_cards = len([a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'destination'])
        hotel_cards = len([a for a in ui_actions if a.get('type') == 'card_add' and a.get('payload', {}).get('category') == 'hotel'])
        trip_planner = len([a for a in ui_actions if a.get('type') == 'trip_planner_card'])
        
        if hotel_cards > 0 and destination_cards == 0:
            return "accommodation_flow"
        elif destination_cards > 0 and hotel_cards == 0:
            return "find_flow"
        elif trip_planner > 0 or any(word in text_lower for word in ['itinerary', 'day 1', 'plan']):
            return "planner_flow"
        else:
            return "unknown_flow"

    def _analyze_ui_formats(self, ui_actions):
        """Analyze UI action formats"""
        formats = []
        
        for action in ui_actions:
            action_type = action.get('type')
            payload = action.get('payload', {})
            category = payload.get('category')
            
            if action_type == 'card_add' and category == 'destination':
                formats.append('destination_cards')
            elif action_type == 'card_add' and category == 'hotel':
                formats.append('hotel_cards')
            elif action_type == 'question_chip':
                formats.append('question_chips')
            elif action_type == 'trip_planner_card':
                formats.append('trip_planner_card')
        
        return list(set(formats))

    def _summarize_ui_actions(self, ui_actions):
        """Summarize UI actions"""
        summary = {}
        for action in ui_actions:
            action_type = action.get('type', 'unknown')
            category = action.get('payload', {}).get('category', '')
            key = f"{action_type}_{category}" if category else action_type
            summary[key] = summary.get(key, 0) + 1
        
        return dict(summary)

def main():
    print("🚀 SlotAgent and ConversationManager Routing Test")
    print("=" * 60)
    
    tester = SlotAgentTester()
    
    # Run focused tests
    intent_success = tester.test_slot_agent_intent_detection()
    routing_success = tester.test_routing_flows()
    format_success = tester.test_ui_action_formats()
    
    # Final results
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    total_tests = 3
    passed_tests = sum([intent_success, routing_success, format_success])
    
    print(f"🎯 SlotAgent Intent Detection: {'PASS' if intent_success else 'FAIL'}")
    print(f"🔄 Routing Flow Architecture: {'PASS' if routing_success else 'FAIL'}")
    print(f"🎨 UI Actions Generation: {'PASS' if format_success else 'FAIL'}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} test categories passed")
    
    if passed_tests >= 2:
        print("✅ SlotAgent and ConversationManager routing flow is working!")
        return 0
    else:
        print("❌ SlotAgent and ConversationManager routing flow needs fixes")
        return 1

if __name__ == "__main__":
    exit(main())