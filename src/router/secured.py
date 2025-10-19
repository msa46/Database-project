from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, Union, List
from pony.orm import db_session, select
import jwt
import os
import logging
import traceback

from ..database.models import User, Customer, Employee, DeliveryPerson, Pizza, Order
from ..database.queryManager import QueryManager
from .auth import verify_token, SECRET_KEY, ALGORITHM

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/v1", tags=["secured endpoints"])

# OAuth2PasswordBearer scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Pydantic models for request/response
class SecuredInfoResponse(BaseModel):
    message: str
    user_type: str
    user_id: int
    username: str
    email: str

class PizzaInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    stock: int

class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedPizzaResponse(BaseModel):
    pizzas: List[PizzaInfo]
    pagination: PaginationInfo

class CustomerInfo(BaseModel):
    id: int
    username: str
    email: str

class OrderInfo(BaseModel):
    id: int
    status: str
    created_at: str
    postal_code: str

class CustomerSpecificResponse(SecuredInfoResponse):
    loyalty_points: int
    birthday_order: bool
    available_pizzas: List[PizzaInfo] = []
    pizza_pagination: Optional[PaginationInfo] = None

class EmployeeSpecificResponse(SecuredInfoResponse):
    position: str
    salary: float
    customers: List[CustomerInfo] = []

class DeliveryPersonSpecificResponse(EmployeeSpecificResponse):
    status: str
    orders: List[OrderInfo] = []

# Token-based authentication dependency
async def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user from Authorization header token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        logger.debug(f"Verifying token: {token[:20]}...")
        payload = verify_token(token)
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        logger.debug(f"Token verified for user: {username}, user_id: {user_id}")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"username": username, "user_id": user_id}
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

# Authorization dependencies for different user types
async def get_current_customer(current_user: dict = Depends(get_current_user_from_token)):
    """Ensure current user is a customer"""
    with db_session:
        user = Customer.get(username=current_user["username"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Customer access required."
            )
        return user

async def get_current_employee(current_user: dict = Depends(get_current_user_from_token)):
    """Ensure current user is an employee"""
    with db_session:
        user = Employee.get(username=current_user["username"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Employee access required."
            )
        return user

async def get_current_delivery_person(current_user: dict = Depends(get_current_user_from_token)):
    """Ensure current user is a delivery person"""
    with db_session:
        user = DeliveryPerson.get(username=current_user["username"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Delivery person access required."
            )
        return user

@router.get("/info", response_model=Union[CustomerSpecificResponse, EmployeeSpecificResponse, DeliveryPersonSpecificResponse])
async def get_secured_info(
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get secured information based on user type"""
    try:
        with db_session:
            # Get the user from database
            user = User.get(username=current_user["username"])
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check user type and return appropriate response
            if isinstance(user, Customer):
                return CustomerSpecificResponse(
                    message="Access granted to customer area",
                    user_type="customer",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    loyalty_points=user.loyalty_points,
                    birthday_order=user.birthday_order
                )
            elif isinstance(user, DeliveryPerson):
                return DeliveryPersonSpecificResponse(
                    message="Access granted to delivery person area",
                    user_type="delivery_person",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    status=user.status.value
                )
            elif isinstance(user, Employee):
                return EmployeeSpecificResponse(
                    message="Access granted to employee area",
                    user_type="employee",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unknown user type"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_secured_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve secured information"
        )

@router.get("/dashboard", response_model=Union[CustomerSpecificResponse, EmployeeSpecificResponse, DeliveryPersonSpecificResponse])
async def get_dashboard(
    current_user: dict = Depends(get_current_user_from_token),
    page: int = 1,
    page_size: int = 10
):
    """Get user dashboard based on user type"""
    try:
        logger.debug(f"Getting dashboard for user: {current_user['username']}")
        with db_session:
            # Get the user from database
            # Fix: Use lambda function instead of generator expression for Pony ORM
            user = User.get(username=current_user["username"])
            logger.debug(f"Found user: {user}")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check user type and return appropriate response
            if isinstance(user, Customer):
                # Get paginated pizzas for customers
                try:
                    pizzas_data = QueryManager.get_pizzas_paginated(page=page, page_size=page_size)
                    logger.debug(f"Retrieved pizzas data: {pizzas_data}")
                    
                    # Convert pizzas to PizzaInfo objects
                    pizza_info_list = []
                    for pizza in pizzas_data["pizzas"]:
                        try:
                            logger.debug(f"Processing pizza: {pizza}")
                            pizza_info = PizzaInfo(
                                id=pizza.id,
                                name=pizza.name,
                                description=pizza.description if hasattr(pizza, 'description') else None,
                                stock=pizza.stock
                            )
                            pizza_info_list.append(pizza_info)
                        except Exception as e:
                            logger.error(f"Error processing pizza {pizza}: {str(e)}")
                            raise
                except Exception as e:
                    logger.error(f"Error in pizzas processing: {str(e)}")
                    raise
                
                # Create pagination info
                pagination_info = PaginationInfo(**pizzas_data["pagination"])
                
                return CustomerSpecificResponse(
                    message="Customer dashboard",
                    user_type="customer",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    loyalty_points=user.loyalty_points,
                    birthday_order=user.birthday_order,
                    available_pizzas=pizza_info_list,
                    pizza_pagination=pagination_info
                )
            
            elif isinstance(user, Employee):
                # Get all customers for employees
                customers = Customer.select()[:]
                customer_info_list = [
                    CustomerInfo(
                        id=customer.id,
                        username=customer.username,
                        email=customer.email
                    ) for customer in customers
                ]
                
                return EmployeeSpecificResponse(
                    message="Employee dashboard",
                    user_type="employee",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    customers=customer_info_list
                )
            
            elif isinstance(user, DeliveryPerson):
                # Get orders for delivery person
                orders = QueryManager.get_orders_by_user(user.id)
                order_info_list = [
                    OrderInfo(
                        id=order.id,
                        status=order.status.value,
                        created_at=order.created_at.isoformat() if order.created_at else "",
                        postal_code=order.postalCode
                    ) for order in orders
                ]
                
                return DeliveryPersonSpecificResponse(
                    message="Delivery person dashboard",
                    user_type="delivery_person",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    position=user.position,
                    salary=user.salary,
                    status=user.status.value,
                    orders=order_info_list
                )
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unknown user type"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_dashboard: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard information"
        )

@router.get("/employee-only", response_model=EmployeeSpecificResponse)
async def get_employee_info(
    employee: Employee = Depends(get_current_employee)
):
    """Endpoint accessible only by employees"""
    try:
        return EmployeeSpecificResponse(
            message="Employee-specific information",
            user_type="employee",
            user_id=employee.id,
            username=employee.username,
            email=employee.email,
            position=employee.position,
            salary=employee.salary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_employee_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employee information"
        )

@router.get("/delivery-only", response_model=DeliveryPersonSpecificResponse)
async def get_delivery_person_info(
    delivery_person: DeliveryPerson = Depends(get_current_delivery_person)
):
    """Endpoint accessible only by delivery persons"""
    try:
        return DeliveryPersonSpecificResponse(
            message="Delivery person-specific information",
            user_type="delivery_person",
            user_id=delivery_person.id,
            username=delivery_person.username,
            email=delivery_person.email,
            position=delivery_person.position,
            salary=delivery_person.salary,
            status=delivery_person.status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_delivery_person_info: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve delivery person information"
        )

@router.get("/pizzas", response_model=PaginatedPizzaResponse)
async def get_pizzas_paginated(
    page: int = 1,
    page_size: int = 10,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get pizzas with pagination. Accessible by any authenticated user."""
    try:
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be greater than 0"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Get paginated pizzas
        pizzas_data = QueryManager.get_pizzas_paginated(page=page, page_size=page_size)
        
        # Convert pizzas to PizzaInfo objects
        pizza_info_list = [
            PizzaInfo(
                id=pizza.id,
                name=pizza.name,
                description=pizza.description if hasattr(pizza, 'description') else None,
                stock=pizza.stock
            ) for pizza in pizzas_data["pizzas"]
        ]
        
        # Create pagination info
        pagination_info = PaginationInfo(**pizzas_data["pagination"])
        
        return PaginatedPizzaResponse(
            pizzas=pizza_info_list,
            pagination=pagination_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_pizzas_paginated: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve paginated pizzas"
        )
