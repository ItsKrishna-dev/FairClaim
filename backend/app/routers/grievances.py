from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.routers.auth import get_current_user
from app.database import get_db
from app.models import Grievance, Case , User
from app.schemas import GrievanceCreate, GrievanceUpdate, GrievanceResponse, GrievanceListResponse
from app.services.priority_classifier import get_nlp_classifier

router = APIRouter(prefix="/grievances", tags=["Grievances"])


def generate_grievance_number() -> str:
    """Generate unique grievance number"""
    return f"GR-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"

@router.post("/", response_model=GrievanceResponse, status_code=status.HTTP_201_CREATED)
def create_grievance(grievance: GrievanceCreate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """Create a new grievance with NLP-based auto-priority classification"""
    # Verify case exists
    case = db.query(Case).filter(Case.id == grievance.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {grievance.case_id} not found"
        )
    # 🔒 Access control: Verify user has access to this case
    if current_user.role == "VICTIM":
        # Victims can only create grievances for their own cases
        if (case.victim_phone != current_user.phone and 
            case.victim_email != current_user.email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create grievances for your own cases"
            )
    elif current_user.role == "OFFICER":
        # Officers can create grievances for cases they're involved with
        if (case.created_by_user_id != current_user.id and 
            case.assigned_officer_user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create grievances for cases you created or are assigned to"
            )
    
    try:
        # 🤖 NLP-based priority classification
        classifier = get_nlp_classifier()
        classification = classifier.classify_with_confidence(
            title=grievance.title,
            description=grievance.description,
            category=grievance.category
        )
        
        priority = classification['priority']
        
        db_grievance = Grievance(
            grievance_number=generate_grievance_number(),
            case_id=grievance.case_id,
            title=grievance.title,
            description=grievance.description,
            category=grievance.category,
            priority=priority,
            contact_name=grievance.contact_name,
            contact_phone=grievance.contact_phone,
            contact_email=grievance.contact_email,
            created_by_user_id=current_user.id
        )
        
        db.add(db_grievance)
        db.commit()
        db.refresh(db_grievance)
        
        # Add classification metadata to response
        response = GrievanceResponse.from_orm(db_grievance)
        
        # You can add confidence info if needed
        print(f"🎯 Classified as {priority} with {classification['confidence']} confidence")
        print(f"📊 Scores: {classification['scores']}")
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create grievance: {str(e)}"
        )
@router.post("/classify-preview")
def preview_classification(
    title: str,
    description: str,
    category: str = ""
):
    """
    Preview priority classification without creating grievance
    Useful for frontend to show predicted priority
    """
    classifier = get_nlp_classifier()
    result = classifier.classify_with_confidence(title, description, category)
    
    return {
        "priority": result['priority'],
        "confidence": result['confidence'],
        "confidence_percent": f"{result['confidence'] * 100:.1f}%",
        "all_scores": result['scores'],
        "explanation": result['explanation']
    }

@router.get("/", response_model=GrievanceListResponse)
def list_grievances(
    page: int = 1,
    page_size: int = 10,
    case_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """List all grievances with filters"""
    query = db.query(Grievance)
    if current_user.role == "VICTIM":
        # Get case IDs that belong to this victim
        victim_cases = db.query(Case.id).filter(
            (Case.victim_phone == current_user.phone) | 
            (Case.victim_email == current_user.email)
        ).all()
        victim_case_ids = [c[0] for c in victim_cases]
        
        # Filter grievances to only those cases
        query = query.filter(Grievance.case_id.in_(victim_case_ids))
    
    elif current_user.role == "OFFICER":
        # Get case IDs for cases officer is assigned to or created
        officer_cases = db.query(Case.id).filter(
            (Case.assigned_officer == current_user.full_name) |
            (Case.created_by_user_id == current_user.id)
        ).all()
        officer_case_ids = [c[0] for c in officer_cases]
        
        # Filter grievances
        query = query.filter(Grievance.case_id.in_(officer_case_ids))
    
    if case_id:
        query = query.filter(Grievance.case_id == case_id)
    if status_filter:
        query = query.filter(Grievance.status == status_filter)
    if priority_filter:
        query = query.filter(Grievance.priority == priority_filter)
    
    total = query.count()
    skip = (page - 1) * page_size
    grievances = query.order_by(Grievance.created_at.desc()).offset(skip).limit(page_size).all()
    
    return {
        "grievances": grievances,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{grievance_id}", response_model=GrievanceResponse)
def get_grievance(grievance_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """Get a single grievance by ID"""
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance with ID {grievance_id} not found"
        )
    case = db.query(Case).filter(Case.id == grievance.case_id).first()
    if current_user.role == "VICTIM":
        if (case.victim_phone != current_user.phone and 
            case.victim_email != current_user.email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view grievances for your own cases"
            )
    elif current_user.role == "OFFICER":
        if (case.created_by_user_id != current_user.id and 
            case.assigned_officer_user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view grievances for cases you're involved with"
            )
    # ADMIN has full access
    return grievance

@router.patch("/{grievance_id}", response_model=GrievanceResponse)
def update_grievance(
    grievance_id: int,
    grievance_update: GrievanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """Update grievance status"""
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance with ID {grievance_id} not found"
        )
    if current_user.role not in ["ADMIN", "OFFICER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and officers can update grievances"
        )
    
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance with ID {grievance_id} not found"
        )
    
    # Officers can only update grievances for their cases
    if current_user.role == "OFFICER":
        case = db.query(Case).filter(Case.id == grievance.case_id).first()
        if (case.created_by_user_id != current_user.id and 
            case.assigned_officer_user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update grievances for cases you're involved with"
            )
    update_data = grievance_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value:
            setattr(grievance, field, value.value)
            # Auto-set resolved_at if status is RESOLVED or CLOSED
            if value.value in ["RESOLVED", "CLOSED"] and not grievance.resolved_at:
                grievance.resolved_at = datetime.utcnow()
        else:
            setattr(grievance, field, value)
    
    try:
        db.commit()
        db.refresh(grievance)
        return grievance
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update grievance: {str(e)}"
        )

@router.delete("/{grievance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grievance(grievance_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """Delete a grievance"""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete grievances"
        )
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grievance with ID {grievance_id} not found"
        )
    
    try:
        db.delete(grievance)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete grievance: {str(e)}"
        )
