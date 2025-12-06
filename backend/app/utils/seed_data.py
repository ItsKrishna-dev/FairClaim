"""
Combined Database Seeding Script
Seeds Users, Cases, and Grievances together.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

# App imports
from app.database import SessionLocal, engine, Base
from app.models import Case, Grievance, User
from app.services import services

def seed_users(db: Session):
    """Create dummy users in database if they don't exist"""
    print("\n" + "=" * 60)
    print("👤 Seeding Users")
    print("=" * 60)
    
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

    print(f"✅ Users processing complete. Added: {success_count}")


def seed_cases(db: Session):
    """Seed 10 dummy cases with random officer assignment"""
    print("\n" + "=" * 60)
    print("📦 Seeding Cases")
    print("=" * 60)
    
    stages = ["FIR", "CHARGESHEET", "CONVICTION"]
    statuses = ["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAYMENT_PROCESSING", "COMPLETED"]
    officers = ["Sneha Reddy", "Vikram Singh"]
    
    dummy_cases = []
    for i in range(1, 11):
        case = Case(
            case_number=f"FC-2025120100{i:02d}",
            victim_name=f"Victim Name {i}",
            victim_aadhaar=f"12345678{i:04d}",
            victim_phone=f"+9198765432{i:02d}",
            victim_email=f"victim{i}@fairclaim.com",
            incident_description=f"Case {i}: Detailed description of atrocity incident involving caste-based discrimination and violence.",
            incident_date=datetime.now() - timedelta(days=random.randint(1, 365)),
            incident_location=f"Village {i}, District {chr(65 + i % 5)}, State",
            stage=random.choice(stages),
            status=random.choice(statuses),
            compensation_amount=random.choice([50000, 100000, 150000, 200000, 250000]),
            bank_account_number=f"123456{i:010d}",
            ifsc_code=f"SBIN000{i:04d}",
            assigned_officer=random.choice(officers),
            remarks=f"Case {i} under review" if i % 3 == 0 else None
        )
        dummy_cases.append(case)
    
    db.add_all(dummy_cases)
    db.commit()
    print(f"✅ Seeded {len(dummy_cases)} cases")
    return dummy_cases


def seed_grievances(db: Session, cases):
    """Seed grievances linked to cases"""
    print("\n" + "=" * 60)
    print("📝 Seeding Grievances")
    print("=" * 60)
    
    grievance_templates = [
        ("Payment not received", "Compensation not credited to bank account after 60 days. Need urgent assistance.", "payment delay"),
        ("URGENT: Medical emergency", "Victim requires immediate medical treatment for severe injuries", "medical emergency"),
        ("Document verification pending", "Submitted caste certificate not verified for 3 weeks", "verification issue"),
        ("Officer not responding", "Assigned officer not replying to calls or emails for 2 weeks", "communication issue"),
        ("Incorrect compensation amount", "Received Rs 50,000 instead of sanctioned Rs 100,000", "payment issue"),
        ("Case status not updated", "Case stuck in PENDING status for 45 days without any update", "status delay"),
        ("Bank details rejected", "Bank account verification failed without proper reason", "verification issue"),
        ("CRITICAL: Threat to life", "Receiving death threats from accused party members", "life threat"),
        ("Delayed chargesheet", "Chargesheet not filed even after 90 days of FIR", "legal delay"),
        ("No response from court", "Court hearing dates not communicated properly", "communication issue"),
    ]
    grievance_status=["PENDING","OPEN","RESOLVED"]
    dummy_grievances = []
    for i, case in enumerate(cases):
        if i < len(grievance_templates):
            title, desc, category = grievance_templates[i]
            grievance = Grievance(
                grievance_number=f"GR-2025120200{i+1:02d}",
                case_id=case.id,
                title=title,
                description=desc,
                category=category,
                priority="MEDIUM",  # Will be auto-classified in real API
                status=random.choice(grievance_status),
                contact_name=case.victim_name,
                contact_phone=case.victim_phone,
                contact_email=case.victim_email,
                resolved_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)) if i % 4 == 0 else None,
                resolved_by=f"Support Officer {chr(65 + i % 3)}" if i % 4 == 0 else None
            )
            dummy_grievances.append(grievance)
    
    db.add_all(dummy_grievances)
    db.commit()
    print(f"✅ Seeded {len(dummy_grievances)} grievances")


def seed_all():
    """Orchestrate the seeding of all data"""
    print("\n🌱 Starting FULL database seeding...\n")
    
    # 1. Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # 2. Get database session
    db = SessionLocal()
    
    try:
        # 3. Seed Users (We do this first, and we don't delete existing users to preserve logins)
        seed_users(db)

        # 4. Clear existing Cases/Grievances to prevent duplicates on re-runs
        print("\n🧹 Cleaning old Case and Grievance data...")
        db.query(Grievance).delete()
        db.query(Case).delete()
        db.commit()
        
        # 5. Seed Cases
        cases = seed_cases(db)
        
        # 6. Seed Grievances (linked to the cases we just created)
        seed_grievances(db, cases)
        
        print("\n" + "=" * 60)
        print("🎉 Database seeding completed successfully!")
        print("=" * 60)

        # Print login credentials reminder
        print("\n📝 Test Credentials:")
        print("-" * 60)
        print("Victims:")
        print("  Email: victim1@fairclaim.com | Password: victim123")
        print("  Email: victim2@fairclaim.com | Password: victim123")
        print("\nOfficials:")
        print("  Email: official1@fairclaim.com | Password: official123")
        print("-" * 60 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {str(e)}\n")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
