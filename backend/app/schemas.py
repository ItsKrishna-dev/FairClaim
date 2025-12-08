from pydantic import BaseModel, Field, validator, EmailStr, field_validator
from datetime import datetime, date
from typing import Optional, List, Literal
from enum import Enum

# ============= ACT TYPE ENUM =============
class ActType(str, Enum):
    """Types of Acts under which compensation is claimed"""
    PCR_ACT_1955 = "PCR Act 1955"
    POA_ACT_2015 = "PoA Act 2015"


# ============= CASE SCHEMAS =============
class CaseStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAYMENT_PROCESSING = "PAYMENT_PROCESSING"
    COMPLETED = "COMPLETED"


class CaseStage(str, Enum):
    FIR = "FIR"
    CHARGESHEET = "CHARGESHEET"
    CONVICTION = "CONVICTION"


# ✅ VICTIM CASE REGISTRATION
class VictimCaseCreate(BaseModel):
    """Victim case registration - 10 fields"""
    
    victim_name: str = Field(..., min_length=2, max_length=100)
    victim_aadhaar: str = Field(..., pattern=r"^\d{12}$")
    fir_number: str = Field(..., min_length=5, max_length=50)
    act_type: ActType = Field(...)
    incident_description: str = Field(..., min_length=10)
    incident_date: str  # Accept string "YYYY-MM-DD"
    incident_location: str = Field(..., min_length=5)
    bank_name: str = Field(..., min_length=2, max_length=100)
    bank_account_number: str = Field(..., min_length=9, max_length=18)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    
    @validator('incident_date')
    def validate_incident_date(cls, v):
        """Parse and validate incident date"""
        from datetime import datetime as dt
        
        try:
            parsed_date = dt.strptime(v, "%Y-%m-%d").date()
            
            if parsed_date > dt.now().date():
                raise ValueError('Incident date cannot be in the future')
            
            return v
            
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise


# ✅ BASE CASE SCHEMA
class CaseBase(BaseModel):
    victim_name: str = Field(..., min_length=2, max_length=100)
    victim_aadhaar: str = Field(..., pattern=r"^\d{12}$")
    victim_phone: str = Field(..., min_length=10, max_length=15)
    victim_email: Optional[str] = None
    incident_description: str = Field(..., min_length=10)
    incident_date: datetime  # ✅ Keep as datetime for database compatibility
    incident_location: str = Field(..., min_length=5)
    stage: CaseStage
    compensation_amount: float = Field(..., gt=0)
    bank_account_number: str = Field(..., min_length=9, max_length=18)
    ifsc_code: str = Field(..., min_length=11, max_length=11)
    fir_number: Optional[str] = None
    act_type: Optional[str] = None
    bank_name: Optional[str] = None
    
    @validator('incident_date', pre=True)
    def parse_incident_date(cls, v):
        """Handle both datetime and date objects"""
        if isinstance(v, str):
            # Parse string to datetime
            return datetime.strptime(v, "%Y-%m-%d")
        elif isinstance(v, date) and not isinstance(v, datetime):
            # Convert date to datetime
            return datetime.combine(v, datetime.min.time())
        return v


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    status: Optional[CaseStatus] = None
    assigned_officer: Optional[str] = None
    remarks: Optional[str] = None


# ✅ CASE RESPONSE - SERIALIZES PROPERLY
class CaseResponse(CaseBase):
    id: int
    case_number: str
    status: str
    uploaded_documents: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assigned_officer: Optional[str] = None
    remarks: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class CaseListResponse(BaseModel):
    cases: List[CaseResponse]
    total: int
    page: int
    page_size: int


# ============= GRIEVANCE SCHEMAS =============
class GrievanceStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class GrievancePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GrievanceBase(BaseModel):
    case_id: int
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(..., min_length=3, max_length=100)
    contact_name: str = Field(..., min_length=2, max_length=100)
    contact_phone: str = Field(..., min_length=10, max_length=15)
    contact_email: Optional[str] = None
    is_escalated: bool = False


class GrievanceCreate(GrievanceBase):
    pass


class GrievanceUpdate(BaseModel):
    status: Optional[GrievanceStatus] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None


class GrievanceResponse(GrievanceBase):
    id: int
    grievance_number: str
    priority: str
    status: str
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GrievanceListResponse(BaseModel):
    grievances: List[GrievanceResponse]
    total: int
    page: int
    page_size: int


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
    phone: Optional[str] = Field(None, pattern=r'^\\+?[1-9]\\d{9,14}$')
    role: UserRoleEnum


class UserRole(str, Enum):
    ADMIN = "admin"
    OFFICER = "officer"
    VICTIM = "victim"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Password: 6-72 characters"
    )
    full_name: str
    role: Literal["admin", "officer", "victim","Victim","Admin","Officer"]
    phone: Optional[str] = Field(None, pattern=r'^\\+?[1-9]\\d{9,14}$')
    aadhaar_number: Optional[str] = Field(None, pattern=r'^\\d{12}$')
    address: Optional[str] = None
    
    # @field_validator('password')
    # @classmethod
    # def validate_password_length(cls, v):
    #     """Ensure password is within bcrypt limits"""
    #     if len(v) > 100:
    #         raise ValueError('Password cannot be longer than 72 characters')
    #     return v


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
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r'^\\+?[1-9]\\d{9,14}$')
    address: Optional[str] = None


# ==================== TOKEN SCHEMAS ====================
class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: Optional[int] = None
    exp: Optional[int] = None


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
    open: int
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
    phone: str = Field(..., pattern=r'^\\+?[1-9]\\d{9,14}$')
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
