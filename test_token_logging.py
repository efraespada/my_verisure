#!/usr/bin/env python3
"""
Test script to verify that hash and refresh tokens are being logged correctly after OTP verification.
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

async def test_hash_logging():
    """Test that hash and refresh tokens are being logged correctly."""
    
    # Get credentials from environment or use defaults
    user = os.getenv('VERISURE_USER', 'test_user')
    password = os.getenv('VERISURE_PASSWORD', 'test_password')
    
    print(f"Testing token logging for user: {user}")
    print("=" * 60)
    
    client = MyVerisureClient(user=user, password=password)
    
    try:
        # Connect to the API
        print("1. Connecting to My Verisure API...")
        await client.connect()
        print("   ✓ Connected successfully")
        
        # Try to login
        print("\n2. Attempting login...")
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
        
        # Send OTP
        print("\n5. Sending OTP...")
        try:
            otp_data = client._otp_data
            record_id = phone_id
            otp_hash = otp_data.get('otp_hash')
            
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
        print("\n6. Waiting for OTP verification...")
        print("   Please enter the OTP code received via SMS:")
        
        otp_code = input("   OTP Code: ").strip()
        
        if not otp_code:
            print("   ❌ No OTP code provided")
            return
        
        print(f"\n7. Verifying OTP code: {otp_code}")
        print("   Look for the token logs in the output above...")
        
        try:
            if await client.verify_otp(otp_code):
                print("   ✓ OTP verification successful")
                
                # Check tokens manually
                print("\n8. Checking tokens manually:")
                print(f"   Hash Token: {client._hash}")
                print(f"   Hash Token Length: {len(client._hash) if client._hash else 0}")
                print(f"   Refresh Token: {client._refresh_token}")
                print(f"   Refresh Token Length: {len(client._refresh_token) if client._refresh_token else 0}")
                
                hash_in_session = client._session_data.get("hash") if client._session_data else None
                refresh_in_session = client._session_data.get("refreshToken") if client._session_data else None
                
                print(f"   Hash in session: {hash_in_session}")
                print(f"   Hash in session Length: {len(hash_in_session) if hash_in_session else 0}")
                print(f"   Refresh in session: {refresh_in_session}")
                print(f"   Refresh in session Length: {len(refresh_in_session) if refresh_in_session else 0}")
                
                # Verify tokens are the same
                if client._hash and hash_in_session:
                    print(f"   Hash tokens match: {client._hash == hash_in_session}")
                else:
                    print(f"   Hash tokens match: False (one or both missing)")
                
                if client._refresh_token and refresh_in_session:
                    print(f"   Refresh tokens match: {client._refresh_token == refresh_in_session}")
                else:
                    print(f"   Refresh tokens match: False (one or both missing)")
                
                # Save session to test token saving
                print("\n9. Testing session save...")
                session_file = f"test_session_{user}.json"
                await client.save_session(session_file)
                print(f"   ✓ Session saved to {session_file}")
                
                # Load session to test token loading
                print("\n10. Testing session load...")
                if await client.load_session(session_file):
                    print("   ✓ Session loaded successfully")
                else:
                    print("   ❌ Failed to load session")
                
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
        print("\n11. Cleaning up...")
        await client.disconnect()
        print("   ✓ Disconnected")

if __name__ == "__main__":
    asyncio.run(test_hash_logging()) 