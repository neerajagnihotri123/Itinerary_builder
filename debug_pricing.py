#!/usr/bin/env python3
"""
Debug script to check actual response format from Dynamic Pricing API
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://trip-architect-4.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔍 Testing Dynamic Pricing API Response Format")
print(f"🔍 API Base: {API_BASE}")

# Sample test data from review request
sample_itinerary = [
    {
        "day": 1,
        "activities": [
            {
                "title": "Beach Visit",
                "category": "leisure",
                "location": "Goa",
                "duration": "3 hours"
            },
            {
                "title": "Water Sports",
                "category": "adventure", 
                "location": "Goa",
                "duration": "2 hours"
            }
        ]
    }
]

traveler_profile = {
    "budget_level": "moderate",
    "vacation_style": "adventurous",
    "propensity_to_pay": "medium",
    "spending_history": 15000
}

travel_dates = {
    "start_date": "2024-12-15",
    "end_date": "2024-12-18"
}

payload = {
    "session_id": "debug_pricing_session",
    "itinerary": sample_itinerary,
    "traveler_profile": traveler_profile,
    "travel_dates": travel_dates
}

try:
    response = requests.post(f"{API_BASE}/dynamic-pricing", json=payload, timeout=60)
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📋 Response Keys: {list(data.keys())}")
        print(f"\n📄 Full Response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {str(e)}")