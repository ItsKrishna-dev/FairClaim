from app.services.file_handler import FileHandler
from app.services.priority_classifier import NLPPriorityClassifier
from .file_handler import FileHandler
def calculate_compensation(act_type: str, stage: str = "FIR") -> float:
    """
    Auto-calculate compensation based on PCR/PoA Act and case stage.
    
    Compensation Matrix (Government Guidelines):
    
    PCR Act 1955:
    - FIR Stage: ₹50,000
    - Chargesheet Stage: ₹1,00,000
    - Conviction Stage: ₹2,00,000
    
    PoA Act 2015:
    - FIR Stage: ₹75,000
    - Chargesheet Stage: ₹1,50,000
    - Conviction Stage: ₹2,50,000
    
    Args:
        act_type: Type of Act ("PCR Act 1955" or "PoA Act 2015")
        stage: Case stage ("FIR", "CHARGESHEET", "CONVICTION")
    
    Returns:
        float: Calculated compensation amount
    """
    
    compensation_matrix = {
        "PCR Act 1955": {
            "FIR": 50000.0,
            "CHARGESHEET": 100000.0,
            "CONVICTION": 200000.0
        },
        "PoA Act 2015": {
            "FIR": 75000.0,
            "CHARGESHEET": 150000.0,
            "CONVICTION": 250000.0
        }
    }
    
    # Default fallback
    default_amount = 50000.0
    
    try:
        return compensation_matrix.get(act_type, {}).get(stage.upper(), default_amount)
    except Exception:
        return default_amount

__all__ = ["FileHandler", "NLPPriorityClassifier","calculate_compensation"]
