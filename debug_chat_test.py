import requests
import json

def test_specific_chat_query(message, description):
    """Test a specific chat query and show detailed response"""
    print(f"\n{'='*60}")
    print(f"🔍 TESTING: {description}")
    print(f"📝 Message: '{message}'")
    print(f"{'='*60}")
    
    url = "https://ai-travel-planner-4.preview.emergentagent.com/api/chat"
    headers = {'Content-Type': 'application/json'}
    
    chat_data = {
        "message": message,
        "session_id": f"debug_session_{hash(message) % 1000}",
        "user_profile": {},
        "trip_details": {}
    }
    
    try:
        response = requests.post(url, json=chat_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Chat Text: '{data.get('chat_text', 'N/A')}'")
            print(f"🎨 UI Actions Count: {len(data.get('ui_actions', []))}")
            
            # Analyze UI actions in detail
            ui_actions = data.get('ui_actions', [])
            for i, action in enumerate(ui_actions):
                print(f"\n   Action {i+1}:")
                print(f"     Type: {action.get('type', 'N/A')}")
                if action.get('type') == 'card_add':
                    payload = action.get('payload', {})
                    print(f"     Category: {payload.get('category', 'N/A')}")
                    print(f"     Title: {payload.get('title', 'N/A')}")
                    if payload.get('rating'):
                        print(f"     Rating: {payload.get('rating')}")
                    if payload.get('price_estimate'):
                        print(f"     Price: {payload.get('price_estimate')}")
                elif action.get('type') == 'question_chip':
                    payload = action.get('payload', {})
                    print(f"     Question: {payload.get('question', 'N/A')}")
                elif action.get('type') == 'prompt':
                    payload = action.get('payload', {})
                    chips = payload.get('chips', [])
                    print(f"     Chips: {len(chips)} chips")
                    for chip in chips[:2]:  # Show first 2
                        print(f"       - {chip.get('label', 'N/A')}")
            
            print(f"\n📊 Analytics Tags: {data.get('analytics_tags', [])}")
            
            return data
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🚀 Debug Chat Testing - Specific Review Request Scenarios")
    
    # Test the exact scenarios from review request
    test_cases = [
        ("tell me about kerala", "Should generate destination cards"),
        ("plan a trip to manali", "Should trigger trip planning flow"),
        ("i want accommodations in goa", "Should generate hotel cards only"),
        ("show me hotels in andaman", "Should generate hotel cards"),
        ("what are popular destinations in india", "Should show destination options"),
        ("i want to visit rishikesh for adventure", "Should generate destination/activity cards")
    ]
    
    for message, description in test_cases:
        test_specific_chat_query(message, description)
    
    print(f"\n{'='*60}")
    print("🎯 SUMMARY")
    print("The system appears to be working but not generating the expected card types.")
    print("This suggests the conversation manager is prioritizing slot-filling over content generation.")
    print("The LLM agents are working but may need adjustment for direct content queries.")

if __name__ == "__main__":
    main()