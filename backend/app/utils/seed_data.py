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
    """Seed 3-4 cases PER dummy victim user (victim1, victim2, victim3 only)"""
    print("\n" + "=" * 60)
    print("📦 Seeding Cases for Dummy Users Only")
    print("=" * 60)
    
    stages = ["FIR", "CHARGESHEET", "CONVICTION"]
    statuses = ["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAYMENT_PROCESSING", "COMPLETED"]
    officers = ["Sneha Reddy", "Vikram Singh"]
    
    # ✅ Only dummy victim users get cases
    dummy_victims = [
        {
            "name": "Rajesh Kumar",
            "email": "victim1@fairclaim.com",
            "phone": "+919876543210",
            "aadhaar": "123456789012"
        },
        {
            "name": "Priya Sharma",
            "email": "victim2@fairclaim.com",
            "phone": "+919876543211",
            "aadhaar": "123456789013"
        },
        {
            "name": "Amit Patel",
            "email": "victim3@fairclaim.com",
            "phone": "+919876543212",
            "aadhaar": "123456789014"
        }
    ]
    
    dummy_cases = []
    case_counter = 1
    
    # ✅ Create 3-4 cases per dummy victim
    for victim in dummy_victims:
        num_cases = random.randint(3, 4)  # 3 or 4 cases per victim
        
        for i in range(num_cases):
            case = Case(
                case_number=f"FC-2025120100{case_counter:03d}",
                victim_name=victim["name"],
                victim_aadhaar=victim["aadhaar"],
                victim_phone=victim["phone"],
                victim_email=victim["email"],  # ✅ Linked to specific dummy user
                incident_description=f"Case {case_counter}: Detailed description of atrocity incident involving caste-based discrimination and violence.",
                incident_date=datetime.now() - timedelta(days=random.randint(1, 365)),
                incident_location=f"Village {case_counter}, District {chr(65 + case_counter % 5)}, State",
                stage=random.choice(stages),
                status=random.choice(statuses),
                compensation_amount=random.choice([50000, 100000, 150000, 200000, 250000]),
                bank_account_number=f"123456{case_counter:010d}",
                ifsc_code=f"SBIN000{case_counter:04d}",
                assigned_officer=random.choice(officers),
                remarks=f"Case {case_counter} under review" if case_counter % 3 == 0 else None
            )
            dummy_cases.append(case)
            case_counter += 1
    
    db.add_all(dummy_cases)
    db.commit()
    
    print(f"✅ Seeded {len(dummy_cases)} cases across {len(dummy_victims)} dummy victims")
    print(f"   - Rajesh Kumar (victim1@fairclaim.com): Cases linked")
    print(f"   - Priya Sharma (victim2@fairclaim.com): Cases linked")
    print(f"   - Amit Patel (victim3@fairclaim.com): Cases linked")
    
    return dummy_cases


def seed_grievances(db: Session, cases):
    """Seed grievances linked to dummy cases only"""
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
    
    grievance_status = ["PENDING", "OPEN", "RESOLVED"]
    dummy_grievances = []
    
    for i, case in enumerate(cases):
        if i < len(grievance_templates):
            title, desc, category = grievance_templates[i]
            
            # Determine escalation
            creation_days_ago = random.randint(1, 20)
            created_at = datetime.utcnow() - timedelta(days=creation_days_ago)
            
            is_resolved = (i % 4 == 0)
            resolved_at = datetime.utcnow() - timedelta(days=random.randint(1, 10)) if is_resolved else None
            
            is_escalated = (not is_resolved) and (creation_days_ago > 10)
            
            grievance = Grievance(
                grievance_number=f"GR-2025120200{i+1:02d}",
                case_id=case.id,
                title=title,
                description=desc,
                category=category,
                priority="MEDIUM",
                status=random.choice(grievance_status),
                contact_name=case.victim_name,
                contact_phone=case.victim_phone,
                contact_email=case.victim_email,
                created_at=created_at,
                resolved_at=resolved_at,
                resolved_by=f"Support Officer {chr(65 + i % 3)}" if is_resolved else None,
                is_escalated=is_escalated
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
        # 3. Seed Users
        seed_users(db)
        
        # 4. ✅ Clear ONLY existing dummy Cases/Grievances linked to dummy users
        print("\n🧹 Cleaning old dummy Case and Grievance data...")
        
        # Delete only cases belonging to dummy users
        dummy_emails = ["victim1@fairclaim.com", "victim2@fairclaim.com", "victim3@fairclaim.com"]
        
        # Get dummy case IDs
        dummy_case_ids = db.query(Case.id).filter(Case.victim_email.in_(dummy_emails)).all()
        dummy_case_ids = [c[0] for c in dummy_case_ids]
        
        # Delete grievances linked to dummy cases
        if dummy_case_ids:
            db.query(Grievance).filter(Grievance.case_id.in_(dummy_case_ids)).delete(synchronize_session=False)
        
        # Delete dummy cases
        db.query(Case).filter(Case.victim_email.in_(dummy_emails)).delete(synchronize_session=False)
        db.commit()
        
        print("✅ Cleaned dummy data only (real user data preserved)")
        
        # 5. Seed Cases (only for dummy users)
        cases = seed_cases(db)
        
        # 6. Seed Grievances
        seed_grievances(db, cases)
        
        print("\n" + "=" * 60)
        print("🎉 Database seeding completed successfully!")
        print("=" * 60)
        
        # Print login credentials reminder
        print("\n📝 Test Credentials (Dummy Users with Cases):")
        print("-" * 60)
        print("Victims (with 3-4 dummy cases each):")
        print("  Email: victim1@fairclaim.com | Password: victim123")
        print("  Email: victim2@fairclaim.com | Password: victim123")
        print("  Email: victim3@fairclaim.com | Password: victim123")
        print("\nOfficials:")
        print("  Email: official1@fairclaim.com | Password: official123")
        print("\n⚠️  New users will have ZERO cases until they create their own!")
        print("-" * 60 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {str(e)}\n")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
