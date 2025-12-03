import requests

BASE_URL = "http://localhost:8000/api"

print("\n🔐 Testing /me Endpoint\n")
print("="*70)

# Step 1: Login
print("\n1️⃣  Logging in...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "officer1@fairclaim.com",
        "password": "password123"
    }
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()['access_token']
print(f"✅ Login successful!")
print(f"   Token: {token[:50]}...")

# Step 2: Test /me endpoint
print("\n2️⃣  Testing /api/auth/me endpoint...")

headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

print(f"   Status: {response.status_code}")

if response.status_code == 200:
    user = response.json()
    print(f"   ✅ SUCCESS!")
    print(f"   User ID: {user['id']}")
    print(f"   Email: {user['email']}")
    print(f"   Name: {user['full_name']}")
    print(f"   Role: {user['role']}")
    print(f"   Active: {user['is_active']}")
elif response.status_code == 401:
    print(f"   ❌ UNAUTHORIZED")
    print(f"   Response: {response.text}")
    print("\n   🔍 This means:")
    print("      • Token verification is failing")
    print("      • Check if there's a duplicate @router in services.py")
    print("      • Make sure services.py only has functions, no routes")
else:
    print(f"   Response: {response.text}")

print("\n" + "="*70 + "\n")
