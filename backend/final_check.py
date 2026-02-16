
import requests
import json
import time

print("\n" + "="*60)
print("🚀 EQUIVISION FINAL SYSTEM CHECK")
print("="*60)
print("Waiting 5s for services to stabilize...")
time.sleep(5)

base_url = "http://localhost:8000"

print("\n✅ 1. API Health Check")
try:
    r = requests.get(f"{base_url}/health", timeout=5)
    if r.status_code == 200:
        print("   PASS")
    else:
        print(f"   FAIL: {r.status_code} {r.text}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n✅ 2. Database & Auth")
token = None
try:
    # Register/Login
    username = f"user_{int(time.time())}"
    r = requests.post(f"{base_url}/auth/register", json={
        "email": f"{username}@test.com", "username": username, "password": "password123"
    })
    if r.status_code in [200, 400]:
        print("   Registration: PASS")
        
        # Login
        r = requests.post(f"{base_url}/auth/login", data={
            "username": username, "password": "password123"
        })
        if r.status_code == 200:
            token = r.json()['access_token']
            print("   Login: PASS")
            print(f"   Token: {token[:10]}...")
        else:
            print(f"   Login FAIL: {r.status_code} {r.text}")
    else:
        print(f"   Registration FAIL: {r.status_code} {r.text}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n✅ 3. Pricing Engine (Local ML)")
try:
    r = requests.post(f"{base_url}/predict/price", json={
        "breed": "arabe", "gender": "male", "age": 5
    })
    if r.status_code == 200:
        print(f"   PASS: {r.json()['estimated_price']} DH")
    else:
        print(f"   FAIL: {r.status_code} {r.text}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n✅ 4. Vision Engine (Docker Proxy)")
try:
    # Create dummy image
    from PIL import Image
    import io
    img = Image.new('RGB', (224, 224), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    files = {'file': ('test.jpg', img_byte_arr, 'image/jpeg')}
    r = requests.post(f"{base_url}/predict/breed", files=files)
    
    if r.status_code == 200:
        print(f"   PASS: {r.json()}")
    else:
        print(f"   FAIL: {r.status_code} {r.text}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n" + "="*60)
