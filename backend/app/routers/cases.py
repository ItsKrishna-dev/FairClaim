from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from app.routers.auth import get_current_user
from app.database import get_db
from app.models import Case, User
from app.schemas import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse
from app.services import FileHandler

router = APIRouter(prefix="/cases", tags=["Cases"])
file_handler = FileHandler()


def get_user_role(user: User) -> str:
    """Extract and normalize user role to lowercase"""
    role = user.role.value if hasattr(user.role, 'value') else user.role
    return str(role).lower()


def generate_case_number() -> str:
    """Generate unique case number"""
    return f"FC-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new case"""
    user_role = get_user_role(current_user)
    
    if user_role not in ["admin", "official", "officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and officers can create cases"
        )
    
    try:
        db_case = Case(
            case_number=generate_case_number(),
            victim_name=case.victim_name,
            victim_aadhaar=case.victim_aadhaar,
            victim_phone=case.victim_phone,
            victim_email=case.victim_email,
            incident_description=case.incident_description,
            incident_date=case.incident_date,
            incident_location=case.incident_location,
            stage=case.stage.value,
            compensation_amount=case.compensation_amount,
            bank_account_number=case.bank_account_number,
            ifsc_code=case.ifsc_code,
            created_by_user_id=current_user.id
        )
        
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return db_case
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create case: {str(e)}"
        )


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
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_update: CaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update case status and fields"""
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


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a case"""
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
