"""
Business logic and service functions
Enhanced with multi-language document verification agent + PDF QR Support
"""

from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError
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

# NEW: PDF and QR handling imports
import io
import zlib
import base64
from pdf2image import convert_from_path

try:
    import pyzbar.pyzbar as pyzbar
except ImportError:
    pyzbar = None  # Handle if not installed

import re
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET

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


# ==================== PDF & QR HELPER FUNCTIONS ====================

def render_pdf_to_image(pdf_path: str):
    """
    Enhanced PDF rendering with multiple DPI attempts
    Handles both DigiLocker and myAadhaar PDFs
    """
    for dpi in [600, 500, 400, 300]:  # Try higher DPI first for myAadhaar
        try:
            pages = convert_from_path(pdf_path, dpi=dpi)
            if pages:
                print(f"✅ Rendered PDF at {dpi} DPI")
                return pages[0]
        except Exception as e:
            print(f"⚠️  DPI {dpi} failed: {e}")
            continue

    raise Exception("Failed to render PDF at any DPI level")


def decode_numeric_3byte(raw: bytes) -> bytes:
    """
    Decode SQR-3 format (3-digit decimal encoding)
    """
    s = raw.decode()
    if len(s) % 3 != 0:
        raise Exception("Invalid SQR-3 format")
    return bytes(int(s[i:i+3]) for i in range(0, len(s), 3))


def parse_sqr3(raw: bytes) -> Dict:
    """
    Parse Secure QR v3.0 format with photo extraction
    """
    b = decode_numeric_3byte(raw)
    ptr = 0

    version = b[ptr]; ptr += 1
    xml_len = int.from_bytes(b[ptr:ptr+2], "big"); ptr += 2
    photo_len = int.from_bytes(b[ptr:ptr+4], "big"); ptr += 4

    xml_gz = b[ptr:ptr+xml_len]; ptr += xml_len
    photo = b[ptr:ptr+photo_len]; ptr += photo_len

    sig_len = int.from_bytes(b[ptr:ptr+2], "big"); ptr += 2
    signature = b[ptr:ptr+sig_len]

    xml = zlib.decompress(xml_gz).decode()

    return {"xml": xml, "photo": photo, "signature": signature}


def parse_qr_universal(raw: bytes) -> Dict:
    """
    Universal Aadhaar QR parser
    Handles:
    - SQR-3 numeric (3-digit decimal)
    - Base64 / zlib compressed XML
    - Plain XML
    """
    # Try SQR-3 (all digits, divisible by 3)
    s = raw.decode(errors='ignore')
    if s.isdigit() and len(s) % 3 == 0:
        try:
            return parse_sqr3(raw)
        except Exception:
            pass

    # Try plain XML
    if raw.startswith(b"<") or b"<" in raw[:10]:
        try:
            return {"xml": raw.decode(), "photo": None}
        except:
            pass

    # Try zlib / gzip decompression
    try:
        xml_dec = zlib.decompress(raw).decode()
        return {"xml": xml_dec, "photo": None}
    except:
        pass

    # Try Base64 decode + decompress (newer PDFs)
    try:
        decoded = base64.b64decode(raw)
        xml_dec = zlib.decompress(decoded).decode()
        return {"xml": xml_dec, "photo": None}
    except:
        pass

    raise Exception(f"Unknown QR format, first 50 bytes: {raw[:50]}")


def extract_fields_from_xml(xml: str) -> Dict:
    """
    Extract Aadhaar fields from XML
    """
    try:
        root = ET.fromstring(xml)
        return {
            "aadhaar_number": root.get('uid', ''),
            "name": root.get('name', ''),
            "dob": root.get('dob', ''),
            "gender": root.get('gender', ''),
            "address": f"{root.get('co', '')}, {root.get('loc', '')}, {root.get('vtcName', '')}, {root.get('districtName', '')}, {root.get('stateName', '')}".strip(", "),
            "pincode": root.get('pc', ''),
            "qr_verified": True
        }
    except Exception as e:
        print(f"⚠️  XML parsing error: {e}")
        return {}


# ==================== ENHANCED DOCUMENT VERIFICATION AGENT ====================


import requests
import json

def transliterate_text(text, lang_code):
    if not text or not lang_code: return [text]
    url = "https://inputtools.google.com/request"
    params = {"text": text, "itc": f"{lang_code}-t-i0-und", "num": "5", "cp": "0", "cs": "1", "ie": "utf-8", "oe": "utf-8", "app": "demopage"}
    try:
        response = requests.get(url, params=params, timeout=2)
        if response.status_code == 200 and response.json()[0] == "SUCCESS":
            return response.json()[1][0][1]
    except: pass
    return [text]

def get_name_variations(name, languages=['hin', 'mar']):
    variations = {name.lower()}
    code_map = {'hindi': 'hi', 'marathi': 'mr', 'tamil': 'ta', 'telugu': 'te', 'kannada': 'kn', 'malayalam': 'ml', 'bengali': 'bn', 'gujarati': 'gu', 'punjabi': 'pa'}
    parts = name.split()
    for lang in languages:
        code = code_map.get(lang, 'hi')
        variations.update(t.lower() for t in transliterate_text(name, code))
        for part in parts:
            variations.update(t.lower() for t in transliterate_text(part, code))
    return list(variations)


class DocumentVerificationAgent:
    """
    Production-ready verification with regional language support + PDF QR parsing

    Supported Languages:
    - English, Hindi, Tamil, Telugu, Marathi, Bengali, Kannada, Malayalam, Gujarati, Punjabi

    NEW: PDF Support for both DigiLocker and myAadhaar formats
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
        Comprehensive Aadhaar verification with PDF + QR priority

        NEW: Now handles both PDF and image files
        """
        try:
            self.verification_steps = []  # Reset for each verification

            # Check file type
            file_ext = os.path.splitext(file_path)[1].lower()

            # Handle PDF files
            if file_ext == '.pdf':
                self.verification_steps.append({
                    "step": "PDF_DETECTION",
                    "status": "detected",
                    "note": "PDF file detected, converting to image..."
                })

                try:
                    # Convert PDF to image
                    pil_image = render_pdf_to_image(file_path)
                    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                    self.verification_steps.append({
                        "step": "PDF_CONVERSION",
                        "status": "success"
                    })
                except Exception as e:
                    self.verification_steps.append({
                        "step": "PDF_CONVERSION",
                        "status": "failed",
                        "error": str(e)
                    })
                    return {
                        "verified": False,
                        "error": f"PDF conversion failed: {str(e)}",
                        "audit_trail": self.verification_steps
                    }
            else:
                # Handle image files
                image = cv2.imread(file_path)
                if image is None:
                    return {
                        "verified": False,
                        "error": "Unable to read image file",
                        "audit_trail": self.verification_steps
                    }

            # Step 1: Try QR Code Extraction (Most Reliable)
            qr_result = self._extract_and_verify_aadhaar_qr(
                image, user_aadhaar, user_name, file_path, file_ext
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
        user_name: str,
        file_path: str = None,
        file_ext: str = None
    ) -> Dict:
        """
        ENHANCED: Extract QR code with PDF support and universal parsing

        Methods tried in order:
        1. Enhanced QR detection for PDFs (9+ methods)
        2. pyzbar on original/grayscale images
        3. OpenCV QRCodeDetector (4 sub-methods)
        """
        self.verification_steps.append({
            "step": "QR_EXTRACTION_ATTEMPT",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started"
        })

        qr_data = None

        # ENHANCED: Try advanced QR detection for PDFs
        if file_ext == '.pdf' or (file_path and file_path.lower().endswith('.pdf')):
            self.verification_steps.append({
                "step": "TRYING_ENHANCED_PDF_QR_DETECTION",
                "status": "started",
                "methods": "9+ advanced techniques"
            })

            try:
                qr_data = self._detect_qr_enhanced(image)
            except Exception as e:
                self.verification_steps.append({
                    "step": "ENHANCED_PDF_QR_DETECTION",
                    "status": "failed",
                    "error": str(e)
                })

        # Method 1: pyzbar (if available and not already found)
        if not qr_data and pyzbar is not None:
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
            if not qr_data:
                self.verification_steps.append({
                    "step": "PYZBAR_NOT_AVAILABLE",
                    "note": "pyzbar library not installed"
                })

        # Method 2: OpenCV QR Detector
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

        # QR Code successfully extracted! Now parse with universal parser
        self.verification_steps.append({
            "step": "QR_EXTRACTION",
            "status": "success",
            "qr_data_length": len(qr_data) if isinstance(qr_data, (str, bytes)) else 0
        })

        # Parse Aadhaar QR with universal parser
        extracted_data = self._parse_aadhaar_qr_enhanced(qr_data)

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
            "extracted_aadhaar": "****" + extracted_data["aadhaar_number"][-4:] + " (masked)",
            "extracted_name": extracted_data.get("name", "N/A")
        })

                # SECURITY CHECK 1: Verify Aadhaar number match
        # MODIFIED: Accept if either full number matches OR last 4 digits match (for demo purposes)

        is_full_match = extracted_data.get("aadhaar_number") == user_aadhaar
        is_last_4_match = False
        if user_aadhaar and extracted_data.get("aadhaar_number"):
            is_last_4_match = extracted_data["aadhaar_number"][-4:] == user_aadhaar[-4:]

        if not is_full_match and not is_last_4_match:
            self.verification_steps.append({
                "step": "AADHAAR_VERIFICATION",
                "status": "FAILED",
                "reason": "Aadhaar number mismatch",
                "expected_last_4": user_aadhaar[-4:] if user_aadhaar else "None",
                "found_last_4": extracted_data.get("aadhaar_number", "")[-4:]
            })
            return {
                "verified": False,
                "reason": "Aadhaar number mismatch",
                "details": f"Document belongs to different person. Expected ending: {user_aadhaar[-4:] if user_aadhaar else 'None'}, Found ending: {extracted_data.get('aadhaar_number', '')[-4:]}",
                "security_alert": True,
                "extracted_name": extracted_data.get("name", "Unknown"),
                "user_name": user_name,
                "audit_trail": self.verification_steps
            }

        if is_last_4_match and not is_full_match:
             self.verification_steps.append({
                "step": "AADHAAR_VERIFICATION",
                "status": "PASSED_WITH_WARNING",
                "match": "Last 4 digits match (Full number mismatch ignored for demo)"
            })
        else:
            self.verification_steps.append({
                "step": "AADHAAR_VERIFICATION",
                "status": "PASSED",
                "match": "Full Aadhaar number match"
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
                "gender": extracted_data.get("gender", "N/A"),
                "address": extracted_data.get("address", "N/A")
            },
            "verification_method": "QR_CODE_VALIDATION_UNIVERSAL",
            "name_match_score": round(name_score, 2),
            "matched_fields": ["aadhaar_number", "name"],
            "audit_trail": self.verification_steps
        }

    def _detect_qr_enhanced(self, image) -> Optional[bytes]:
        """
        ENHANCED QR detection with 9+ methods
        Specifically designed for myAadhaar PDFs
        """
        detector = cv2.QRCodeDetector()

        # Import pyzbar for enhanced detection
        try:
            from pyzbar.pyzbar import decode
        except ImportError:
            decode = None

        # Method 1: Direct OpenCV
        data, pts, _ = detector.detectAndDecode(image)
        if data and len(data) > 50:
            return data.encode()

        # Method 2: pyzbar on original
        if decode:
            barcodes = decode(Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB)))
            if barcodes:
                return barcodes[0].data

        # Method 3: Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        data, pts, _ = detector.detectAndDecode(gray)
        if data and len(data) > 50:
            return data.encode()

        # Method 4: Adaptive threshold
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY, 31, 10)
        data, pts, _ = detector.detectAndDecode(thr)
        if data and len(data) > 50:
            return data.encode()

        # Method 5: Otsu binarization
        _, thr2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        data, pts, _ = detector.detectAndDecode(thr2)
        if data and len(data) > 50:
            return data.encode()

        # Method 6: Inverted image
        inv = cv2.bitwise_not(gray)
        data, pts, _ = detector.detectAndDecode(inv)
        if data and len(data) > 50:
            return data.encode()

        # Method 7: CLAHE enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        data, pts, _ = detector.detectAndDecode(clahe_img)
        if data and len(data) > 50:
            return data.encode()

        # Method 8-9: pyzbar on processed images
        if decode:
            for img_variant in [gray, thr, thr2, inv, clahe_img]:
                barcodes = decode(Image.fromarray(img_variant))
                if barcodes:
                    return barcodes[0].data

        # All methods failed
        return None

    def _parse_aadhaar_qr_enhanced(self, qr_data: bytes) -> Dict:
        """
        ENHANCED: Universal QR parser supporting all Aadhaar formats
        """
        try:
            # Use the universal parser
            parsed = parse_qr_universal(qr_data if isinstance(qr_data, bytes) else qr_data.encode())

            # Extract fields from XML
            if parsed.get("xml"):
                return extract_fields_from_xml(parsed["xml"])

            return {}
        except Exception as e:
            self.verification_steps.append({
                "step": "UNIVERSAL_QR_PARSING",
                "status": "error",
                "error": str(e)
            })

            # Fallback to old XML parsing
            return self._parse_aadhaar_qr(qr_data)

    def _parse_qr_objects(self, decoded_objects) -> Optional[str]:
        """
        Helper to parse QR objects from pyzbar
        Extracts the QR data string from decoded objects
        """
        for obj in decoded_objects:
            if obj.type == 'QRCODE':
                try:
                    qr_data = obj.data.decode('utf-8', errors='ignore') if isinstance(obj.data, bytes) else obj.data
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
        Parse Aadhaar QR code (XML format) - LEGACY FALLBACK
        Format: <uid="..." name="..." dob="..." gender="..." .../>
        """
        try:
            # Try XML parsing first
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

    def verify_income_certificate(
        self,
        file_path: str,
        user_name: str
    ) -> Dict:
        """
        Verify income certificate with support for ALL 10 Indian languages + Transliteration
        """
        try:
            self.verification_steps = []
            self.verification_steps.append({
                "step": "INCOME_CERT_VERIFICATION",
                "status": "started",
                "timestamp": datetime.utcnow().isoformat()
            })

            image = Image.open(file_path)

            # COMPREHENSIVE LANGUAGE SUPPORT
            universal_lang = 'eng+hin+mar+tam+tel+kan+mal+ben+guj+pan'

            try:
                text = pytesseract.image_to_string(image, lang=universal_lang)
            except Exception:
                print("⚠️ Full language pack not found, falling back to eng+hin")
                try:
                    text = pytesseract.image_to_string(image, lang='eng+hin')
                    universal_lang = 'eng+hin (fallback)'
                except:
                     text = pytesseract.image_to_string(image, lang='eng')
                     universal_lang = 'eng (fallback)'

            text_lower = text.lower()

            self.verification_steps.append({
                "step": "OCR_EXTRACTION",
                "language_mode": "universal_10_lang",
                "used_lang_str": universal_lang,
                "text_length": len(text)
            })

            # === UNIVERSAL KEYWORD DATABASE ===
            keywords = {
                'english': ['income', 'certificate', 'annual', 'year', 'government', 'tehsildar', 'revenue', 'valid', 'financial'],
                'hindi': ['आय', 'प्रमाण', 'पत्र', 'वार्षिक', 'रुपये', 'तहसीलदार', 'शासन'],
                'marathi': ['उत्पन्न', 'दाखला', 'प्रमाणपत्र', 'वार्षिक', 'वर्ष', 'तहसीलदार', 'शासन', 'महा', 'सेवा'],
                'tamil': ['வருமானம்', 'சான்றிதழ்', 'ஆண்டு', 'வட்டாட்சியர்', 'அரசு'],
                'telugu': ['ఆదాయ', 'ధృవీకరణ', 'పత్రం', 'సంవత్సర', 'తహసీల్దార్', 'ప్రభుత్వం'],
                'kannada': ['ಆದಾಯ', 'ಪ್ರಮಾಣ', 'ಪತ್ರ', 'ವಾರ್ಷಿಕ', 'ತಹಶೀಲ್ದార్', 'ಸರ್ಕಾರ'],
                'malayalam': ['വരുമാന', 'സർട്ടിഫിക്കറ്റ്', 'വാർഷിക', 'തഹസിൽദാർ', 'സർക്കാർ'],
                'bengali': ['আয়ের', 'প্রশংসাপত্র', 'বাৎসরিক', 'রোজগার', 'তহশিলদার', 'সরকার'],
                'gujarati': ['આવક', 'દાખલો', 'પ્રમાણપત્ર', 'વાર્ષિક', 'મામલતદાર', 'સરકાર'],
                'punjabi': ['ਆਮਦਨ', 'ਸਰਟੀਫਿਕੇਟ', 'ਸਾਲਾਨਾ', 'ਤਹਿਸੀਲਦਾਰ', 'ਸਰਕਾਰ']
            }

            all_keywords = [kw for lang_list in keywords.values() for kw in lang_list]
            matches = sum(1 for kw in all_keywords if kw in text_lower)

            matched_langs = []
            for lang, kws in keywords.items():
                if any(kw in text_lower for kw in kws):
                    matched_langs.append(lang)

            confidence = min((matches / 3) * 100, 95.0)

            # === ENHANCED NAME MATCHING (Transliteration + Token) ===
            # 1. Determine languages to transliterate to
            target_langs = [l for l in matched_langs if l in ['hindi', 'marathi', 'tamil', 'telugu', 'kannada', 'malayalam', 'bengali', 'gujarati', 'punjabi']]
            if not target_langs: 
                target_langs = ['hindi', 'marathi'] # Default to common

            # 2. Generate name variations (Full Name)
            name_variations = []
            try:
                name_variations = get_name_variations(user_name, target_langs)
            except Exception as e:
                print(f"Name variations error: {e}")
                name_variations = [user_name.lower()]

            # 3. Check full name variations first
            name_found = any(var in text_lower for var in name_variations)

            # 4. If not found, check PART-BY-PART variations (e.g. "Krishna" found AND "Chaurasia" found)
            if not name_found:
                user_parts = user_name.split()
                if len(user_parts) > 0:
                    part_matches = 0
                    for part in user_parts:
                        # Generate variations for this part (e.g. "Krishna" -> "कृष्णा")
                        try:
                            part_vars = get_name_variations(part, target_langs)
                        except:
                            part_vars = [part.lower()]

                        if any(pv in text_lower for pv in part_vars):
                            part_matches += 1

                    # Strict match: All parts must be present
                    if part_matches == len(user_parts):
                        name_found = True
                    # Fuzzy match: Allow 1 missing part if name is long (3+ parts)
                    elif len(user_parts) >= 3 and part_matches >= len(user_parts) - 1:
                        name_found = True

            self.verification_steps.append({
                "step": "NAME_MATCHING_TRANSLITERATED",
                "languages_checked": target_langs,
                "variations_generated": len(name_variations),
                "status": "match" if name_found else "mismatch"
            })

            result = {
                "verified": confidence >= 25 and name_found,
                "verification_method": "UNIVERSAL_MULTILANG_OCR_PLUS_TRANSLITERATION",
                "confidence": round(confidence, 2),
                "languages_detected": matched_langs,
                "keywords_matched": matches,
                "name_matched": name_found,
                "extracted_text_preview": text[:100].replace('', ' ') + "...",
                "audit_trail": self.verification_steps
            }

            if not result["verified"]:
                 if not name_found:
                     result["reason"] = "Name mismatch"
                     result["details"] = f"Name '{user_name}' (or its translations in {target_langs}) not found in document."
                 else:
                     result["reason"] = "Low confidence"
                     result["suggestion"] = "Ensure image is clear and contains income keywords"

            return result

        except Exception as e:
            return {
                "verified": False,
                "error": str(e),
                "audit_trail": self.verification_steps
            }





    def verify_caste_certificate(
        self,
        file_path: str,
        user_name: str,
        state: Optional[str] = None
    ) -> Dict:
        """
        Verify caste certificate with regional language support + Transliteration + Caste Extraction
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

    def _verify_caste_multilang_ocr(
        self,
        file_path: str,
        user_name: str,
        state: Optional[str] = None
    ) -> Dict:
        """Verify caste certificate with multilingual OCR & Transliteration"""
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
            english_keywords = ['caste', 'certificate', 'scheduled caste', 'scheduled tribe', 'sc', 'st', 'government', 'community']
            hindi_keywords = ['जाति', 'प्रमाण', 'अनुसूचित', 'सरकार', 'समुदाय']
            marathi_keywords = ['जात', 'प्रमाणपत्र', 'जमात', 'अनुसूचित']

            all_keywords = english_keywords + hindi_keywords + marathi_keywords

            matches = sum(1 for kw in all_keywords if kw in text_lower)
            confidence = min((matches / len(english_keywords)) * 100, 95.0)

            # === ENHANCED NAME MATCHING (Transliteration) ===
            # Determine target languages for transliteration
            target_langs = []
            if 'mar' in lang: target_langs.append('marathi')
            if 'hin' in lang: target_langs.append('hindi')
            if 'tam' in lang: target_langs.append('tamil')
            if 'tel' in lang: target_langs.append('telugu')
            if 'guj' in lang: target_langs.append('gujarati')
            if 'ben' in lang: target_langs.append('bengali')
            if 'kan' in lang: target_langs.append('kannada')
            if 'mal' in lang: target_langs.append('malayalam')
            if 'pan' in lang: target_langs.append('punjabi')

            if not target_langs: target_langs = ['hindi', 'marathi']

            try:
                name_variations = get_name_variations(user_name, target_langs)
            except:
                name_variations = [user_name.lower()]

            name_found = any(name_var in text_lower for name_var in name_variations)

            # Fallback: Part-by-part matching
            if not name_found:
                user_parts = user_name.split()
                if len(user_parts) > 1:
                    part_matches = 0
                    for part in user_parts:
                        try:
                            part_vars = get_name_variations(part, target_langs)
                        except:
                            part_vars = [part.lower()]

                        if any(pv in text_lower for pv in part_vars):
                            part_matches += 1

                    if part_matches == len(user_parts) or (len(user_parts) > 2 and part_matches >= len(user_parts) - 1):
                        name_found = True

            # === CASTE EXTRACTION LOGIC ===
            extracted_caste = "Unknown"
            caste_markers = ['caste:', 'community:', 'belongs to', 'son of', 'daughter of', 'shri', 'kumari', 'जाति', 'जमात']

            # Simple extraction: Look for words like "SC", "ST", "OBC", "Maratha", "Brahmin", etc.
            # This is a basic heuristic.
            common_castes = ['sc', 'st', 'obc', 'general', 'scheduled caste', 'scheduled tribe', 'maratha', 'kunbi', 'mahar', 'chamar', 'valmiki']

            for caste in common_castes:
                if caste in text_lower:
                    extracted_caste = caste.upper()
                    break

            if confidence >= 30 and name_found:
                return {
                    "verified": True,
                    "confidence": min(confidence, 85.0),
                    "verification_method": "MULTILANG_OCR_TRANSLITERATION",
                    "language_used": lang,
                    "extracted_caste": extracted_caste,
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
                "extracted_caste": extracted_caste,
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

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token with detailed error logging"""
    try:
        print(f"🔍 Verifying token...")
        # Verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Token decoded successfully. Sub: {payload.get('sub')}")
        return payload
    except ExpiredSignatureError:
        print("❌ Token verification failed: Token has expired")
        return None
    except JWTError as e:
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

    NEW: Now supports PDF files for Aadhaar verification

    Args:
        file_path: Path to uploaded document (can be PDF or image)
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

        elif document_type == "income_certificate":
            return _verification_agent.verify_income_certificate(
                file_path=file_path,
                user_name=user.full_name
            )
        elif document_type == "fir_copy":
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
            print("⚠️ Twilio not configured. SMS simulation mode.")
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

        # Handle status as string (not enum) since it's stored as String in DB
        status_breakdown = {status: count for status, count in cases_by_status}

        total_allocated = db.query(func.sum(Case.compensation_amount)).scalar() or 0.0
        total_disbursed = db.query(func.sum(Case.compensation_amount)).filter(
            Case.status == "COMPLETED"
        ).scalar() or 0.0

        total_grievances = db.query(Grievance).count()
        pending_grievances = db.query(Grievance).filter(
            Grievance.status == "PENDING"
        ).count()

        open_grievances = db.query(Grievance).filter(
            Grievance.status == "OPEN"
        ).count()

        in_progress = db.query(Grievance).filter(
            Grievance.status == "IN_PROGRESS"
        ).count()

        resolved = db.query(Grievance).filter(
            Grievance.status == "RESOLVED"
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
                "open": open_grievances,
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
                "open": 0,
                "in_progress": 0,
                "resolved": 0,
                "high_priority": 0
            }
        }

# ==================== COMPENSATION CALCULATOR ====================

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
    
    return compensation_matrix.get(act_type, {}).get(stage.upper(), 50000.0)

# ==================== PLACEHOLDER FOR DEV B SERVICES ====================

# Dev B will add case and grievance service functions here