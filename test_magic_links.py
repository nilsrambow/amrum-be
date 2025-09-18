#!/usr/bin/env python3
"""
Test script for magic link functionality
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8888"

def test_magic_link_flow():
    """Test the complete magic link flow"""
    
    print("🧪 Testing Magic Link Functionality")
    print("=" * 50)
    
    # 1. Create a guest
    print("\n1. Creating a guest...")
    guest_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/guests", json=guest_data)
    if response.status_code != 200:
        print(f"❌ Failed to create guest: {response.text}")
        return
    
    guest = response.json()
    print(f"✅ Guest created: {guest['first_name']} {guest['last_name']}")
    
    # 2. Create a booking
    print("\n2. Creating a booking...")
    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)
    
    booking_data = {
        "guest_id": guest["id"],
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat()
    }
    
    response = requests.post(f"{BASE_URL}/bookings", json=booking_data)
    if response.status_code != 200:
        print(f"❌ Failed to create booking: {response.text}")
        return
    
    booking = response.json()
    print(f"✅ Booking created: ID {booking['id']}")
    print(f"   Check-in: {booking['check_in']}")
    print(f"   Check-out: {booking['check_out']}")
    print(f"   Access token: {booking.get('access_token', 'None')}")
    
    # 3. Get token information
    print("\n3. Getting token information...")
    response = requests.get(f"{BASE_URL}/booking/{booking['id']}/token")
    if response.status_code != 200:
        print(f"❌ Failed to get token info: {response.text}")
        return
    
    token_info = response.json()
    print(f"✅ Token info retrieved:")
    print(f"   Token: {token_info['token']}")
    print(f"   Expires: {token_info['expires_at']}")
    
    # 4. Test guest access via magic link
    print("\n4. Testing guest access via magic link...")
    magic_link = f"{BASE_URL}/guest/booking/{token_info['token']}"
    print(f"   Magic link: {magic_link}")
    
    response = requests.get(magic_link)
    if response.status_code != 200:
        print(f"❌ Failed to access booking via magic link: {response.text}")
        return
    
    guest_booking = response.json()
    print(f"✅ Guest booking access successful:")
    print(f"   Guest name: {guest_booking['guest_name']}")
    print(f"   Guest email: {guest_booking['guest_email']}")
    print(f"   Status: {guest_booking['status']}")
    
    # 5. Test adding meter readings via magic link
    print("\n5. Testing meter readings via magic link...")
    readings_data = {
        "booking_id": booking["id"],
        "electricity_start": 100.5,
        "electricity_end": 150.2,
        "gas_start": 50.0,
        "gas_end": 75.3,
        "firewood_boxes": 2
    }
    
    response = requests.post(f"{magic_link}/readings", json=readings_data)
    if response.status_code != 200:
        print(f"❌ Failed to add meter readings: {response.text}")
        return
    
    meter_reading = response.json()
    print(f"✅ Meter readings added successfully:")
    print(f"   Electricity: {meter_reading['electricity_start']} - {meter_reading['electricity_end']}")
    print(f"   Gas: {meter_reading['gas_start']} - {meter_reading['gas_end']}")
    print(f"   Firewood: {meter_reading['firewood_boxes']} boxes")
    
    # 6. Test getting meter readings via magic link
    print("\n6. Testing get meter readings via magic link...")
    response = requests.get(f"{magic_link}/readings")
    if response.status_code != 200:
        print(f"❌ Failed to get meter readings: {response.text}")
        return
    
    retrieved_readings = response.json()
    print(f"✅ Meter readings retrieved successfully")
    
    # 7. Test invalid token
    print("\n7. Testing invalid token...")
    invalid_link = f"{BASE_URL}/guest/booking/invalid_token_123"
    response = requests.get(invalid_link)
    if response.status_code == 404:
        print("✅ Invalid token correctly rejected")
    else:
        print(f"❌ Invalid token not properly handled: {response.status_code}")
    
    print("\n🎉 Magic link functionality test completed successfully!")

if __name__ == "__main__":
    test_magic_link_flow() 