from fastapi import APIRouter, HTTPException, status, Depends, Cookie, Response
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

class EmployeeSpecificResponse(SecuredInfoResponse):
    position: str
    salary: float
    customers: List[CustomerInfo] = []

class DeliveryPersonSpecificResponse(EmployeeSpecificResponse):
    status: str
    orders: List[OrderInfo] = []

# Cookie-based authentication dependency
async def get_current_user_from_cookie(access_token: Optional[str] = Cookie(None, alias="access_token")):
    """Get current authenticated user from cookie"""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing access token cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = verify_token(access_token)
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
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
async def get_current_customer(current_user: dict = Depends(get_current_user_from_cookie)):
    """Ensure current user is a customer"""
    with db_session:
        user = Customer.select(u for u in Customer if u.username == current_user["username"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Customer access required."
            )
        return user

async def get_current_employee(current_user: dict = Depends(get_current_user_from_cookie)):
    """Ensure current user is an employee"""
    with db_session:
        user = Employee.select(u for u in Employee if u.username == current_user["username"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Employee access required."
            )
        return user

async def get_current_delivery_person(current_user: dict = Depends(get_current_user_from_cookie)):
    """Ensure current user is a delivery person"""
    with db_session:
        user = DeliveryPerson.select(u for u in DeliveryPerson if u.username == current_user["username"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Delivery person access required."
            )
        return user

@router.get("/info", response_model=Union[CustomerSpecificResponse, EmployeeSpecificResponse, DeliveryPersonSpecificResponse])
async def get_secured_info(
    response: Response,
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """Get secured information based on user type"""
    try:
        with db_session:
            # Get the user from database
            user = User.select(u for u in User if u.username == current_user["username"]).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Set a secure cookie
            response.set_cookie(
                key="secured_access",
                value="granted",
                httponly=True,
                secure=True,  # Set to False for development without HTTPS
                samesite="strict",
                max_age=2 * 24 * 60 * 60  # 2 days
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
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """Get user dashboard based on user type"""
    try:
        with db_session:
            # Get the user from database
            user = User.select(u for u in User if u.username == current_user["username"]).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check user type and return appropriate response
            if isinstance(user, Customer):
                # Get all available pizzas for customers
                pizzas = QueryManager.get_all_pizzas()
                pizza_info_list = [
                    PizzaInfo(
                        id=pizza.id,
                        name=pizza.name,
                        description=pizza.description if hasattr(pizza, 'description') else None
                    ) for pizza in pizzas
                ]
                
                return CustomerSpecificResponse(
                    message="Customer dashboard",
                    user_type="customer",
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    loyalty_points=user.loyalty_points,
                    birthday_order=user.birthday_order,
                    available_pizzas=pizza_info_list
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
