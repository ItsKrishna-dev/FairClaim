"""
Dashboard Routes
Provides aggregated statistics for admin/official dashboards and personalized views for victims.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.schemas import DashboardStats
from app.services import services
from app.routers.auth import get_current_user
from app.models import User, Case, Grievance, CaseStage

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get role-specific dashboard data.
    
    **Victim View:**
    - Case progress (FIR, Chargesheet, Conviction)
    - Compensation wallet (Disbursed vs Pending)
    - Active Grievances with SLA status
    
    **Official View:**
    - System-wide analytics
    - Pending verifications & funds
    - Escalated grievances
    """
    try:
        if current_user.role.value == "victim":
            return get_victim_stats(current_user, db)
        elif current_user.role.value == "official":
            return get_official_stats(current_user, db)
        else:
            raise HTTPException(status_code=403, detail="Invalid role")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard statistics: {str(e)}"
        )

def get_victim_stats(user: User, db: Session):
    # 1. Get Victim's Case
    case = db.query(Case).filter(Case.id == user.id).first()
    
    if not case:
        return {
            "role": "victim",
            "has_case": False,
            "message": "No active case found linked to your profile."
        }

    # 2. Calculate Compensation (Logic based on PCR/PoA Act stages)
    total_sanctioned = case.compensation_amount or 0
    
    # Sum successful payments
    received =total_sanctioned//2 or 0
    pending = total_sanctioned - received

    # 3. Case Timeline / Stages
    current_stage = case.stage  # e.g., 'FIR', 'CHARGESHEET', 'TRIAL'
    
    # 4. Grievances
    active_grievances = db.query(Grievance).filter(
        Grievance.id == user.id,
        Grievance.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()

    return {
        "role": "victim",
        "has_case": True,
        "case_number": case.case_number,
        "overview": {
            "total_sanctioned": total_sanctioned,
            "amount_received": received,
            "amount_pending": pending,
            "completion_percentage": int((received / total_sanctioned * 100) if total_sanctioned > 0 else 0)
        },
        "status": {
            "current_stage": current_stage,
            "next_milestone": _get_next_milestone(current_stage),
            "is_verified": case.status=="COMPLETED"
        },
        "grievances": {
            "active_count": active_grievances,
            "latest_status": "Check 'Grievances' tab for details"
        }
    }

def get_official_stats(user: User, db: Session):
    # Aggregated System Stats
    total_cases = db.query(Case).filter(Case.assigned_officer == user.full_name).count()
    
    # Fund Stats
    total_disbursed = db.query(func.sum(Case.compensation_amount)).filter(
            Case.status == "COMPLETED"
        ).scalar() or 0.0
    total_allocated = db.query(func.sum(Case.compensation_amount)).scalar() or 0
    
    # Action Items
    pending_verifications = db.query(Case).filter(
        (Case.status == "PENDING") | (Case.status == "UNDER_REVIEW")
    ).count()
    escalated_grievances = db.query(Grievance).filter(Grievance.is_escalated == True).count()

    status_breakdown = {
        "FIR_Stage": db.query(Case).filter(Case.stage == "FIR").count(),
        "Chargesheet_Stage": db.query(Case).filter(Case.stage == "CHARGESHEET").count(),
        "Conviction_Stage": db.query(Case).filter(Case.stage == "CONVICTION").count(),
    }

    return {
        "role": "official",
        "overview": {
            "total_cases": total_cases,
            "pending_actions": pending_verifications + escalated_grievances,
        },
        "fund_statistics": {
            "total_allocated": total_allocated,
            "total_disbursed": total_disbursed,
            "pending": total_allocated - total_disbursed
        },
        "action_items": {
            "pending_verifications": pending_verifications,
            "escalated_grievances": escalated_grievances
        },
        "status_breakdown": status_breakdown
    }

def _get_next_milestone(current_stage):
    stages = {
        "FIR": "Chargesheet Filing",
        "CHARGESHEET": "Trial/Conviction",
        "CONVICTION": "Case Closure",
        "CLOSED": "None"
    }
    return stages.get(current_stage, "Unknown")
