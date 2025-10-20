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
from ..database.views import MenuView, DietaryFilter
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

# Pydantic models for multiple pizza order
class PizzaQuantity(BaseModel):
    pizza_id: int
    quantity: int

class MultiplePizzaOrderRequest(BaseModel):
    pizza_quantities: List[PizzaQuantity]
    extra_ids: Optional[List[int]] = None
    discount_code: Optional[str] = None
    postal_code: Optional[str] = None

class OrderItemInfo(BaseModel):
    type: str
    name: str
    quantity: int
    unit_price: float
    subtotal: float

class DiscountInfo(BaseModel):
    code: str
    percentage: float
    amount: float

class MultiplePizzaOrderResponse(BaseModel):
    order_id: int
    status: str
    message: str
    total_price: float
    items: List[OrderItemInfo]
    discount: Optional[DiscountInfo] = None
    created_at: str
    postal_code: str

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
                # Get pizzas with prices for customers
                try:
                    all_pizzas = MenuView.get_pizzas_with_prices_and_filters(DietaryFilter.ALL)
                    logger.debug(f"Retrieved {len(all_pizzas)} pizzas with prices")

                    # Apply pagination to the results
                    start_idx = (page - 1) * page_size
                    end_idx = start_idx + page_size
                    paginated_pizzas = all_pizzas[start_idx:end_idx]

                    # Convert pizzas to PizzaInfo objects (now including price)
                    pizza_info_list = []
                    for pizza in paginated_pizzas:
                        try:
                            logger.debug(f"Processing pizza: {pizza['name']}")
                            pizza_info = PizzaInfo(
                                id=pizza['id'],
                                name=pizza['name'],
                                description=pizza.get('description'),
                                stock=pizza['stock']
                            )
                            pizza_info_list.append(pizza_info)
                        except Exception as e:
                            logger.error(f"Error processing pizza {pizza}: {str(e)}")
                            raise

                    # Create pagination info
                    total_count = len(all_pizzas)
                    total_pages = (total_count + page_size - 1) // page_size
                    pagination_info = PaginationInfo(
                        page=page,
                        page_size=page_size,
                        total_count=total_count,
                        total_pages=total_pages,
                        has_next=end_idx < total_count,
                        has_prev=page > 1
                    )

                except Exception as e:
                    logger.error(f"Error in pizzas processing: {str(e)}")
                    raise
                
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

@router.post("/order-multiple-pizzas", response_model=MultiplePizzaOrderResponse, status_code=status.HTTP_201_CREATED)
async def order_multiple_pizzas(
    request: MultiplePizzaOrderRequest,
    customer: Customer = Depends(get_current_customer)
):
    """Create an order with multiple pizzas for authenticated customers."""
    try:
        logger.debug(f"Customer {customer.username} attempting to order multiple pizzas")
        logger.debug(f"Request data: {request}")
        
        # Validate pizza quantities
        if not request.pizza_quantities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one pizza must be ordered"
            )
        
        # Convert PizzaQuantity objects to [pizza_id, quantity] pairs for QueryManager
        pizza_quantities_list = [[pq.pizza_id, pq.quantity] for pq in request.pizza_quantities]
        
        with db_session:
            # Create the order using QueryManager
            order = QueryManager.create_multiple_pizza_order(
                user_id=customer.id,
                pizza_quantities=pizza_quantities_list,
                extra_ids=request.extra_ids,
                discount_code=request.discount_code,
                postal_code=request.postal_code
            )
            
            logger.info(f"Successfully created order {order.id} for customer {customer.username}")
            
            # Get order confirmation details
            order_details = QueryManager.get_order_confirmation(order.id)
            if not order_details:
                # This shouldn't happen if the order was just created
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve order confirmation"
                )
            
            # Create response
            response = MultiplePizzaOrderResponse(
                order_id=order.id,
                status=order.status.value,
                message="Order created successfully",
                total_price=order_details["total_price"],
                items=[
                    OrderItemInfo(
                        type=item["type"],
                        name=item["name"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                        subtotal=item["subtotal"]
                    ) for item in order_details["items"]
                ],
                discount=(
                    DiscountInfo(
                        code=order_details["discount"]["code"],
                        percentage=order_details["discount"]["percentage"],
                        amount=order_details["discount"]["amount"]
                    ) if order_details["discount"] else None
                ),
                created_at=order.created_at.isoformat() if order.created_at else "",
                postal_code=order.postalCode
            )
            
            logger.debug(f"Created response for order {order.id}")
            return response
            
    except ValueError as e:
        # Handle specific validation errors from QueryManager
        error_message = str(e)
        status_code = status.HTTP_400_BAD_REQUEST
        
        # Check for specific error types to return appropriate status codes
        if "not found" in error_message.lower():
            if "pizza" in error_message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "extra" in error_message.lower():
                status_code = status.HTTP_404_NOT_FOUND
            elif "user" in error_message.lower():
                status_code = status.HTTP_401_UNAUTHORIZED
        elif "insufficient stock" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "must be positive" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "postal code" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
            
        logger.error(f"Validation error in order_multiple_pizzas: {error_message}")
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in order_multiple_pizzas: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order due to an internal error"
        )
