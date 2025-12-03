"""
Authentication Routes
Handles user registration, login, and current user retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app import services
from app.models import User

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (victim or official)
    
    **Request Body:**
    - email: Valid email address
    - password: Minimum 6 characters
    - full_name: User's full name
    - role: Either "victim" or "official"
    - phone: Optional phone number with country code
    - aadhaar_number: Optional 12-digit Aadhaar number
    - address: Optional address
    
    **Returns:**
    - Created user object (without password)
    
    **Errors:**
    - 400: Email already registered
    - 422: Validation error
    """
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please use a different email or login."
        )
    
    # Check for duplicate Aadhaar if provided
    if user_data.aadhaar_number:
        existing_aadhaar = db.query(User).filter(
            User.aadhaar_number == user_data.aadhaar_number
        ).first()
        if existing_aadhaar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aadhaar number already registered"
            )
    
    # Create new user
    try:
        new_user = services.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role.value,
            phone=user_data.phone,
            aadhaar_number=user_data.aadhaar_number,
            address=user_data.address
        )
        
        return new_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get JWT access token
    
    **Request Body:**
    - email: User's email address
    - password: User's password
    
    **Returns:**
    - access_token: JWT token for authentication
    - token_type: Always "bearer"
    - user: User information
    
    **Usage:**
    Add token to subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```
    
    **Errors:**
    - 401: Invalid credentials
    - 403: Account inactive
    """
    
    # Authenticate user
    user = services.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Create JWT access token
    access_token = services.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current logged-in user information
    
    **Headers Required:**
    - Authorization: Bearer <access_token>
    
    **Returns:**
    - Current user object
    
    **Errors:**
    - 401: Invalid or expired token
    - 404: User not found
    """
    
    # Extract token from Authorization header
    token = credentials.credentials
    
    # Verify and decode token
    payload = services.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = services.get_user_by_id(db, int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Account may have been deleted."
        )
    
    return user


@router.post("/logout")
def logout():
    """
    Logout user (client-side token removal)
    
    **Note:** 
    JWT tokens are stateless. To logout, the client should:
    1. Remove the token from localStorage/sessionStorage
    2. Clear any cached user data
    
    This endpoint is provided for consistency but doesn't invalidate tokens.
    Tokens expire automatically after the configured time.
    
    **Returns:**
    - Success message
    """
    return {
        "message": "Logout successful. Please remove token from client storage.",
        "action": "Remove token from localStorage/sessionStorage"
    }


# Dependency function for other routes to get current user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency function to get current authenticated user
    
    Use this in other routes that require authentication:
    ```
    @router.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.email}
    ```
    """
    token = credentials.credentials
    payload = services.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = int(payload.get("sub"))
    user = services.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
