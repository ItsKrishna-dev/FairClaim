# FairClaim – Case & Grievance Management

FastAPI + React system for managing PCR/PoA cases, grievances, document verification, and DBT compensation tracking. The backend auto-seeds demo data into SQLite and exposes REST + Swagger; the frontend is a Vite React dashboard with role-aware views.

## Features
- User auth (register/login/JWT) for victims and officials.
- Case lifecycle: create, list/filter, update status/stage, document uploads, delete.
- Grievances with SentenceTransformer-based NLP priority classification and preview.
- Document verification with QR/OCR (multi-language, PDF/image), security alerts, audit trail.
- Dashboards: victim progress/wallet view, official analytics and action items.
- Ready-to-use Swagger (`/docs`), Redoc (`/redoc`), and seeded sample data.

## Project Structure
- `backend/` – FastAPI app, SQLite DB, seeders, services, tests.
- `app/Frontend/` – React (Vite), Tailwind, i18n, protected routes, dashboards.
- `uploads/` – Saved uploads during verification/case attachments (gitignored).

## Prerequisites
- Python 3.11+ (venv recommended)
- Node.js 18+ and npm
- Tesseract OCR installed and on PATH (or set `pytesseract.pytesseract.tesseract_cmd` in `backend/app/services/services.py`)

## Quick Start
### Backend (API)
```bash
cd backend
python -m venv venv && venv/Scripts/activate  # adjust for your shell
pip install -r requirements.txt
python run.py  # starts on http://localhost:8000
```
- Swagger: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- Health: `GET /health`
- DB: SQLite file `fairclaim.db` is created/seeded on startup (cases + grievances).

### Frontend (React)
```bash
cd app/Frontend
npm install
npm run dev  # defaults to http://localhost:5173
```
The frontend calls the API at `http://localhost:8000/api` (see `src/services/api.js`).

## Configuration (.env)
Create `backend/.env` (values have sensible defaults but should be set in production):
```
SECRET_KEY=<strong-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
TWILIO_ACCOUNT_SID=<optional>
TWILIO_AUTH_TOKEN=<optional>
TWILIO_MESSAGING_SERVICE_SID=<optional>
# Tesseract (Windows example)
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Key Endpoints (base `/api`)
- Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- Cases: `POST /cases/victim/register`, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}`, `POST /cases/{id}/upload`, `DELETE /cases/{id}`
- Grievances: `POST /grievances` (auto-priority), `GET /grievances`, `GET /grievances/{id}`, `PATCH /grievances/{id}`, `DELETE /grievances/{id}`, `POST /grievances/classify-preview`
- Verification: `POST /verify-document`, `GET /supported-documents`
- Dashboard: `GET /api/dashboard/stats`
Detailed request/response samples: `backend/API_Documentation.md`.

## Testing
```bash
cd backend
python -m pytest  # or run individual files: python test_nlp_classifier.py
```

## Notes for Development
- Uploads are stored under `backend/uploads/`; clean as needed during development.
- Main app startup (`backend/app/main.py`) seeds demo data each run; remove if you need a clean DB.
- Frontend uses localStorage for JWT; clear it to log out or call `POST /api/auth/logout` helper.

## License
MIT License (see `LICENSE`).

