# test_firebase.py
from database import Database

print("Testing Firebase connection...")

try:
    # Test creating a user
    user = Database.create_user(
        username="testuser123",
        email="test@test.com",
        hashed_password="hashedpassword123"
    )
    print(f"✅ Created test user: {user}")
    
    # Test getting user
    fetched_user = Database.get_user_by_username("testuser123")
    print(f"✅ Fetched test user: {fetched_user}")
    
except Exception as e:
    print(f"❌ Error: {e}")