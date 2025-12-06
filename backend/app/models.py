from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum , Boolean
import enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

# Case Enums
class CaseStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    COMPLETED = "COMPLETED"

class CaseStage(str, enum.Enum):
    FIR = "FIR"
    CHARGESHEET = "CHARGESHEET"
    CONVICTION = "CONVICTION"

# Grievance Enums
class GrievanceStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"

class GrievancePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# Case Model
class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Victim Details
    victim_name = Column(String(100), nullable=False)
    victim_aadhaar = Column(String(12), nullable=False)
    victim_phone = Column(String(15), nullable=False)
    victim_email = Column(String(100), nullable=True)
    
    # Incident Details 
    incident_description = Column(Text, nullable=False)
    incident_date = Column(DateTime, nullable=False)
    incident_location = Column(String(255), nullable=False)
    
    # DBT Details
    stage = Column(String(20), nullable=False)  # Using String for SQLite compatibility
    status = Column(String(20), default="PENDING", nullable=False)
    compensation_amount = Column(Float, nullable=False)
    bank_account_number = Column(String(20), nullable=False)
    ifsc_code = Column(String(11), nullable=False)
    
    # File Uploads
    uploaded_documents = Column(Text, nullable=True)  # JSON string\
    # 🔗 ADD THESE - Link to User
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_officer_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    assigned_officer = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    
    # Relationships
    grievances = relationship("Grievance", back_populates="case", cascade="all, delete-orphan")
    creator = relationship("User", back_populates="created_cases", foreign_keys=[created_by_user_id])
    assigned_officer_user = relationship("User", back_populates="assigned_cases", foreign_keys=[assigned_officer_user_id])
    def __repr__(self):
        return f"<Case(id={self.id}, fir='{self.fir_number}', status='{self.status.value}')>"

# Grievance Model
class Grievance(Base):
    __tablename__ = "grievances"
    
    id = Column(Integer, primary_key=True, index=True)
    grievance_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign Key
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Grievance Details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    
    # Priority & Status
    priority = Column(String(20), default="MEDIUM", nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)
    
    # Contact
    contact_name = Column(String(100), nullable=False)
    contact_phone = Column(String(15), nullable=False)
    contact_email = Column(String(100), nullable=True)
     
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # Escalation
    is_escalated = Column(Boolean, default=False, nullable=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="grievances")
    creator = relationship("User", back_populates="created_grievances")
    def __repr__(self):
        return f"<Grievance(id={self.id}, priority='{self.priority.value}', status='{self.status.value}')>"

class UserRole(enum.Enum):
    """User role types"""
    VICTIM = "victim"
    OFFICIAL = "official"

class User(Base):
    """
    User model for both victims and officials
    Handles authentication and user information
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # User Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(15), nullable=True)
    full_name = Column(String(255), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    
    # Additional Information
    aadhaar_number = Column(String(12), unique=True, nullable=True)  # For Aadhaar verification
    address = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Email/phone verification status
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships (will be populated by Dev B)
    # cases = relationship("Case", back_populates="user", cascade="all, delete-orphan")
    # Relationships
    created_cases = relationship("Case", back_populates="creator", foreign_keys="Case.created_by_user_id")
    assigned_cases = relationship("Case", back_populates="assigned_officer_user", foreign_keys="Case.assigned_officer_user_id")
    created_grievances = relationship("Grievance", back_populates="creator")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"