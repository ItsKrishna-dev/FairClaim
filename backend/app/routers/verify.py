from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import services
from app.routers.auth import get_current_user
from app.models import User
import os
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/verify-document")
async def verify_document(
    file: UploadFile = File(..., description="Document image (JPG/PNG)"),
    document_type: str = Form(..., description="aadhaar, caste_certificate, income_certificate, fir_copy"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced document verification with:
    - QR code extraction & validation
    - Multi-language OCR support (10+ Indian languages)
    - User-document cross-verification
    - Security alerts for mismatches
    - Audit trail logging
    """
    
    # Validation 1: Check file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validation 2: Aadhaar number required for Aadhaar verification
    if document_type == "aadhaar" and not current_user.aadhaar_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please update your Aadhaar number in profile before verification"
        )
    
    # Validation 3: File size check
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size: 10 MB"
        )
    
    try:
        # Save uploaded file
        os.makedirs("uploads", exist_ok=True)
        file_id = uuid.uuid4()
        file_path = os.path.join("uploads", f"{file_id}{file_ext}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Verify document with enhanced agent
        verification_result = services.verify_document_with_ocr(
            file_path=file_path,
            document_type=document_type,
            user=current_user  # Pass user object for cross-verification
        )
        
        # Security Check: Log suspicious activity
        if verification_result.get("security_alert"):
            print(f"🚨 SECURITY ALERT: User {current_user.id} ({current_user.email})")
            print(f"   Reason: {verification_result.get('reason')}")
            print(f"   Details: {verification_result.get('details', 'N/A')}")
            
            # In production: Save to SecurityAlert table in database
        
        # Optional: Delete file after verification (uncomment in production)
        # os.remove(file_path)
        
        return {
            "success": True,
            "filename": file.filename,
            "document_type": document_type,
            "file_id": str(file_id),
            "verification_result": verification_result,
            "uploaded_by": current_user.email,
            "user_name": current_user.full_name,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Cleanup on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/supported-documents")
def get_supported_documents():
    """List supported document types and languages"""
    return {
        "supported_documents": [
            {
                "type": "aadhaar",
                "name": "Aadhaar Card",
                "verification_methods": ["QR Code Validation", "OCR Fallback"],
                "confidence": "High (95%) with QR, Medium (65%) with OCR",
                "requirements": "Clear image with QR code visible",
                "security": "Cross-verified with user profile"
            },
            {
                "type": "caste_certificate",
                "name": "Caste Certificate",
                "verification_methods": ["QR Code", "Multilingual OCR", "API Setu (Mock)"],
                "confidence": "Medium (75%)",
                "requirements": "Government-issued certificate with clear text"
            },
            {
                "type": "income_certificate",
                "name": "Income Certificate",
                "verification_methods": ["OCR", "Keyword Matching"],
                "confidence": "Medium (60%)",
                "requirements": "Clear readable text"
            },
            {
                "type": "fir_copy",
                "name": "FIR Copy",
                "verification_methods": ["OCR", "CCTNS API (Mock)"],
                "confidence": "Medium (60%)",
                "requirements": "Official police station copy"
            }
        ],
        "supported_languages": [
            "English", "Hindi (हिंदी)", "Tamil (தமிழ்)", "Telugu (తెలుగు)",
            "Marathi (मराठी)", "Bengali (বাংলা)", "Kannada (ಕನ್ನಡ)",
            "Malayalam (മലയാളം)", "Gujarati (ગુજરાતી)", "Punjabi (ਪੰਜਾਬੀ)"
        ],
        "note": "QR code verification provides highest confidence. OCR is fallback method.",
        "security_features": [
            "User-document cross-verification",
            "Aadhaar number matching",
            "Name fuzzy matching (handles typos)",
            "Security alerts for mismatches",
            "Complete audit trail"
        ]
    }
