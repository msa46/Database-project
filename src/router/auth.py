from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from typing import Optional
from pony.orm import db_session, select, commit
from datetime import datetime, timedelta, timezone
import jwt
import os
import logging
import traceback

from ..database.models import User, Customer, Employee, DeliveryPerson, DeliveryStatus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserSignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str
    user_type: str = "customer"  # Can be "customer", "employee", or "delivery_person"
    birthdate: Optional[datetime] = None
    address: str
    postalCode: str
    phone: str
    gender: str
    # Employee/Delivery person specific fields
    position: Optional[str] = None
    salary: Optional[float] = None

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        password = info.data.get('password')
        if password and v != password:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('username')
    @classmethod
    def username_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters long')
        return v

    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v: str) -> str:
        valid_types = ['customer', 'employee', 'delivery_person']
        if v not in valid_types:
            raise ValueError(f'Invalid user type. Must be one of: {", ".join(valid_types)}')
        return v

class UserLoginRequest(BaseModel):
    username_or_email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    birthdate: Optional[datetime] = None
    address: Optional[str] = None
    postalCode: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7 * 24 * 60 # 7 days 

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scheme_name="JWT",
    auto_error=True,
    description="JWT token for authentication"
)

# Router
router = APIRouter(prefix="/auth", tags=["authentication"])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/signup", response_model=TokenResponse)
@db_session
def signup(user_data: UserSignupRequest):
    """Register a new user account"""
    try:
        logger.debug(f"Signup attempt for username: {user_data.username}, email: {user_data.email}")
        
        # Check if username already exists using User.get() method
        logger.debug("Checking if username already exists")
        existing_user = User.get(username=user_data.username)
        if existing_user:
            logger.warning(f"Username already registered: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email already exists using User.get() method
        logger.debug("Checking if email already exists")
        existing_email = User.get(email=user_data.email)
        if existing_email:
            logger.warning(f"Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user account using the unified create_full_user method
        logger.debug(f"Creating new {user_data.user_type} account")
        # Convert datetime to date if birthdate is provided
        birthdate = None
        if user_data.birthdate:
            birthdate = user_data.birthdate.date() if isinstance(user_data.birthdate, datetime) else user_data.birthdate
        
        try:
            user = User.create_full_user(
                username=user_data.username,
                email=user_data.email,
                password=user_data.password,
                address=user_data.address,
                postalCode=user_data.postalCode,
                phone=user_data.phone,
                Gender=user_data.gender,
                user_type=user_data.user_type,
                birthdate=birthdate,
                position=user_data.position,
                salary=user_data.salary
            )
            logger.debug(f"{user_data.user_type.capitalize()} created successfully with ID: {user.id}")
            
            # Explicitly commit the transaction to ensure the user ID is populated
            commit()
            logger.debug(f"Transaction committed, user ID: {user.id}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # Create access token for the newly registered user
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expire_time = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=user.id,
            username=user.username,
            email=user.email
        )

    except ValueError as e:
        logger.error(f"Validation error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
@db_session
def login(credentials: UserLoginRequest):
    """Authenticate user and return access token"""
    try:
        # Find user by username or email
        user = select(u for u in User if u.username == credentials.username_or_email or u.email == credentials.username_or_email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not user.check_password(credentials.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, expire_time = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=user.id,
            username=user.username,
            email=user.email
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
@db_session
def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user information"""
    try:
        payload = verify_token(token)
        username: str = payload.get("sub")

        user = select(u for u in User if u.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            birthdate=user.birthdate,
            address=user.address,
            postalCode=user.postalCode,
            phone=user.phone,
            gender=user.Gender
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )

@router.post("/refresh", response_model=TokenResponse)
@db_session
def refresh_token(token: str = Depends(oauth2_scheme)):
    """Refresh access token"""
    try:
        payload = verify_token(token)

        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token, expire_time = create_access_token(
            data={"sub": payload.get("sub"), "user_id": payload.get("user_id")},
            expires_delta=access_token_expires
        )

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=payload.get("user_id"),
            username=payload.get("sub"),
            email=""  # Would need to fetch from DB if needed
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
