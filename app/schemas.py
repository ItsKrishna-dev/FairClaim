"""
Pydantic Schemas for Request/Response validation
Defines data validation and serialization for API endpoints
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS FOR SCHEMAS ====================

class UserRoleEnum(str, Enum):
    """User role types for API"""
    VICTIM = "victim"
    OFFICIAL = "official"


class CaseStatusEnum(str, Enum):
    """Case status types for API"""
    FIR_STAGE = "fir_stage"
    CHARGESHEET_STAGE = "chargesheet_stage"
    CONVICTION_STAGE = "conviction_stage"


class GrievancePriorityEnum(str, Enum):
    """Grievance priority for API"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GrievanceStatusEnum(str, Enum):
    """Grievance status for API"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{9,14}$')
    role: UserRoleEnum


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{9,14}$')
    role: UserRoleEnum
    aadhaar_number: Optional[str] = Field(None, pattern=r'^\d{12}$')
    address: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    aadhaar_number: Optional[str]
    address: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy ORM compatibility


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{9,14}$')
    address: Optional[str] = None


# ==================== TOKEN SCHEMAS ====================

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: Optional[int] = None  # User ID
    exp: Optional[int] = None  # Expiration time


# ==================== CASE SCHEMAS (DEV B) ====================

class CaseBase(BaseModel):
    """Base case schema"""
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    fir_number: str = Field(..., min_length=3, max_length=50)
    case_type: Optional[str] = None


class CaseCreate(CaseBase):
    """Schema for creating a new case"""
    fund_amount: float = Field(default=0.0, ge=0)


class CaseUpdate(BaseModel):
    """Schema for updating case"""
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = None
    status: Optional[CaseStatusEnum] = None
    fund_amount: Optional[float] = Field(None, ge=0)
    fund_disbursed: Optional[float] = Field(None, ge=0)


class CaseResponse(CaseBase):
    """Schema for case response"""
    id: int
    user_id: int
    status: str
    fund_amount: float
    fund_disbursed: float
    document_path: Optional[str]
    document_verified: bool
    verification_confidence: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Schema for list of cases"""
    total: int
    cases: List[CaseResponse]


# ==================== GRIEVANCE SCHEMAS (DEV B) ====================

class GrievanceBase(BaseModel):
    """Base grievance schema"""
    subject: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)


class GrievanceCreate(GrievanceBase):
    """Schema for creating grievance"""
    case_id: int = Field(..., gt=0)


class GrievanceUpdate(BaseModel):
    """Schema for updating grievance"""
    status: Optional[GrievanceStatusEnum] = None
    resolution_notes: Optional[str] = None


class GrievanceResponse(GrievanceBase):
    """Schema for grievance response"""
    id: int
    case_id: int
    user_id: int
    priority: str
    status: str
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class GrievanceListResponse(BaseModel):
    """Schema for list of grievances"""
    total: int
    grievances: List[GrievanceResponse]


# ==================== DOCUMENT VERIFICATION SCHEMAS ====================

class DocumentVerificationResponse(BaseModel):
    """Schema for document verification result"""
    filename: str
    document_type: str
    verified: bool
    confidence: float
    extracted_text_preview: Optional[str]
    keywords_matched: int
    total_keywords: int
    uploaded_by: str
    timestamp: datetime


# ==================== DASHBOARD SCHEMAS ====================

class FundStatistics(BaseModel):
    """Schema for fund statistics"""
    total_allocated: float
    total_disbursed: float
    pending: float


class GrievanceStatistics(BaseModel):
    """Schema for grievance statistics"""
    total: int
    pending: int
    in_progress: int
    resolved: int
    high_priority: int


class DashboardStats(BaseModel):
    """Schema for dashboard statistics"""
    total_cases: int
    status_breakdown: dict
    fund_statistics: FundStatistics
    grievances: GrievanceStatistics
    user_role: str


# ==================== NOTIFICATION SCHEMAS ====================

class SMSNotification(BaseModel):
    """Schema for SMS notification"""
    phone: str = Field(..., pattern=r'^\+?[1-9]\d{9,14}$')
    message: str = Field(..., min_length=1, max_length=160)


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    success: bool
    message_sid: Optional[str]
    status: Optional[str]
    error: Optional[str]


# ==================== ERROR SCHEMAS ====================

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
