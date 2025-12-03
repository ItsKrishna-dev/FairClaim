"""
Dashboard Routes
Provides aggregated statistics for admin/official dashboards
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DashboardStats
from app.services import services
from app.routers.auth import get_current_user
from app.models import User

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated dashboard statistics
    
    **Authentication Required:** Yes (Bearer token)
    
    **Returns:**
    - total_cases: Total number of cases in system
    - status_breakdown: Cases grouped by status (FIR, Chargesheet, Conviction)
    - fund_statistics:
        - total_allocated: Total funds allocated across all cases
        - total_disbursed: Total funds disbursed
        - pending: Remaining funds to be disbursed
    - grievances:
        - total: Total grievances
        - pending: Pending grievances
        - in_progress: Grievances being processed
        - resolved: Resolved grievances
        - high_priority: High priority grievances needing attention
    
    **Use Cases:**
    - Official dashboard overview
    - Victim can see their own statistics (filtered by user_id)
    - Generate reports and analytics
    
    **Errors:**
    - 401: Unauthorized (invalid token)
    - 500: Server error fetching statistics
    """
    
    try:
        # Get statistics from service layer
        stats = services.get_dashboard_statistics(db, user_role=current_user.role.value)
        
        # Add current user role to response
        stats["user_role"] = current_user.role.value
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard statistics: {str(e)}"
        )


@router.get("/user-stats")
def get_user_specific_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics specific to current user
    
    **Authentication Required:** Yes (Bearer token)
    
    **Returns:**
    - For victims: Their own cases and grievances
    - For officials: Cases assigned to them
    
    **Errors:**
    - 401: Unauthorized
    """
    
    from app.models import Case, Grievance
    
    try:
        if current_user.role.value == "victim":
            # Victim's own statistics
            my_cases = db.query(Case).filter(Case.user_id == current_user.id).count()
            my_grievances = db.query(Grievance).filter(Grievance.user_id == current_user.id).count()
            
            return {
                "role": "victim",
                "my_cases": my_cases,
                "my_grievances": my_grievances,
                "user_id": current_user.id
            }
        else:
            # Official's statistics (all cases they can manage)
            total_cases = db.query(Case).count()
            pending_grievances = db.query(Grievance).filter(Grievance.status == "PENDING").count()
            
            return {
                "role": "official",
                "manageable_cases": total_cases,
                "pending_grievances": pending_grievances,
                "user_id": current_user.id
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user statistics: {str(e)}"
        )
