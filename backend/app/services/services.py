"""
Business logic and service functions
Enhanced with multi-language document verification agent
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, UserRole, Case, Grievance, GrievanceStatus
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from twilio.rest import Client
import cv2
import numpy as np
try:
    import pyzbar.pyzbar as pyzbar
except ImportError:
    pyzbar = None  # Handle if not installed
import re
from difflib import SequenceMatcher


# Load environment variables
load_dotenv()


# ==================== CONFIGURATION ====================

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

# Tesseract Configuration (Windows users uncomment and set path)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== ENHANCED DOCUMENT VERIFICATION AGENT ====================

class DocumentVerificationAgent:
    """
    Production-ready verification with regional language support
    
    Supported Languages:
    - English
    - Hindi (हिंदी)
    - Tamil (தமிழ்)
    - Telugu (తెలుగు)
    - Marathi (मराठी)
    - Bengali (বাংলা)
    - Kannada (ಕನ್ನಡ)
    - Malayalam (മലയാളം)
    - Gujarati (ગુજરાતી)
    - Punjabi (ਪੰਜਾਬੀ)
    """
    
    # Language codes for Tesseract
    SUPPORTED_LANGUAGES = {
        'english': 'eng',
        'hindi': 'hin',
        'tamil': 'tam',
        'telugu': 'tel',
        'marathi': 'mar',
        'bengali': 'ben',
        'kannada': 'kan',
        'malayalam': 'mal',
        'gujarati': 'guj',
        'punjabi': 'pan'
    }
    
    def __init__(self):
        self.verification_steps = []
    
    def verify_aadhaar_card(
        self,
        file_path: str,
        user_aadhaar: str,
        user_name: str
    ) -> Dict:
        """
        Comprehensive Aadhaar verification with QR priority
        """
        try:
            self.verification_steps = []  # Reset for each verification
            
            image = cv2.imread(file_path)
            if image is None:
                return {
                    "verified": False,
                    "error": "Unable to read image file",
                    "audit_trail": self.verification_steps
                }
            
            # Step 1: Try QR Code Extraction (Most Reliable)
            qr_result = self._extract_and_verify_aadhaar_qr(
                image, user_aadhaar, user_name
            )
            
            if qr_result.get("verified") is not None:
                return qr_result
            
            # Step 2: Fallback to Multi-language OCR
            return self._verify_aadhaar_multilang_ocr(
                file_path, user_aadhaar, user_name
            )
            
        except Exception as e:
            return {
                "verified": False,
                "error": f"Verification failed: {str(e)}",
                "audit_trail": self.verification_steps
            }
    
    def _extract_and_verify_aadhaar_qr(
        self,
        image,
        user_aadhaar: str,
        user_name: str
    ) -> Dict:
        """
        Extract QR code with multiple fallback methods and verify against user profile

        Methods tried in order:
        1. pyzbar on original image
        2. pyzbar on grayscale image
        3. OpenCV QRCodeDetector (4 sub-methods)

        Args:
            image: CV2 image object
            user_aadhaar: Aadhaar number from user profile
            user_name: Full name from user profile

        Returns:
            Verification result dictionary or empty dict to trigger OCR fallback
        """

        self.verification_steps.append({
            "step": "QR_EXTRACTION_ATTEMPT",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        })

        qr_data = None

        # Method 1: pyzbar (if available)
        if pyzbar is not None:
            self.verification_steps.append({
                "step": "TRYING_PYZBAR",
                "status": "started"
            })

            # Try original image
            try:
                decoded = pyzbar.decode(image)
                if decoded:
                    qr_data = self._parse_qr_objects(decoded)
                    if qr_data:
                        self.verification_steps.append({
                            "step": "PYZBAR_SUCCESS",
                            "method": "direct_image"
                        })
            except Exception as e:
                self.verification_steps.append({
                    "step": "PYZBAR_ERROR",
                    "error": str(e)
                })

            # Try grayscale if still no data
            if not qr_data:
                try:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    decoded = pyzbar.decode(gray)
                    if decoded:
                        qr_data = self._parse_qr_objects(decoded)
                        if qr_data:
                            self.verification_steps.append({
                                "step": "PYZBAR_SUCCESS",
                                "method": "grayscale_image"
                            })
                except Exception as e:
                    self.verification_steps.append({
                        "step": "PYZBAR_GRAYSCALE_ERROR",
                        "error": str(e)
                    })
        else:
            self.verification_steps.append({
                "step": "PYZBAR_NOT_AVAILABLE",
                "note": "pyzbar library not installed"
            })

        # Method 2: OpenCV QR Detector (more reliable for Aadhaar cards)
        if not qr_data:
            self.verification_steps.append({
                "step": "TRYING_OPENCV_DETECTOR",
                "status": "started"
            })
            qr_data = self._extract_qr_with_opencv(image)

        # If no QR found after all methods, return empty to trigger OCR fallback
        if not qr_data:
            self.verification_steps.append({
                "step": "QR_EXTRACTION",
                "status": "failed_all_methods",
                "fallback": "OCR",
                "note": "QR code not detected. Falling back to OCR extraction."
            })
            return {}  # Trigger OCR fallback

        # QR Code successfully extracted! Now parse and verify
        self.verification_steps.append({
            "step": "QR_EXTRACTION",
            "status": "success",
            "qr_data_length": len(qr_data)
        })

        # Parse Aadhaar XML from QR
        extracted_data = self._parse_aadhaar_qr(qr_data)

        if not extracted_data.get("aadhaar_number"):
            self.verification_steps.append({
                "step": "QR_PARSING",
                "status": "failed",
                "reason": "Could not extract Aadhaar number from QR data",
                "fallback": "OCR"
            })
            return {}  # Trigger OCR fallback

        self.verification_steps.append({
            "step": "QR_PARSING",
            "status": "success",
            "extracted_aadhaar": extracted_data["aadhaar_number"][-4:] + " (masked)",
            "extracted_name": extracted_data.get("name", "N/A")
        })

        # SECURITY CHECK 1: Verify Aadhaar number match
        if extracted_data["aadhaar_number"] != user_aadhaar:
            self.verification_steps.append({
                "step": "AADHAAR_VERIFICATION",
                "status": "FAILED",
                "reason": "Aadhaar number mismatch",
                "expected_last_4": user_aadhaar[-4:],
                "found_last_4": extracted_data["aadhaar_number"][-4:]
            })

            return {
                "verified": False,
                "reason": "Aadhaar number mismatch",
                "details": f"Document belongs to different person. Expected ending: {user_aadhaar[-4:]}, Found ending: {extracted_data['aadhaar_number'][-4:]}",
                "security_alert": True,
                "extracted_name": extracted_data.get("name", "Unknown"),
                "user_name": user_name,
                "audit_trail": self.verification_steps
            }

        self.verification_steps.append({
            "step": "AADHAAR_VERIFICATION",
            "status": "PASSED",
            "match": "Aadhaar numbers match"
        })

        # SECURITY CHECK 2: Verify name match (fuzzy matching)
        name_score = self._fuzzy_match(
            user_name.lower().strip(),
            extracted_data["name"].lower().strip()
        )

        self.verification_steps.append({
            "step": "NAME_VERIFICATION",
            "status": "checking",
            "user_name": user_name,
            "document_name": extracted_data["name"],
            "similarity_score": round(name_score, 2),
            "threshold": 0.65
        })

        if name_score < 0.65:  # 65% similarity threshold
            self.verification_steps.append({
                "step": "NAME_VERIFICATION",
                "status": "FAILED",
                "reason": "Name similarity too low"
            })

            return {
                "verified": False,
                "reason": "Name mismatch",
                "details": f"Name similarity too low. Expected: {user_name}, Found: {extracted_data['name']}",
                "name_match_score": round(name_score, 2),
                "security_alert": True,
                "audit_trail": self.verification_steps
            }

        self.verification_steps.append({
            "step": "NAME_VERIFICATION",
            "status": "PASSED",
            "similarity_acceptable": True
        })

        # ALL CHECKS PASSED - SUCCESS!
        return {
            "verified": True,
            "confidence": 95.0,
            "extracted_data": {
                "name": extracted_data["name"],
                "aadhaar_last_4": extracted_data["aadhaar_number"][-4:],
                "dob": extracted_data.get("dob", "N/A"),
                "gender": extracted_data.get("gender", "N/A")
            },
            "verification_method": "QR_CODE_VALIDATION",
            "name_match_score": round(name_score, 2),
            "matched_fields": ["aadhaar_number", "name"],
            "audit_trail": self.verification_steps
        }

    def _parse_qr_objects(self, decoded_objects) -> Optional[str]:
        """
        Helper to parse QR objects from pyzbar
        Extracts the QR data string from decoded objects
        """
        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                try:
                    qr_data = obj.data.decode('utf-8', errors='ignore')
                    if len(qr_data) > 50:  # Valid Aadhaar QR should be substantial
                        self.verification_steps.append({
                            "step": "QR_DATA_EXTRACTED",
                            "status": "success",
                            "data_length": len(qr_data)
                        })
                        return qr_data
                except Exception as e:
                    self.verification_steps.append({
                        "step": "QR_DATA_EXTRACTION",
                        "status": "error",
                        "error": str(e)
                    })
                    continue
        return None

    def _extract_qr_with_opencv(self, image) -> Optional[str]:
        """
        Fallback QR detection using OpenCV QRCodeDetector
        More reliable than pyzbar for certain image qualities

        Returns:
            QR data string if found, None otherwise
        """
        try:
            # Initialize OpenCV QR code detector
            qr_detector = cv2.QRCodeDetector()

            # Method 1: Try with original image
            data, bbox, _ = qr_detector.detectAndDecode(image)

            if data and len(data) > 50:
                self.verification_steps.append({
                    "step": "QR_EXTRACTION_OPENCV",
                    "status": "success",
                    "method": "opencv_qr_detector_direct"
                })
                return data

            # Method 2: Try with grayscale conversion
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            data, bbox, _ = qr_detector.detectAndDecode(gray)

            if data and len(data) > 50:
                self.verification_steps.append({
                    "step": "QR_EXTRACTION_OPENCV",
                    "status": "success",
                    "method": "opencv_qr_detector_grayscale"
                })
                return data

            # Method 3: Try with contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            data, bbox, _ = qr_detector.detectAndDecode(enhanced)

            if data and len(data) > 50:
                self.verification_steps.append({
                    "step": "QR_EXTRACTION_OPENCV",
                    "status": "success",
                    "method": "opencv_qr_detector_enhanced"
                })
                return data

            # Method 4: Try with larger image
            height, width = image.shape[:2]
            resized = cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
            data, bbox, _ = qr_detector.detectAndDecode(resized)

            if data and len(data) > 50:
                self.verification_steps.append({
                    "step": "QR_EXTRACTION_OPENCV",
                    "status": "success",
                    "method": "opencv_qr_detector_upscaled"
                })
                return data

            # No QR found with any method
            self.verification_steps.append({
                "step": "QR_EXTRACTION_OPENCV",
                "status": "no_qr_found",
                "methods_tried": 4
            })
            return None

        except Exception as e:
            self.verification_steps.append({
                "step": "QR_EXTRACTION_OPENCV",
                "status": "error",
                "error": str(e)
            })
            return None

    def _parse_aadhaar_qr(self, qr_data: str) -> Dict:
        """
        Parse Aadhaar QR code (XML format)
        
        Format: <?xml version="1.0"?><PrintLetterBarcodeData uid="..." name="..." ...>
        """
        import xml.etree.ElementTree as ET
        
        try:
            # Try XML parsing
            root = ET.fromstring(qr_data)
            
            return {
                "aadhaar_number": root.get('uid', ''),
                "name": root.get('name', ''),
                "dob": root.get('dob', ''),
                "gender": root.get('gender', ''),
                "address": root.get('co', '') + ', ' + root.get('loc', ''),
                "qr_verified": True
            }
        except:
            # Fallback: Regex extraction
            patterns = {
                "aadhaar_number": r'uid="(\d{12})"',
                "name": r'name="([^"]+)"',
                "dob": r'dob="([^"]+)"',
                "gender": r'gender="([^"]+)"'
            }
            
            extracted = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, qr_data, re.IGNORECASE)
                extracted[key] = match.group(1) if match else ""
            
            return extracted
    
    def _verify_aadhaar_multilang_ocr(
        self,
        file_path: str,
        user_aadhaar: str,
        user_name: str
    ) -> Dict:
        """
        Fallback OCR with multi-language support
        Tries multiple languages to extract Aadhaar number
        """
        self.verification_steps.append({
            "step": "MULTILANG_OCR_FALLBACK",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        image = Image.open(file_path)
        
        # Try English + Hindi (most common combination)
        languages_to_try = ['eng+hin', 'eng', 'hin', 'eng+tam', 'eng+tel']
        
        aadhaar_found = None
        name_found = False
        
        for lang in languages_to_try:
            try:
                text = pytesseract.image_to_string(image, lang=lang)
                
                self.verification_steps.append({
                    "step": f"OCR_ATTEMPT_{lang}",
                    "text_length": len(text)
                })
                
                # Extract Aadhaar number (always in digits)
                aadhaar_pattern = r'\b\d{4}\s*\d{4}\s*\d{4}\b'
                found_numbers = re.findall(aadhaar_pattern, text)
                
                if found_numbers:
                    aadhaar_found = found_numbers[0].replace(' ', '')
                    
                    # Check if user name appears in text
                    name_found = user_name.lower() in text.lower()
                    
                    break  # Found Aadhaar, stop trying
                
            except Exception as e:
                self.verification_steps.append({
                    "step": f"OCR_ATTEMPT_{lang}",
                    "status": "error",
                    "error": str(e)
                })
                continue
        
        # Verify extracted data
        if aadhaar_found:
            if aadhaar_found == user_aadhaar:
                return {
                    "verified": True,
                    "confidence": 65.0 if name_found else 50.0,
                    "verification_method": "MULTILANG_OCR",
                    "warning": "QR code not found. Verification based on OCR only. Please re-upload clear image with QR code for higher confidence.",
                    "name_matched": name_found,
                    "languages_tried": languages_to_try,
                    "audit_trail": self.verification_steps
                }
            else:
                return {
                    "verified": False,
                    "reason": "Aadhaar number mismatch",
                    "details": f"Expected: {user_aadhaar[-4:]}, Found: {aadhaar_found[-4:]}",
                    "security_alert": True,
                    "verification_method": "MULTILANG_OCR",
                    "audit_trail": self.verification_steps
                }
        
        return {
            "verified": False,
            "reason": "Unable to extract Aadhaar number from image",
            "suggestion": "Please upload a clear, high-resolution image with visible text and QR code",
            "verification_method": "MULTILANG_OCR",
            "languages_tried": languages_to_try,
            "audit_trail": self.verification_steps
        }
    
    def verify_caste_certificate(
        self,
        file_path: str,
        user_name: str,
        state: Optional[str] = None
    ) -> Dict:
        """
        Verify caste certificate with regional language support
        """
        try:
            self.verification_steps = []
            
            image = cv2.imread(file_path)
            
            # Step 1: Try QR extraction
            qr_data = self._extract_qr_code(image)
            
            if qr_data:
                # Mock API Setu verification
                api_result = self._mock_api_setu_verify(qr_data, "caste_certificate")
                
                if api_result.get("verified"):
                    return {
                        "verified": True,
                        "confidence": 85.0,
                        "verification_method": "QR_VALIDATION",
                        "note": "QR code validated (Mock API Setu for demo)",
                        "audit_trail": self.verification_steps
                    }
            
            # Step 2: Multilingual OCR
            return self._verify_caste_multilang_ocr(file_path, user_name, state)
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "audit_trail": self.verification_steps
            }
    
    def _extract_qr_code(self, image) -> Optional[str]:
        """Extract QR code from image"""
        if pyzbar is None:
            return None
        
        try:
            decoded_objects = pyzbar.decode(image)
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    return obj.data.decode('utf-8', errors='ignore')
        except:
            pass
        
        return None
    
    def _verify_caste_multilang_ocr(
        self,
        file_path: str,
        user_name: str,
        state: Optional[str] = None
    ) -> Dict:
        """Verify caste certificate with multilingual OCR"""
        
        image = Image.open(file_path)
        
        # Determine language based on state (if provided)
        lang_map = {
            'tamil nadu': 'eng+tam',
            'telangana': 'eng+tel',
            'andhra pradesh': 'eng+tel',
            'karnataka': 'eng+kan',
            'kerala': 'eng+mal',
            'maharashtra': 'eng+mar',
            'gujarat': 'eng+guj',
            'punjab': 'eng+pan',
            'west bengal': 'eng+ben'
        }
        
        lang = lang_map.get(state.lower() if state else '', 'eng+hin')
        
        try:
            text = pytesseract.image_to_string(image, lang=lang)
            text_lower = text.lower()
            
            # Keywords in multiple languages
            english_keywords = ['caste', 'certificate', 'scheduled caste', 'scheduled tribe', 'sc', 'st', 'government']
            hindi_keywords = ['जाति', 'प्रमाण', 'अनुसूचित', 'सरकार']
            
            all_keywords = english_keywords + hindi_keywords
            
            matches = sum(1 for kw in all_keywords if kw in text_lower)
            confidence = (matches / len(english_keywords)) * 100
            
            # Check name presence
            name_variations = [
                user_name.lower(),
                user_name.split()[0].lower() if user_name.split() else '',  # First name
                user_name.split()[-1].lower() if user_name.split() else ''  # Last name
            ]
            
            name_found = any(name_var in text_lower for name_var in name_variations if name_var)
            
            if confidence >= 30 and name_found:
                return {
                    "verified": True,
                    "confidence": min(confidence, 75.0),
                    "verification_method": "MULTILANG_OCR_KEYWORD_MATCH",
                    "language_used": lang,
                    "warning": "Medium confidence. Document validated but please upload with QR code for government registry verification.",
                    "name_matched": name_found,
                    "keywords_matched": matches,
                    "audit_trail": self.verification_steps
                }
            
            return {
                "verified": False,
                "reason": "Insufficient evidence" if not name_found else "Document type unclear",
                "confidence": confidence,
                "name_matched": name_found,
                "suggestion": "Ensure document is clear and contains all required elements",
                "language_used": lang,
                "audit_trail": self.verification_steps
            }
            
        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "audit_trail": self.verification_steps
            }
    
    def _mock_api_setu_verify(self, qr_data: str, doc_type: str) -> Dict:
        """
        Mock API Setu verification for demo
        In production: Replace with actual API call
        """
        self.verification_steps.append({
            "step": "MOCK_API_SETU_CALL",
            "doc_type": doc_type,
            "note": "Demo mode - using mock validation"
        })
        
        # Simple validation: QR should have certificate-related keywords
        if len(qr_data) > 50:
            return {
                "verified": True,
                "status": "VALIDATED_MOCK",
                "note": "In production, this will call actual API Setu endpoint"
            }
        
        return {"verified": False}
    
    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """Calculate string similarity (0-1)"""
        return SequenceMatcher(None, str1, str2).ratio()


# Initialize verification agent
_verification_agent = DocumentVerificationAgent()


# ==================== PASSWORD FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT TOKEN FUNCTIONS ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


from jose import JWTError, jwt, ExpiredSignatureError  # Import ExpiredSignatureError explicitly
from app.services.services import SECRET_KEY, ALGORITHM  # Ensure these are imported

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token with detailed error logging"""
    try:
        print(f"🔍 Verifying token...")
        
        # Verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        print(f"✅ Token decoded successfully. Sub: {payload.get('sub')}")
        return payload
        
    except ExpiredSignatureError:
        # ✅ CORRECT: Python-jose uses this specific exception
        print("❌ Token verification failed: Token has expired")
        return None
        
    except JWTError as e:
        # ✅ CORRECT: Catches signature/format errors
        print(f"❌ Token verification failed: {str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__} - {str(e)}")
        return None




# ==================== USER CRUD OPERATIONS ====================

def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: str,
    phone: Optional[str] = None,
    aadhaar_number: Optional[str] = None,
    address: Optional[str] = None
) -> User:
    """Create a new user in the database"""
    hashed_pwd = hash_password(password)
    user_role = UserRole.VICTIM if role.lower() == "victim" else UserRole.OFFICIAL
    
    db_user = User(
        email=email,
        hashed_password=hashed_pwd,
        full_name=full_name,
        role=user_role,
        phone=phone,
        aadhaar_number=aadhaar_number,
        address=address,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    print(f"✅ User created: {email} (ID: {db_user.id})")
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ Authentication failed: User not found - {email}")
        return None
    
    if not user.is_active:
        print(f"❌ Authentication failed: User inactive - {email}")
        return None
    
    if not verify_password(password, user.hashed_password):
        print(f"❌ Authentication failed: Wrong password - {email}")
        return None
    
    print(f"✅ Authentication successful: {email}")
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user information"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


# ==================== ENHANCED DOCUMENT VERIFICATION ====================

def verify_document_with_ocr(
    file_path: str,
    document_type: str,
    user: User
) -> Dict:
    """
    Enhanced multilingual document verification with user cross-check
    
    Args:
        file_path: Path to uploaded document
        document_type: Type of document (aadhaar, caste_certificate, etc.)
        user: Logged-in user object for cross-verification
        
    Returns:
        Verification result with security checks
    """
    try:
        if document_type == "aadhaar":
            if not user.aadhaar_number:
                return {
                    "verified": False,
                    "error": "User Aadhaar number not registered in profile",
                    "suggestion": "Please update your profile with Aadhaar number first"
                }
            
            return _verification_agent.verify_aadhaar_card(
                file_path=file_path,
                user_aadhaar=user.aadhaar_number,
                user_name=user.full_name
            )
        
        elif document_type == "caste_certificate":
            # Extract state from address if available
            state = None
            if user.address:
                # Try to extract state from address (last part usually)
                address_parts = user.address.split(',')
                if address_parts:
                    state = address_parts[-1].strip()
            
            return _verification_agent.verify_caste_certificate(
                file_path=file_path,
                user_name=user.full_name,
                state=state
            )
        
        elif document_type in ["income_certificate", "fir_copy"]:
            # Use old OCR method for these (for now)
            return _verify_document_basic_ocr(file_path, document_type, user.full_name)
        
        else:
            return {
                "verified": False,
                "error": f"Unsupported document type: {document_type}"
            }
            
    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
            "security_alert": True
        }


def _verify_document_basic_ocr(file_path: str, document_type: str, user_name: str) -> Dict:
    """
    Basic OCR verification for income_certificate and fir_copy
    (Fallback method - to be enhanced later)
    """
    try:
        image = Image.open(file_path)
        extracted_text = pytesseract.image_to_string(image)
        text_lower = extracted_text.lower()
        
        # Define keywords for different document types
        keywords_map = {
            "income_certificate": [
                "income", "certificate", "annual income", "government", "revenue",
                "district", "magistrate", "financial year"
            ],
            "fir_copy": [
                "fir", "first information report", "police station", "complaint",
                "case", "section", "ipc", "accused"
            ]
        }
        
        required_keywords = keywords_map.get(document_type, [])
        matches = sum(1 for keyword in required_keywords if keyword in text_lower)
        total_keywords = len(required_keywords)
        
        confidence = (matches / total_keywords) * 100 if total_keywords > 0 else 0
        name_found = user_name.lower() in text_lower
        
        verified = confidence >= 40 and name_found
        
        return {
            "verified": verified,
            "confidence": round(confidence, 2),
            "verification_method": "BASIC_OCR",
            "extracted_text_preview": extracted_text[:200],
            "keywords_matched": matches,
            "total_keywords": total_keywords,
            "name_matched": name_found,
            "note": "Basic verification. Enhanced multi-language support coming soon."
        }
        
    except Exception as e:
        return {
            "verified": False,
            "error": str(e),
            "confidence": 0.0
        }


# ==================== SMS NOTIFICATION SERVICE ====================

def send_sms(to_phone: str, message: str) -> Dict:
    """Send SMS notification via Twilio using Messaging Service"""
    try:
        if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_MESSAGING_SERVICE_SID]):
            print("⚠️  Twilio not configured. SMS simulation mode.")
            return {
                "success": True,
                "message_sid": "SIMULATED_SID_" + str(hash(to_phone))[-6:],
                "status": "simulated",
                "note": "SMS would be sent in production",
                "to": to_phone,
                "message_preview": message[:50] + "..."
            }
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        sms = client.messages.create(
            body=message,
            messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID,
            to=to_phone
        )
        
        print(f"✅ SMS sent to {to_phone}: {message[:50]}...")
        return {
            "success": True,
            "message_sid": sms.sid,
            "status": sms.status,
            "to": to_phone,
            "delivery_status": "queued"
        }
        
    except Exception as e:
        error_msg = f"SMS sending failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "to": to_phone,
            "note": "Check Twilio credentials and phone number format"
        }


def send_case_status_notification(phone: str, case_id: int, new_status: str, user_name: str = "User") -> Dict:
    """Send case status update notification"""
    status_display = new_status.replace("_", " ").title()
    
    message = (
        f"Dear {user_name},\n"
        f"Your FairClaim case #{case_id} status has been updated to: {status_display}.\n"
        f"Visit the portal for details."
    )
    
    return send_sms(phone, message)


def send_grievance_acknowledgment(phone: str, grievance_id: int, case_id: int) -> Dict:
    """Send grievance submission acknowledgment"""
    message = (
        f"Your grievance #{grievance_id} for case #{case_id} has been registered successfully. "
        f"We will respond within 48 hours."
    )
    
    return send_sms(phone, message)


# ==================== DASHBOARD STATISTICS ====================

def get_dashboard_statistics(db: Session, user_role: str = None) -> Dict:
    """Get aggregated statistics for dashboard"""
    try:
        total_cases = db.query(Case).count()
        
        cases_by_status = db.query(
            Case.status,
            func.count(Case.id)
        ).group_by(Case.status).all()
        
        status_breakdown = {status.name: count for status, count in cases_by_status}
        
        total_allocated = db.query(func.sum(Case.fund_amount)).scalar() or 0.0
        total_disbursed = db.query(func.sum(Case.fund_disbursed)).scalar() or 0.0
        
        total_grievances = db.query(Grievance).count()
        pending_grievances = db.query(Grievance).filter(
            Grievance.status == GrievanceStatus.PENDING
        ).count()
        in_progress = db.query(Grievance).filter(
            Grievance.status == GrievanceStatus.IN_PROGRESS
        ).count()
        resolved = db.query(Grievance).filter(
            Grievance.status == GrievanceStatus.RESOLVED
        ).count()
        high_priority = db.query(Grievance).filter(
            Grievance.priority == "HIGH"
        ).count()
        
        return {
            "total_cases": total_cases,
            "status_breakdown": status_breakdown,
            "fund_statistics": {
                "total_allocated": round(total_allocated, 2),
                "total_disbursed": round(total_disbursed, 2),
                "pending": round(total_allocated - total_disbursed, 2)
            },
            "grievances": {
                "total": total_grievances,
                "pending": pending_grievances,
                "in_progress": in_progress,
                "resolved": resolved,
                "high_priority": high_priority
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching dashboard stats: {str(e)}")
        return {
            "total_cases": 0,
            "status_breakdown": {},
            "fund_statistics": {
                "total_allocated": 0.0,
                "total_disbursed": 0.0,
                "pending": 0.0
            },
            "grievances": {
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "resolved": 0,
                "high_priority": 0
            }
        }


# ==================== PLACEHOLDER FOR DEV B SERVICES ====================
# Dev B will add case and grievance service functions here
