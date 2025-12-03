
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from app.models import Case, Grievance
from app.database import SessionLocal, engine, Base

def seed_cases(db: Session):
    """Seed 10 dummy cases"""
    print("📦 Seeding cases...")
    
    stages = ["FIR", "CHARGESHEET", "CONVICTION"]
    statuses = ["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAYMENT_PROCESSING", "COMPLETED"]
    
    dummy_cases = []
    for i in range(1, 11):
        case = Case(
            case_number=f"FC-2025120100{i:02d}",
            victim_name=f"Victim Name {i}",
            victim_aadhaar=f"12345678{i:04d}",
            victim_phone=f"+9198765432{i:02d}",
            victim_email=f"victim{i}@example.com",
            incident_description=f"Case {i}: Detailed description of atrocity incident involving caste-based discrimination and violence.",
            incident_date=datetime.now() - timedelta(days=random.randint(1, 365)),
            incident_location=f"Village {i}, District {chr(65 + i % 5)}, State",
            stage=random.choice(stages),
            status=random.choice(statuses),
            compensation_amount=random.choice([50000, 100000, 150000, 200000, 250000]),
            bank_account_number=f"123456{i:010d}",
            ifsc_code=f"SBIN000{i:04d}",
            assigned_officer=f"Officer {chr(65 + i % 5)}" if i % 2 == 0 else None,
            remarks=f"Case {i} under review" if i % 3 == 0 else None
        )
        dummy_cases.append(case)
    
    db.add_all(dummy_cases)
    db.commit()
    print(f"✅ Seeded {len(dummy_cases)} cases")
    return dummy_cases

def seed_grievances(db: Session, cases):
    """Seed grievances linked to cases"""
    print("📦 Seeding grievances...")
    
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
                status="OPEN" if i % 2 == 0 else "IN_PROGRESS",
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
    """Seed all data"""
    print("\n🌱 Starting database seeding...\n")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Clear existing data (optional)
        db.query(Grievance).delete()
        db.query(Case).delete()
        db.commit()
        
        # Seed data
        cases = seed_cases(db)
        seed_grievances(db, cases)
        
        print("\n✅ Database seeding completed successfully!\n")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding database: {str(e)}\n")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
