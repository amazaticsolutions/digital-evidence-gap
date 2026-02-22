#!/usr/bin/env python3
"""
Test script for Sign Up and Sign In APIs.

This script:
1. Creates a new user using the Sign Up API
2. Authenticates the user using the Sign In API
3. Displays the tokens and user information
"""

import requests
import json
from datetime import datetime
import random
import string

# Configuration
BASE_URL = "http://localhost:8000"
SIGNUP_URL = f"{BASE_URL}/api/users/signup/"
SIGNIN_URL = f"{BASE_URL}/api/users/signin/"

# Generate unique email for testing
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
test_email = f"testuser_{timestamp}_{random_suffix}@example.com"
test_password = "TestPassword123!"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_response(response):
    """Print formatted response details."""
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_signup():
    """Test the Sign Up API."""
    print_section("TEST 1: Sign Up API")
    
    # Prepare sign up data
    signup_data = {
        "email": test_email,
        "password": test_password,
        "password_confirm": test_password,
        "phone_number": "+1234567890",
        "organization": "Test Organization"
    }
    
    print(f"\nRequest URL: {SIGNUP_URL}")
    print(f"Request Method: POST")
    print(f"Request Body:")
    print(json.dumps({
        **signup_data,
        "password": "***HIDDEN***",
        "password_confirm": "***HIDDEN***"
    }, indent=2))
    
    try:
        response = requests.post(SIGNUP_URL, json=signup_data)
        print_response(response)
        
        if response.status_code == 201:
            print("\n✅ Sign Up successful!")
            data = response.json()
            return data.get('access'), data.get('refresh'), data.get('user')
        else:
            print("\n❌ Sign Up failed!")
            return None, None, None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server. Is Django running on port 8000?")
        return None, None, None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None, None, None

def test_signin():
    """Test the Sign In API."""
    print_section("TEST 2: Sign In API")
    
    # Prepare sign in data
    signin_data = {
        "email": test_email,
        "password": test_password
    }
    
    print(f"\nRequest URL: {SIGNIN_URL}")
    print(f"Request Method: POST")
    print(f"Request Body:")
    print(json.dumps({
        **signin_data,
        "password": "***HIDDEN***"
    }, indent=2))
    
    try:
        response = requests.post(SIGNIN_URL, json=signin_data)
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Sign In successful!")
            data = response.json()
            return data.get('access'), data.get('refresh'), data.get('user')
        else:
            print("\n❌ Sign In failed!")
            return None, None, None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server. Is Django running on port 8000?")
        return None, None, None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None, None, None

def main():
    """Run all authentication tests."""
    print("\n" + "=" * 70)
    print("  AUTHENTICATION API TEST SUITE")
    print("  Testing Sign Up and Sign In endpoints")
    print("=" * 70)
    print(f"\nTest User Email: {test_email}")
    print(f"Test User Password: {test_password}")
    
    # Test 1: Sign Up
    access_token_1, refresh_token_1, user_data_1 = test_signup()
    
    if access_token_1:
        print("\n📝 Sign Up Response Summary:")
        print(f"   Access Token: {access_token_1[:50]}..." if len(access_token_1) > 50 else f"   Access Token: {access_token_1}")
        print(f"   Refresh Token: {refresh_token_1[:50]}..." if len(refresh_token_1) > 50 else f"   Refresh Token: {refresh_token_1}")
        print(f"   User ID: {user_data_1.get('id')}")
        print(f"   User Email: {user_data_1.get('email')}")
    
    # Test 2: Sign In
    access_token_2, refresh_token_2, user_data_2 = test_signin()
    
    if access_token_2:
        print("\n📝 Sign In Response Summary:")
        print(f"   Access Token: {access_token_2[:50]}..." if len(access_token_2) > 50 else f"   Access Token: {access_token_2}")
        print(f"   Refresh Token: {refresh_token_2[:50]}..." if len(refresh_token_2) > 50 else f"   Refresh Token: {refresh_token_2}")
        print(f"   User ID: {user_data_2.get('id')}")
        print(f"   User Email: {user_data_2.get('email')}")
    
    # Final summary
    print_section("TEST SUMMARY")
    
    signup_status = "✅ PASSED" if access_token_1 else "❌ FAILED"
    signin_status = "✅ PASSED" if access_token_2 else "❌ FAILED"
    
    print(f"\n1. Sign Up API: {signup_status}")
    print(f"2. Sign In API: {signin_status}")
    
    if access_token_1 and access_token_2:
        print("\n🎉 All tests passed successfully!")
        print("\n💡 Tips:")
        print("   - Save the access token to use for authenticated requests")
        print("   - Include it in headers as: Authorization: Bearer <access_token>")
        print("   - Use the refresh token to get a new access token when it expires")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
