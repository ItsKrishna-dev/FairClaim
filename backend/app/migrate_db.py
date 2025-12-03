from sqlalchemy import text
from database import engine

def migrate_database():
    """Add user relationship columns to existing tables"""
    
    with engine.connect() as conn:
        try:
            # Add columns to cases table
            conn.execute(text("""
                ALTER TABLE cases 
                ADD COLUMN created_by_user_id INTEGER;
            """))
            
            conn.execute(text("""
                ALTER TABLE cases 
                ADD COLUMN assigned_officer_user_id INTEGER;
            """))
            
            # Add column to grievances table
            conn.execute(text("""
                ALTER TABLE grievances 
                ADD COLUMN created_by_user_id INTEGER;
            """))
            
            conn.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"⚠️  Migration error (columns may already exist): {e}")

if __name__ == "__main__":
    migrate_database()
