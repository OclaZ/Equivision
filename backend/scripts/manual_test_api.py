import requests
import json

print("=" * 60)
print("EquiVision API Testing")
print("=" * 60)

base_url = "http://localhost:8000"

# Test 1: Health Check
print("\n1. Testing Health Check...")
try:
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 2: Welcome Message
print("\n2. Testing Welcome Message...")
try:
    response = requests.get(f"{base_url}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 3: Price Prediction - Arabian Horse
print("\n3. Testing Price Prediction (Arabian Horse)...")
try:
    data = {
        "breed": "arabe",
        "gender": "male",
        "age": 5
    }
    response = requests.post(f"{base_url}/predict/price", json=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Estimated Price: {result['estimated_price']} {result['currency']}")
    print(f"   Confidence Range: {result['confidence_interval']['min']} - {result['confidence_interval']['max']}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 4: Price Prediction - Friesian Horse
print("\n4. Testing Price Prediction (Friesian Horse)...")
try:
    data = {
        "breed": "frison",
        "gender": "female",
        "age": 3
    }
    response = requests.post(f"{base_url}/predict/price", json=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Estimated Price: {result['estimated_price']} {result['currency']}")
    print(f"   Confidence Range: {result['confidence_interval']['min']} - {result['confidence_interval']['max']}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 5: Price Prediction - Pony
print("\n5. Testing Price Prediction (Pony)...")
try:
    data = {
        "breed": "poney",
        "gender": "male",
        "age": 2
    }
    response = requests.post(f"{base_url}/predict/price", json=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Estimated Price: {result['estimated_price']} {result['currency']}")
    print(f"   Confidence Range: {result['confidence_interval']['min']} - {result['confidence_interval']['max']}")
    print("   ✅ PASS")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 6: User Registration
print("\n6. Testing User Registration...")
try:
    data = {
        "email": "test@equivision.com",
        "username": "testuser123",
        "password": "securepass123"
    }
    response = requests.post(f"{base_url}/auth/register", json=data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   User Created: {result['username']} ({result['email']})")
        print("   ✅ PASS")
    elif response.status_code == 400:
        print(f"   User already exists (expected if running multiple times)")
        print("   ✅ PASS (user exists)")
    else:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

# Test 7: User Login
print("\n7. Testing User Login...")
try:
    data = {
        "username": "testuser123",
        "password": "securepass123"
    }
    response = requests.post(
        f"{base_url}/auth/login",
        data=data  # OAuth2 uses form data
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        token = result['access_token']
        print(f"   Token Type: {result['token_type']}")
        print(f"   Access Token: {token[:20]}...")
        print("   ✅ PASS")
        
        # Test 8: Get Current User
        print("\n8. Testing Get Current User (with token)...")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/auth/me", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            user = response.json()
            print(f"   Logged in as: {user['username']} ({user['email']})")
            print("   ✅ PASS")
        else:
            print(f"   ❌ FAIL: {response.json()}")
    else:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ FAIL: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
