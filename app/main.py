"""
FastAPI Main Application
Entry point for the FairClaim backend API
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.database import engine, Base, init_db
from app.routers import auth, dashboard, verify
import time

# Create database tables
print("🔄 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully")

# Initialize FastAPI application
app = FastAPI(
    title="FairClaim API",
    description="DBT Solution for Justice & Inclusion under PCR/PoA Acts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "FairClaim Team",
        "email": "support@fairclaim.gov.in"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)


# ==================== MIDDLEWARE ====================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
            "body": exc.body
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
            "path": str(request.url)
        }
    )


# ==================== ROUTERS ====================

# Include authentication router
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}
)

# Include dashboard router
app.include_router(
    dashboard.router,
    prefix="/api/dashboard",
    tags=["Dashboard"],
    responses={401: {"description": "Unauthorized"}}
)

# Include document verification router
app.include_router(
    verify.router,
    prefix="/api",
    tags=["Document Verification"],
    responses={401: {"description": "Unauthorized"}}
)

# Placeholder for Dev B routers (uncomment when ready)
# from app.routers import cases, grievances
# app.include_router(cases.router, prefix="/api/cases", tags=["Cases"])
# app.include_router(grievances.router, prefix="/api/grievances", tags=["Grievances"])


# ==================== ROOT ENDPOINTS ====================

@app.get("/", tags=["Root"])
def root():
    """
    API Root Endpoint
    Welcome message and basic API information
    """
    return {
        "message": "Welcome to FairClaim API",
        "status": "running",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "dashboard": "/api/dashboard",
            "verification": "/api/verify-document"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health Check Endpoint
    Used by monitoring tools to verify API is running
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "database": "connected"
    }


@app.get("/api/info", tags=["Info"])
def api_info():
    """
    API Information Endpoint
    Returns API capabilities and features
    """
    return {
        "name": "FairClaim API",
        "description": "Direct Benefit Transfer System for SC/ST Atrocity Victims",
        "features": [
            "User Authentication (JWT)",
            "Case Management",
            "Grievance Tracking",
            "AI Document Verification (OCR)",
            "SMS Notifications (Twilio)",
            "Dashboard Analytics",
            "Real-time Status Tracking"
        ],
        "tech_stack": {
            "framework": "FastAPI",
            "database": "SQLite/PostgreSQL",
            "authentication": "JWT (Bearer Token)",
            "ocr": "Tesseract",
            "sms": "Twilio",
            "orm": "SQLAlchemy"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# ==================== STARTUP/SHUTDOWN EVENTS ====================

@app.on_event("startup")
async def startup_event():
    """
    Runs when application starts
    Good place for initialization tasks
    """
    print("🚀 FairClaim API is starting up...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc Documentation: http://localhost:8000/redoc")
    print("✅ Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when application shuts down
    Good place for cleanup tasks
    """
    print("🛑 FairClaim API is shutting down...")
    print("✅ Shutdown complete")
