from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from typing import Optional
from pony.orm import db_session, commit
from datetime import datetime
import logging

from ..database.models import User, Customer, Employee, DeliveryPerson

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/public-auth", tags=["public authentication"])

# Models with input sanitization (but still no security)
class SimpleSignupRequest(BaseModel):
    username: str
    email: str
    password: str  # We'll ignore this
    confirm_password: str  # Added for validation
    user_type: str = "customer"  # customer, employee, or delivery_person
    address: str = "Unknown"
    postalCode: str = "0000AA"
    phone: str = "0000000000"
    gender: str = "Unknown"
    position: str = "None"
    salary: float = 0.0

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

class SimpleLoginRequest(BaseModel):
    username_or_email: str

class SimpleUserResponse(BaseModel):
    id: int
    username: str
    email: str
    user_type: str

# Super simple signup - no validation, no security, just create user
@router.post("/signup", response_model=SimpleUserResponse)
@db_session
def simple_signup(user_data: SimpleSignupRequest):
    """Create user with no validation or security - INSECURE!"""
    try:
        logger.debug(f"Creating user: {user_data.username}")

        # Just create the user - no checks for duplicates or anything
        user = User.create_full_user(
            username=user_data.username,
            email=user_data.email,
            password="password",  # Always use same password
            address=user_data.address,
            postalCode=user_data.postalCode,
            phone=user_data.phone,
            Gender=user_data.gender,
            user_type=user_data.user_type,
            position=user_data.position,
            salary=user_data.salary
        )
        commit()

        return SimpleUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            user_type=user_data.user_type
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )

# Super simple login - no password check, just return user if exists
@router.post("/login", response_model=SimpleUserResponse)
@db_session
def simple_login(credentials: SimpleLoginRequest):
    """Login with no security - just find user by username or email - INSECURE!"""
    try:
        logger.debug(f"Login attempt for: {credentials.username_or_email}")

        # Try username first
        user = User.get(username=credentials.username_or_email)
        if not user:
            # Try email
            user = User.get(email=credentials.username_or_email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Determine user type
        user_type = "customer"
        if isinstance(user, Employee):
            user_type = "employee"
        elif isinstance(user, DeliveryPerson):
            user_type = "delivery_person"

        return SimpleUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            user_type=user_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# Get user by ID - no authentication needed
@router.get("/user/{user_id}", response_model=SimpleUserResponse)
@db_session
def get_user(user_id: int):
    """Get user by ID with no authentication - INSECURE!"""
    try:
        user = User.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_type = "customer"
        if isinstance(user, Employee):
            user_type = "employee"
        elif isinstance(user, DeliveryPerson):
            user_type = "delivery_person"

        return SimpleUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            user_type=user_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

# Get user by username - no authentication needed
@router.get("/user-by-name/{username}", response_model=SimpleUserResponse)
@db_session
def get_user_by_username(username: str):
    """Get user by username with no authentication - INSECURE!"""
    try:
        user = User.get(username=username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_type = "customer"
        if isinstance(user, Employee):
            user_type = "employee"
        elif isinstance(user, DeliveryPerson):
            user_type = "delivery_person"

        return SimpleUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            user_type=user_type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )

# List all users - no authentication needed - EXTREMELY INSECURE!
@router.get("/users", response_model=list[SimpleUserResponse])
@db_session
def list_all_users():
    """List ALL users with no authentication - DANGEROUSLY INSECURE!"""
    try:
        users = User.select()

        user_list = []
        for user in users:
            user_type = "customer"
            if isinstance(user, Employee):
                user_type = "employee"
            elif isinstance(user, DeliveryPerson):
                user_type = "delivery_person"

            user_list.append(SimpleUserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                user_type=user_type
            ))

        return user_list
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )