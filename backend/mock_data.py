"""
Mock data for the multi-agent travel system
"""

# Mock destinations data
MOCK_DESTINATIONS = [
    {
        "id": "rishikesh_uttarakhand",
        "name": "Rishikesh",
        "state": "Uttarakhand",
        "country": "India",
        "category": ["Adventure", "Spiritual", "Nature"],
        "rating": 4.7,
        "hero_image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
        "pitch": "The Yoga Capital of the World, offering spiritual experiences, adventure sports, and scenic Himalayan views.",
        "highlights": ["White water rafting", "Bungee jumping", "Yoga retreats", "Ganga Aarti", "Laxman Jhula"],
        "coordinates": {"lat": 30.0869, "lng": 78.2676}
    },
    {
        "id": "manali_himachal",
        "name": "Manali",
        "state": "Himachal Pradesh", 
        "country": "India",
        "category": ["Adventure", "Mountains", "Honeymoon"],
        "rating": 4.6,
        "hero_image": "https://images.unsplash.com/photo-1605640840605-14ac1855827b?w=800&h=600&fit=crop",
        "pitch": "A stunning hill station perfect for adventure activities, mountain views, and romantic getaways.",
        "highlights": ["Solang Valley", "Rohtang Pass", "Paragliding", "Snow activities", "Hadimba Temple"],
        "coordinates": {"lat": 32.2396, "lng": 77.1887}
    },
    {
        "id": "andaman_islands",
        "name": "Andaman Islands",
        "state": "Andaman and Nicobar Islands",
        "country": "India",
        "category": ["Beach", "Marine Adventure", "Honeymoon"],
        "rating": 4.8,
        "hero_image": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=800&h=600&fit=crop",
        "pitch": "Pristine beaches, crystal clear waters, and amazing marine life for the perfect tropical getaway.",
        "highlights": ["Radhanagar Beach", "Scuba diving", "Coral reefs", "Neil Island", "Cellular Jail"],
        "coordinates": {"lat": 11.7401, "lng": 92.6586}
    },
    {
        "id": "kerala_backwaters",
        "name": "Kerala",
        "state": "Kerala",
        "country": "India", 
        "category": ["Backwaters", "Cultural", "Ayurveda"],
        "rating": 4.7,
        "hero_image": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&h=600&fit=crop",
        "pitch": "God's Own Country with serene backwaters, lush greenery, and rich cultural heritage.",
        "highlights": ["Houseboats", "Alleppey backwaters", "Ayurvedic spas", "Munnar tea gardens", "Kathakali dance"],
        "coordinates": {"lat": 10.8505, "lng": 76.2711}
    }
]

# Mock hotels data
MOCK_HOTELS = [
    {
        "id": "rishikesh_riverside_resort",
        "name": "Ganga Riverside Resort",
        "destination_id": "rishikesh_uttarakhand",
        "type": "Resort",
        "rating": 4.5,
        "price_per_night": 4500,
        "location": "Rishikesh, Uttarakhand",
        "description": "Luxury resort on the banks of River Ganga with spiritual and adventure experiences.",
        "amenities": ["River view", "Spa", "Yoga classes", "Adventure sports", "Restaurant", "Free WiFi"],
        "coordinates": {"lat": 30.0869, "lng": 78.2676}
    },
    {
        "id": "manali_snow_peak_hotel",
        "name": "Snow Peak Hotel",
        "destination_id": "manali_himachal",
        "type": "Hotel",
        "rating": 4.3,
        "price_per_night": 3200,
        "location": "Mall Road, Manali",
        "description": "Cozy mountain hotel with stunning valley views and easy access to adventure activities.",
        "amenities": ["Mountain view", "Heating", "Restaurant", "Room service", "Parking", "Free WiFi"],
        "coordinates": {"lat": 32.2396, "lng": 77.1887}
    },
    {
        "id": "andaman_beach_resort",
        "name": "Coral Bay Beach Resort",
        "destination_id": "andaman_islands",
        "type": "Beach Resort",
        "rating": 4.7,
        "price_per_night": 8500,
        "location": "Havelock Island, Andaman",
        "description": "Luxury beachfront resort with water sports and diving facilities.",
        "amenities": ["Beach access", "Diving center", "Spa", "Pool", "Restaurant", "Water sports", "Free WiFi"],
        "coordinates": {"lat": 11.7401, "lng": 92.6586}
    },
    {
        "id": "kerala_backwater_villa",
        "name": "Backwater Heritage Villa",
        "destination_id": "kerala_backwaters",
        "type": "Heritage Villa",
        "rating": 4.6,
        "price_per_night": 6200,
        "location": "Alleppey, Kerala",
        "description": "Traditional Kerala villa with houseboat access and Ayurvedic treatments.",
        "amenities": ["Backwater view", "Ayurvedic spa", "Traditional architecture", "Houseboat trips", "Restaurant", "Free WiFi"],
        "coordinates": {"lat": 10.8505, "lng": 76.2711}
    }
]

# Mock tours data
MOCK_TOURS = [
    {
        "id": "rishikesh_adventure_tour",
        "title": "Rishikesh Adventure Package",
        "location": "Rishikesh, Uttarakhand",
        "price": 2500,
        "duration": "Full Day",
        "rating": 4.8,
        "reviews": 1247,
        "description": "Complete adventure experience including rafting, bungee jumping, and yoga.",
        "highlights": ["White water rafting", "Bungee jumping", "Yoga session", "Ganga Aarti", "Lunch included"],
        "includes": ["Transportation", "All activities", "Lunch", "Safety equipment", "Professional guide"]
    },
    {
        "id": "manali_solang_tour",
        "title": "Solang Valley Adventure Tour",
        "location": "Solang Valley, Manali",
        "price": 1800,
        "duration": "Half Day",
        "rating": 4.6,
        "reviews": 892,
        "description": "Thrilling adventure activities in the beautiful Solang Valley.",
        "highlights": ["Paragliding", "Zorbing", "ATV rides", "Cable car", "Mountain views"],
        "includes": ["Transportation", "Activity tickets", "Safety gear", "Refreshments"]
    },
    {
        "id": "andaman_island_hopping",
        "title": "Andaman Island Hopping Tour",
        "location": "Andaman Islands",
        "price": 4200,
        "duration": "3 Days 2 Nights",
        "rating": 4.9,
        "reviews": 567,
        "description": "Explore multiple islands with snorkeling, diving, and beach activities.",
        "highlights": ["Neil Island", "Ross Island", "Snorkeling", "Glass boat ride", "Beach time"],
        "includes": ["Inter-island transfers", "Accommodation", "Meals", "Activities", "Guide"]
    }
]

# Mock activities data  
MOCK_ACTIVITIES = [
    {
        "id": "rishikesh_river_rafting",
        "title": "Ganga River Rafting",
        "location": "Rishikesh, Uttarakhand",
        "price": 800,
        "duration": "2-3 hours",
        "rating": 4.7,
        "reviews": 2156,
        "description": "Exciting white water rafting experience on the holy Ganga river.",
        "category": "Adventure Sports"
    },
    {
        "id": "manali_paragliding",
        "title": "Paragliding in Solang Valley",
        "location": "Solang Valley, Manali",
        "price": 1200,
        "duration": "15-20 minutes",
        "rating": 4.8,
        "reviews": 1845,
        "description": "Soar above the Himalayan valleys with professional instructors.",
        "category": "Adventure Sports"
    },
    {
        "id": "andaman_scuba_diving",
        "title": "Scuba Diving Experience",
        "location": "Havelock Island, Andaman",
        "price": 3500,
        "duration": "30 minutes",
        "rating": 4.9,
        "reviews": 1150,
        "description": "Discover the underwater world with coral reefs and tropical fish.",
        "category": "Marine Adventure"
    },
    {
        "id": "kerala_houseboat_cruise",
        "title": "Backwaters Houseboat Cruise",
        "location": "Alleppey, Kerala",
        "price": 2200,
        "duration": "4 hours",
        "rating": 4.8,
        "reviews": 987,
        "description": "Peaceful cruise through Kerala's famous backwaters on traditional houseboat.",
        "category": "Cultural Experience"
    }
]