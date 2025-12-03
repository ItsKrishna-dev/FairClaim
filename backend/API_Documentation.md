# FairClaim API - Case & Grievance Management

## Base URL
http://localhost:8000/api


## Authentication
Currently: None (Add JWT later when integrating with Developer A's auth module)

---

## 📋 CASE ENDPOINTS

### 1. Create Case
**POST** `/api/cases/`

**Request Body:**


{
"victim_name": "string",
"victim_aadhaar": "string (12 digits)",
"victim_phone": "string (10-15 chars)",
"victim_email": "string (optional)",
"incident_description": "string (min 10 chars)",
"incident_date": "datetime (ISO format)",
"incident_location": "string (min 5 chars)",
"stage": "FIR | CHARGESHEET | CONVICTION",
"compensation_amount": "float (>0)",
"bank_account_number": "string (9-18 digits)",
"ifsc_code": "string (11 chars)"
}



**Response:** Case object with auto-generated `case_number`

---

### 2. List All Cases
**GET** `/api/cases/?page=1&page_size=10&status_filter=PENDING&stage_filter=FIR`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10)
- `status_filter` (optional): PENDING | UNDER_REVIEW | APPROVED | REJECTED | PAYMENT_PROCESSING | COMPLETED
- `stage_filter` (optional): FIR | CHARGESHEET | CONVICTION

**Response:**
{
"cases": [...],
"total": 10,
"page": 1,
"page_size": 10
}

---

### 3. Get Single Case
**GET** `/api/cases/{case_id}`

**Response:** Single case object

---

### 4. Update Case
**PATCH** `/api/cases/{case_id}`

**Request Body:**

{
"status": "APPROVED",
"assigned_officer": "string (optional)",
"remarks": "string (optional)"
}


---

### 5. Upload Documents
**POST** `/api/cases/{case_id}/upload`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `files`: Multiple files (PDF, JPG, PNG, DOC, DOCX)

**Response:** Updated case with file paths in `uploaded_documents`

---

### 6. Delete Case
**DELETE** `/api/cases/{case_id}`

**Response:** 204 No Content

---

## 📢 GRIEVANCE ENDPOINTS

### 1. Create Grievance (with Auto-Priority)
**POST** `/api/grievances/`

**Request Body:**

{
"case_id": "integer",
"title": "string (5-200 chars)",
"description": "string (min 10 chars)",
"category": "string (3-100 chars)",
"contact_name": "string",
"contact_phone": "string",
"contact_email": "string (optional)"
}


**Response:** Grievance object with auto-classified `priority` (CRITICAL | HIGH | MEDIUM | LOW)

**Priority Keywords:**
- **CRITICAL**: death, murder, rape, life-threatening
- **HIGH**: urgent, immediate, threat, violence, medical
- **MEDIUM**: delayed, pending, payment, verification
- **LOW**: default

---

### 2. List Grievances
**GET** `/api/grievances/?page=1&page_size=10&case_id=1&status_filter=OPEN&priority_filter=HIGH`

**Query Parameters:**
- `page`, `page_size`: Pagination
- `case_id`: Filter by specific case
- `status_filter`: OPEN | IN_PROGRESS | RESOLVED | CLOSED | ESCALATED
- `priority_filter`: CRITICAL | HIGH | MEDIUM | LOW

---

### 3. Get Single Grievance
**GET** `/api/grievances/{grievance_id}`

---

### 4. Update Grievance
**PATCH** `/api/grievances/{grievance_id}`

**Request Body:**
{
"status": "RESOLVED",
"resolution_notes": "string (optional)",
"resolved_by": "string (optional)"
}


**Note:** `resolved_at` is auto-set when status becomes RESOLVED/CLOSED

---

### 5. Delete Grievance
**DELETE** `/api/grievances/{grievance_id}`

---

## 🗄️ DATABASE SCHEMA

### Cases Table
- id (Primary Key)
- case_number (Unique)
- victim_name, victim_aadhaar, victim_phone, victim_email
- incident_description, incident_date, incident_location
- stage, status, compensation_amount
- bank_account_number, ifsc_code
- uploaded_documents (JSON)
- created_at, updated_at
- assigned_officer, remarks

### Grievances Table
- id (Primary Key)
- grievance_number (Unique)
- case_id (Foreign Key → Cases)
- title, description, category
- priority (Auto-classified), status
- contact_name, contact_phone, contact_email
- resolution_notes, resolved_at, resolved_by
- created_at, updated_at

---

## 🧪 Testing
- Swagger UI: http://localhost:8000/docs
- Seeded Data: 10 cases + 10 grievances
- Run Tests: `python test_endpoints.py`
