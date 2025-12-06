from fastapi import FastAPI , Request , status
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.routers import cases, grievances
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.database import engine, Base, init_db
from app.routers import verify
import time

from app.routers import auth, dashboard
from app.utils.seed_data import seed_users, seed_cases, seed_grievances
from app.models import Case, Grievance

# Create database tables
print("🔄 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully")

# Seed database on startup
print("\n📊 Initializing database with seed data...")
try:
    db = SessionLocal()
    
    # Clean existing Cases and Grievances to prevent duplicates
    print("🧹 Cleaning old Case and Grievance data...")
    db.query(Grievance).delete()
    db.query(Case).delete()
    db.commit()
    
    seed_users(db)
    seeded_cases = seed_cases(db)
    seed_grievances(db, seeded_cases)
    db.close()
    print("✅ Database seeding completed successfully\n")
except Exception as e:
    print(f"⚠️  Database seeding encountered an issue: {e}\n")

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

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# Include routers
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

app.include_router(
    cases.router,
      prefix="/api",
        tags=["Cases"]
        )
app.include_router(
    grievances.router,
      prefix="/api",
        tags=["Grievances"]
        )

@app.get("/")
def root():
    return {
        "message": "FairClaim API - Case & Grievance Management",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "api_docs": "/api"
    }

@app.get("/api")
def api_root():
    """API root endpoint - shows available endpoints"""
    return {
        "message": "FairClaim API v1.0",
        "status": "active",
        "endpoints": {
            "cases": {
                "list": "GET /api/cases/",
                "create": "POST /api/cases/",
                "get": "GET /api/cases/{id}",
                "update": "PATCH /api/cases/{id}",
                "upload": "POST /api/cases/{id}/upload",
                "delete": "DELETE /api/cases/{id}"
            },
            "grievances": {
                "list": "GET /api/grievances/",
                "create": "POST /api/grievances/",
                "get": "GET /api/grievances/{id}",
                "update": "PATCH /api/grievances/{id}",
                "delete": "DELETE /api/grievances/{id}"
            }
        },
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "SQLite (fairclaim.db)",
        "version": "1.0.0"
    }
