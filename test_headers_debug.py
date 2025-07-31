#!/usr/bin/env python3
"""
Test script to debug headers being sent in OTP operations.
"""

import asyncio
import json
import logging
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from custom_components.my_verisure.api.client import MyVerisureClient
from custom_components.my_verisure.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError
)

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def print_headers(title: str, headers: dict):
    """Print headers in a formatted way."""
    print(f"\n{title}")
    print("=" * 50)
    for key, value in headers.items():
        if key.lower() in ['authorization', 'auth', 'security']:
            # Truncate sensitive headers
            if isinstance(value, str) and len(value) > 50:
                print(f"  {key}: {value[:50]}...")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")
    print()

async def test_headers_debug():
    """Test and debug headers in OTP operations."""
    
    # Get credentials from environment or use defaults
    user = os.getenv('VERISURE_USER', 'test_user')
    password = os.getenv('VERISURE_PASSWORD', 'test_password')
    
    print(f"Debugging headers for user: {user}")
    print("=" * 60)
    
    client = MyVerisureClient(user=user, password=password)
    
    try:
        # Connect to the API
        print("1. Connecting to My Verisure API...")
        await client.connect()
        print("   ✓ Connected successfully")
        
        # Show basic headers
        basic_headers = client._get_headers()
        print_headers("BASIC HEADERS (no token)", basic_headers)
        
        # Show native app headers
        native_headers = client._get_native_app_headers()
        print_headers("NATIVE APP HEADERS", native_headers)
        
        # Try to login
        print("2. Attempting login...")
        try:
            await client.login()
            print("   ✓ Login successful without OTP")
            return
        except MyVerisureOTPError as e:
            print(f"   ⚠ OTP required: {e}")
        except MyVerisureDeviceAuthorizationError as e:
            print(f"   ❌ Device authorization error: {e}")
            return
        except MyVerisureAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
            return
        
        # Show session headers after login attempt
        if client._session_data:
            session_headers = client._get_session_headers()
            print_headers("SESSION HEADERS (after login attempt)", session_headers)
        
        # Get available phones
        print("\n3. Getting available phone numbers...")
        phones = client.get_available_phones()
        if not phones:
            print("   ❌ No phone numbers available")
            return
        
        print(f"   ✓ Found {len(phones)} phone number(s):")
        for phone in phones:
            print(f"     - ID {phone.get('id')}: {phone.get('phone')}")
        
        # Select first phone
        selected_phone = phones[0]
        phone_id = selected_phone.get('id')
        print(f"\n4. Selecting phone ID {phone_id}...")
        
        if not client.select_phone(phone_id):
            print("   ❌ Failed to select phone")
            return
        
        print("   ✓ Phone selected successfully")
        
        # Show headers before sending OTP
        print("\n5. Headers before sending OTP...")
        otp_headers = client._get_session_headers()
        print_headers("HEADERS FOR OTP SEND", otp_headers)
        
        # Send OTP
        print("\n6. Sending OTP...")
        try:
            otp_data = client._otp_data
            record_id = 0  # Default to first phone
            otp_hash = otp_data.get('otp_hash')
            
            print(f"   OTP variables: recordId={record_id}, otpHash={otp_hash}")
            
            if await client.send_otp(record_id, otp_hash):
                print("   ✓ OTP sent successfully")
                print("   📱 Please check your phone for the SMS")
            else:
                print("   ❌ Failed to send OTP")
                return
        except Exception as e:
            print(f"   ❌ Error sending OTP: {e}")
            return
        
        # Wait for user to enter OTP
        print("\n7. Waiting for OTP verification...")
        print("   Please enter the OTP code received via SMS:")
        
        otp_code = input("   OTP Code: ").strip()
        
        if not otp_code:
            print("   ❌ No OTP code provided")
            return
        
        # Show headers before OTP verification
        print(f"\n8. Headers before OTP verification...")
        verification_headers = client._get_session_headers()
        
        # Add Security header manually to show what will be sent
        security_header = {
            "token": otp_code,
            "type": "OTP",
            "otpHash": otp_data.get('otp_hash')
        }
        verification_headers["Security"] = json.dumps(security_header)
        
        print_headers("HEADERS FOR OTP VERIFICATION", verification_headers)
        
        print(f"\n9. Verifying OTP code: {otp_code}")
        
        try:
            if await client.verify_otp(otp_code):
                print("   ✓ OTP verification successful")
                
                # Show final headers after verification
                final_headers = client._get_session_headers()
                print_headers("FINAL HEADERS (after OTP verification)", final_headers)
                
            else:
                print("   ❌ OTP verification failed")
                
        except MyVerisureDeviceAuthorizationError as e:
            print(f"   ❌ Device authorization failed: {e}")
            print("   This is the expected behavior for unauthorized devices")
            
        except MyVerisureOTPError as e:
            print(f"   ❌ OTP verification failed: {e}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\n10. Cleaning up...")
        await client.disconnect()
        print("   ✓ Disconnected")

if __name__ == "__main__":
    asyncio.run(test_headers_debug()) 