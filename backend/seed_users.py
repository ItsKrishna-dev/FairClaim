"""
Database Seeding Script
Creates dummy users for testing
"""
from app.database import SessionLocal
from app.services import services
from app.models import User

def seed_users():
    """Create dummy users in database"""
    db = SessionLocal()
    
    print("\n" + "=" * 60)
    print("🌱 Seeding Database with Dummy Users")
    print("=" * 60 + "\n")
    
    users_data = [
        {
            "email": "victim1@fairclaim.com",
            "password": "victim123",
            "full_name": "Rajesh Kumar",
            "role": "victim",
            "phone": "+919876543210",
            "aadhaar_number": "123456789012",
            "address": "Village Rampur, District Katihar, Bihar - 854105"
        },
        {
            "email": "victim2@fairclaim.com",
            "password": "victim123",
            "full_name": "Priya Sharma",
            "role": "victim",
            "phone": "+919876543211",
            "aadhaar_number": "123456789013",
            "address": "Village Bhagalpur, District Munger, Bihar - 811201"
        },
        {
            "email": "victim3@fairclaim.com",
            "password": "victim123",
            "full_name": "Amit Patel",
            "role": "victim",
            "phone": "+919876543212",
            "aadhaar_number": "123456789014",
            "address": "Village Sultanpur, District Kushinagar, UP - 274401"
        },
        {
            "email": "official1@fairclaim.com",
            "password": "official123",
            "full_name": "Sneha Reddy",
            "role": "official",
            "phone": "+919876543213",
            "address": "District Collectorate, Patna, Bihar - 800001"
        },
        {
            "email": "official2@fairclaim.com",
            "password": "official123",
            "full_name": "Vikram Singh",
            "role": "official",
            "phone": "+919876543214",
            "address": "District Magistrate Office, Lucknow, UP - 226001"
        },
    ]
    
    success_count = 0
    error_count = 0
    
    for user_data in users_data:
        try:
            # Check if user already exists
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"⏭️  Skipped: {user_data['email']} (already exists)")
                continue
            
            # Create user
            services.create_user(db, **user_data)
            print(f"✅ Created: {user_data['email']} ({user_data['role']})")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error creating {user_data['email']}: {str(e)}")
            error_count += 1
    
    db.close()
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully created: {success_count} users")
    print(f"❌ Errors: {error_count}")
    print("=" * 60)
    
    # Print login credentials
    print("\n📝 Test Credentials:")
    print("-" * 60)
    print("Victims:")
    print("  Email: victim1@fairclaim.com | Password: victim123")
    print("  Email: victim2@fairclaim.com | Password: victim123")
    print("  Email: victim3@fairclaim.com | Password: victim123")
    print("\nOfficials:")
    print("  Email: official1@fairclaim.com | Password: official123")
    print("  Email: official2@fairclaim.com | Password: official123")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    seed_users()
