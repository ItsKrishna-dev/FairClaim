"""
SQLAlchemy ORM Models
Defines database table structures for the FairClaim application
"""
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ==================== ENUMS ====================

class UserRole(enum.Enum):
    """User role types"""
    VICTIM = "victim"
    OFFICIAL = "official"


class CaseStatus(enum.Enum):
    """Case processing stages"""
    FIR_STAGE = "fir_stage"
    CHARGESHEET_STAGE = "chargesheet_stage"
    CONVICTION_STAGE = "conviction_stage"


class GrievancePriority(enum.Enum):
    """Grievance priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GrievanceStatus(enum.Enum):
    """Grievance processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ==================== MODELS ====================

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
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"


# ==================== PLACEHOLDER FOR DEV B ====================
# Dev B will add these models:

class Case(Base):
    """
    Case model for tracking victim compensation cases
    DEV B: Add complete implementation
    """
    __tablename__ = "cases"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Case Information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    fir_number = Column(String(50), unique=True, nullable=False, index=True)
    case_type = Column(String(100), nullable=True)  # Type of atrocity
    
    # Status
    status = Column(Enum(CaseStatus), default=CaseStatus.FIR_STAGE, nullable=False, index=True)
    
    # Financial Information
    fund_amount = Column(Float, default=0.0, nullable=False)  # Total sanctioned amount
    fund_disbursed = Column(Float, default=0.0, nullable=False)  # Amount disbursed
    
    # Documents
    document_path = Column(String(500), nullable=True)  # Path to uploaded document
    document_verified = Column(Boolean, default=False)
    verification_confidence = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    # user = relationship("User", back_populates="cases")
    # grievances = relationship("Grievance", back_populates="case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Case(id={self.id}, fir='{self.fir_number}', status='{self.status.value}')>"


class Grievance(Base):
    """
    Grievance model for tracking complaints and issues
    DEV B: Add complete implementation
    """
    __tablename__ = "grievances"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Keys
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Grievance Information
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Priority and Status
    priority = Column(Enum(GrievancePriority), default=GrievancePriority.MEDIUM, nullable=False, index=True)
    status = Column(Enum(GrievanceStatus), default=GrievanceStatus.PENDING, nullable=False, index=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Official who resolved
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    # case = relationship("Case", back_populates="grievances")
    
    def __repr__(self):
        return f"<Grievance(id={self.id}, priority='{self.priority.value}', status='{self.status.value}')>"
