from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime, date

from app.routers.auth import get_current_user
from app.database import get_db
from app.models import Case, User
from app.schemas import (
    CaseCreate, 
    CaseUpdate, 
    CaseResponse, 
    CaseListResponse, 
    VictimCaseCreate  # ✅ New schema for victim registration
)
from app.services import FileHandler, calculate_compensation

router = APIRouter(prefix="/cases", tags=["Cases"])
file_handler = FileHandler()


# ============= HELPER FUNCTIONS =============

def get_user_role(user: User) -> str:
    """Extract and normalize user role to lowercase"""
    role = user.role.value if hasattr(user.role, 'value') else user.role
    return str(role).lower()


def generate_case_number() -> str:
    """Generate unique case number"""
    return f"FC-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"


# ============= CASE REGISTRATION ENDPOINTS =============

@router.post("/victim/register", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def register_victim_case(
    case_data: VictimCaseCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Register a new case (VICTIMS ONLY).
    Compensation is AUTO-CALCULATED based on Act Type.
    """
    
    user_role = get_user_role(current_user)
    
    if user_role != "victim":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only victims can register new cases"
        )
    
    try:
        from datetime import datetime, date
        
        # ✅ AUTO-CALCULATE COMPENSATION
        compensation = calculate_compensation(
            act_type=case_data.act_type.value,
            stage="FIR"
        )
        
        # ✅ PARSE DATE PROPERLY
        incident_date = case_data.incident_date
        
        if isinstance(incident_date, str):
            # Parse string "2025-12-08" to date object
            incident_date_obj = datetime.strptime(incident_date, "%Y-%m-%d").date()
        elif isinstance(incident_date, date):
            # Already a date object
            incident_date_obj = incident_date
        else:
            # Fallback
            incident_date_obj = datetime.now().date()
        
        # Convert date to datetime for database
        incident_datetime = datetime.combine(incident_date_obj, datetime.min.time())
        
        # Get phone and email from logged-in user
        victim_phone = current_user.phone or "0000000000"
        victim_email = current_user.email
        
        # Create case
        db_case = Case(
            case_number=generate_case_number(),
            victim_name=case_data.victim_name,
            victim_aadhaar=case_data.victim_aadhaar,
            victim_phone=victim_phone,
            victim_email=victim_email,
            fir_number=case_data.fir_number,
            act_type=case_data.act_type.value,
            bank_name=case_data.bank_name,
            incident_description=case_data.incident_description,
            incident_date=incident_datetime,
            incident_location=case_data.incident_location,
            stage="FIR",
            status="PENDING",
            compensation_amount=compensation,
            bank_account_number=case_data.bank_account_number,
            ifsc_code=case_data.ifsc_code,
            created_by_user_id=current_user.id
        )
        
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        
        print(f"✅ Case {db_case.case_number} created with auto-compensation: ₹{compensation:,.2f}")
        
        return db_case
        
    except ValueError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        print(f"❌ Error registering case: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register case: {str(e)}"
        )

# ============= CASE LISTING & RETRIEVAL =============

@router.get("/", response_model=CaseListResponse)
def list_cases(
    page: int = 1,
    page_size: int = 10,
    status_filter: Optional[str] = None,
    stage_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all cases with pagination and filters"""
    query = db.query(Case)
    user_role = get_user_role(current_user)
    
    if user_role == "victim":
        # ✅ Victims can only see their own cases
        query = query.filter(
            (Case.victim_phone == current_user.phone) |
            (Case.victim_email == current_user.email)
        )
    
    elif user_role in ["official", "officer"]:
        # Officers see cases assigned to them
        query = query.filter(
            (Case.assigned_officer == current_user.full_name) |
            (Case.created_by_user_id == current_user.id)
        )
    
    # Apply filters
    if status_filter:
        query = query.filter(Case.status == status_filter)
    if stage_filter:
        query = query.filter(Case.stage == stage_filter)
    
    total = query.count()
    skip = (page - 1) * page_size
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(page_size).all()
    
    return {
        "cases": cases,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Get a single case by ID"""
    case = db.query(Case).filter(Case.id == case_id).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )
    
    user_role = get_user_role(current_user)
    
    # 🔒 Access control
    if user_role == "victim":
        if case.victim_phone != current_user.phone and case.victim_email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own cases"
            )
    
    elif user_role in ["official", "officer"]:
        if case.assigned_officer != current_user.full_name and case.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view cases assigned to you"
            )
    
    return case


# ============= CASE UPDATES =============

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int, 
    case_update: CaseUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Update case status and fields (officials only)"""
    user_role = get_user_role(current_user)
    
    if user_role not in ["admin", "official", "officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and officers can update cases"
        )
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )
    
    update_data = case_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(case, field, value.value)
        else:
            setattr(case, field, value)
    
    try:
        db.commit()
        db.refresh(case)
        return case
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update case: {str(e)}"
        )


# ============= DOCUMENT UPLOAD =============

@router.post("/{case_id}/upload", response_model=CaseResponse)
async def upload_case_documents(
    case_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload documents for a case"""
    case = db.query(Case).filter(Case.id == case_id).first()
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )
    
    user_role = get_user_role(current_user)
    
    if user_role == "victim":
        if (case.victim_phone != current_user.phone and
            case.victim_email != current_user.email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload documents to your own cases"
            )
    
    elif user_role in ["official", "officer"]:
        if (case.created_by_user_id != current_user.id and
            case.assigned_officer != current_user.full_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload documents to cases you created or are assigned to"
            )
    
    try:
        file_paths = file_handler.save_multiple_files(files, subfolder=f"cases/{case_id}")
        existing_files = json.loads(case.uploaded_documents) if case.uploaded_documents else []
        existing_files.extend(file_paths)
        case.uploaded_documents = json.dumps(existing_files)
        
        db.commit()
        db.refresh(case)
        return case
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )


# ============= CASE DELETION =============

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a case (admins only)"""
    user_role = get_user_role(current_user)
    
    if user_role not in ["admin", "official", "officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and officers can delete cases"
        )
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found"
        )
    
    try:
        db.delete(case)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete case: {str(e)}"
        )
