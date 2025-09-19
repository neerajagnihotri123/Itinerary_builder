#!/usr/bin/env python3
"""
Debug script to check actual response format from Checkout Cart API
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://trip-architect-4.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔍 Testing Checkout Cart API Response Format")
print(f"🔍 API Base: {API_BASE}")

# Sample pricing data (would come from dynamic pricing API)
pricing_data = {
    "base_total": 7000,
    "adjusted_total": 10500,
    "final_total": 9975.0,
    "total_savings": -2975.0,
    "line_items": [
        {
            "id": "day_1_Beach Visit",
            "title": "Beach Visit",
            "category": "leisure",
            "base_price": 1500,
            "current_price": 2250
        },
        {
            "id": "day_1_Water Sports",
            "title": "Water Sports",
            "category": "adventure",
            "base_price": 1500,
            "current_price": 2250
        }
    ],
    "discounts_applied": [
        {
            "type": "loyalty",
            "tier": "bronze",
            "amount": 525.0,
            "description": "Bronze member discount"
        }
    ]
}

sample_itinerary = [
    {
        "day": 1,
        "activities": [
            {"title": "Beach Visit", "category": "leisure", "location": "Goa"},
            {"title": "Water Sports", "category": "adventure", "location": "Goa"}
        ]
    }
]

user_details = {
    "name": "Rajesh Kumar",
    "email": "rajesh.kumar@email.com",
    "phone": "+91-9876543210",
    "travelers": 2
}

payload = {
    "session_id": "debug_cart_session",
    "pricing_data": pricing_data,
    "itinerary": sample_itinerary,
    "user_details": user_details
}

try:
    response = requests.post(f"{API_BASE}/create-checkout-cart", json=payload, timeout=60)
    
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